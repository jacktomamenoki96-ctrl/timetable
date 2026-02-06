"""
時間割自動生成エンジン - OR-Tools CSPソルバー

Google OR-Toolsの制約プログラミングソルバーを使用した時間割生成
"""
from typing import List, Dict, Optional, Tuple
from ortools.sat.python import cp_model
from models import (
    Teacher, Room, Class, Lesson, TimeSlot, Assignment, Timetable,
    Weekday, RoomType
)
from constraints import is_valid_assignment


class TimetableSolver:
    """OR-Tools CP-SATソルバーを使用した時間割生成"""
    
    def __init__(
        self,
        teachers: List[Teacher],
        rooms: List[Room],
        classes: List[Class],
        lessons: List[Lesson]
    ):
        self.teachers = {t.id: t for t in teachers}
        self.rooms = {r.id: r for r in rooms}
        self.classes = {c.id: c for c in classes}
        self.lessons = {l.id: l for l in lessons}
        
        self.timeslots = TimeSlot.all_slots()
        
        self.model = cp_model.CpModel()
        self.variables: Dict = {}
        
    def setup_variables(self):
        """
        決定変数を定義
        
        各Lessonの各配置（units分）に対して:
        - assignment[(lesson_id, unit_index, timeslot, room_id, teacher_id)] = BoolVar
        
        True = その配置が選択される
        """
        for lesson in self.lessons.values():
            # 各Lessonはunits回配置される必要がある
            for unit_index in range(lesson.units):
                # 各TimeSlotについて
                for timeslot in self.timeslots:
                    # 適切な教室タイプの教室について
                    eligible_rooms = [
                        room for room in self.rooms.values()
                        if room.room_type == lesson.room_type_required
                    ]
                    
                    for room in eligible_rooms:
                        # 担当可能な教員について
                        for teacher_id in lesson.teacher_ids:
                            teacher = self.teachers[teacher_id]
                            
                            # 教員が担当可能な時間のみ変数を作成
                            if teacher.is_available(timeslot):
                                var_name = f"L{lesson.id}_U{unit_index}_T{timeslot}_R{room.id}_Teach{teacher_id}"
                                var = self.model.NewBoolVar(var_name)
                                self.variables[(lesson.id, unit_index, timeslot, room, teacher_id)] = var
    
    def add_hard_constraints(self):
        """全てのハード制約をモデルに追加"""
        
        # 制約1: 各Lessonの各unitは必ず1つのtimeslot/room/teacherに配置される
        for lesson in self.lessons.values():
            for unit_index in range(lesson.units):
                # このunitに関する全ての変数
                unit_vars = [
                    var for (lid, uid, ts, room, tid), var in self.variables.items()
                    if lid == lesson.id and uid == unit_index
                ]
                # 必ず1つが選択される
                if unit_vars:
                    self.model.Add(sum(unit_vars) == 1)
        
        # 制約2: 同一Lessonの異なるunitは異なるtimeslotに配置
        for lesson in self.lessons.values():
            if lesson.units > 1:
                for unit1 in range(lesson.units):
                    for unit2 in range(unit1 + 1, lesson.units):
                        # unit1とunit2が同じtimeslotに配置されることを禁止
                        for timeslot in self.timeslots:
                            vars_unit1 = [
                                var for (lid, uid, ts, room, tid), var in self.variables.items()
                                if lid == lesson.id and uid == unit1 and ts == timeslot
                            ]
                            vars_unit2 = [
                                var for (lid, uid, ts, room, tid), var in self.variables.items()
                                if lid == lesson.id and uid == unit2 and ts == timeslot
                            ]
                            # 両方が選択されることはない（最大1つ）
                            if vars_unit1 and vars_unit2:
                                self.model.Add(sum(vars_unit1) + sum(vars_unit2) <= 1)
        
        # 制約3: 教員競合 - 同一教員は同じtimeslotに1つの授業のみ
        for teacher_id in self.teachers.keys():
            for timeslot in self.timeslots:
                teacher_vars = [
                    var for (lid, uid, ts, room, tid), var in self.variables.items()
                    if tid == teacher_id and ts == timeslot
                ]
                if teacher_vars:
                    self.model.Add(sum(teacher_vars) <= 1)
        
        # 制約4: 教室競合 - 同一教室は同じtimeslotに1つの授業のみ
        for room_id in self.rooms.keys():
            for timeslot in self.timeslots:
                room_vars = [
                    var for (lid, uid, ts, r, tid), var in self.variables.items()
                    if r.id == room_id and ts == timeslot
                ]
                if room_vars:
                    self.model.Add(sum(room_vars) <= 1)
        
        # 制約5: クラス競合 - 同一クラスは同じtimeslotに1つの授業のみ
        for class_id in self.classes.keys():
            for timeslot in self.timeslots:
                class_vars = [
                    var for (lid, uid, ts, room, tid), var in self.variables.items()
                    if class_id in self.lessons[lid].class_ids and ts == timeslot
                ]
                if class_vars:
                    self.model.Add(sum(class_vars) <= 1)
        
        # 制約6: 同期制約 - 同じsynchronization_idを持つLessonは同じtimeslotに配置
        sync_groups: Dict[str, List[Lesson]] = {}
        for lesson in self.lessons.values():
            if lesson.synchronization_id:
                if lesson.synchronization_id not in sync_groups:
                    sync_groups[lesson.synchronization_id] = []
                sync_groups[lesson.synchronization_id].append(lesson)
        
        for sync_id, sync_lessons in sync_groups.items():
            # 同期グループ内の全Lessonが同じtimeslotに配置されるようにする
            if len(sync_lessons) > 1:
                # 基準となる最初のLesson
                base_lesson = sync_lessons[0]
                
                for unit_index in range(base_lesson.units):
                    # 基準Lessonの各unitについて
                    for timeslot in self.timeslots:
                        # 基準Lessonがこのtimeslotに配置される変数
                        base_vars = [
                            var for (lid, uid, ts, room, tid), var in self.variables.items()
                            if lid == base_lesson.id and uid == unit_index and ts == timeslot
                        ]
                        
                        if not base_vars:
                            continue
                        
                        # 他の同期Lessonも同じtimeslotに配置されるようにする
                        for other_lesson in sync_lessons[1:]:
                            if unit_index < other_lesson.units:
                                other_vars = [
                                    var for (lid, uid, ts, room, tid), var in self.variables.items()
                                    if lid == other_lesson.id and uid == unit_index and ts == timeslot
                                ]
                                
                                if other_vars:
                                    # base_varsが選択されている ⇔ other_varsが選択されている
                                    # sum(base_vars) == sum(other_vars)
                                    self.model.Add(sum(base_vars) == sum(other_vars))
    
    def solve(self, timeout_seconds: int = 60) -> Optional[Timetable]:
        """
        時間割を生成
        
        Args:
            timeout_seconds: タイムアウト時間（秒）
        
        Returns:
            生成された時間割（解が見つからない場合はNone）
        """
        # 変数と制約のセットアップ
        self.setup_variables()
        self.add_hard_constraints()
        
        # ソルバーの実行
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout_seconds
        solver.parameters.num_search_workers = 16  # 並列処理
        solver.parameters.log_search_progress = True
        
        status = solver.Solve(self.model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # 解から時間割を構築
            timetable = Timetable()
            
            for (lesson_id, unit_index, timeslot, room, teacher_id), var in self.variables.items():
                if solver.Value(var) == 1:
                    lesson = self.lessons[lesson_id]
                    assignment = Assignment(
                        lesson=lesson,
                        timeslot=timeslot,
                        room=room,
                        teacher_id=teacher_id
                    )
                    timetable.add_assignment(assignment)
            
            # 念のため制約チェック
            is_valid, errors = is_valid_assignment(
                timetable,
                self.teachers,
                list(self.lessons.values())
            )
            
            if not is_valid:
                print("警告: 生成された時間割に制約違反があります:")
                for error in errors:
                    print(f"  - {error}")
            
            return timetable
        
        elif status == cp_model.INFEASIBLE:
            print("解が見つかりませんでした（制約が厳しすぎる可能性があります）")
            return None
        
        else:
            print(f"ソルバーのステータス: {status}")
            return None
    
    def get_solver_info(self, solver: cp_model.CpSolver) -> str:
        """ソルバーの実行情報を取得"""
        return f"""
ソルバー情報:
  - 決定変数数: {len(self.variables)}
  - 実行時間: {solver.WallTime():.2f}秒
  - 分岐数: {solver.NumBranches()}
  - 競合数: {solver.NumConflicts()}
"""
