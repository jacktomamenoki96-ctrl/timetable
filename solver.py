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
                                # キーをオブジェクトではなくID（文字列やタプル）に変更してハッシュ化エラーを回避
                                self.variables[(lesson.id, unit_index, timeslot, room.id, teacher_id)] = var
    
    def add_hard_constraints(self):
        """全てのハード制約をモデルに追加"""
        
        # 制約1: 各Lessonの各unitは必ず1つのtimeslot/room/teacherに配置される
        for lesson in self.lessons.values():
            for unit_index in range(lesson.units):
                # このunitに関する全ての変数
                unit_vars = [
                    var for (lid, uid, ts, room_id, tid), var in self.variables.items()
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
                                var for (lid, uid, ts, room_id, tid), var in self.variables.items()
                                if lid == lesson.id and uid == unit1 and ts == timeslot
                            ]
                            vars_unit2 = [
                                var for (lid, uid, ts, room_id, tid), var in self.variables.items()
                                if lid == lesson.id and uid == unit2 and ts == timeslot
                            ]
                            # 両方が選択されることはない（最大1つ）
                            if vars_unit1 and vars_unit2:
                                self.model.Add(sum(vars_unit1) + sum(vars_unit2) <= 1)
        
        # 制約3: 教員競合 - 同一教員は同じtimeslotに1つの授業のみ
        for teacher_id in self.teachers.keys():
            for timeslot in self.timeslots:
                teacher_vars = [
                    var for (lid, uid, ts, room_id, tid), var in self.variables.items()
                    if tid == teacher_id and ts == timeslot
                ]
                if teacher_vars:
                    self.model.Add(sum(teacher_vars) <= 1)
        
        # 制約4: 教室競合 - 同一教室は同じtimeslotに1つの授業のみ
        for room_id in self.rooms.keys():
            for timeslot in self.timeslots:
                room_vars = [
                    var for (lid, uid, ts, r_id, tid), var in self.variables.items()
                    if r_id == room_id and ts == timeslot
                ]
                if room_vars:
                    self.model.Add(sum(room_vars) <= 1)
        
        # 制約5: クラス競合 - 同一クラスは同じtimeslotに1つの授業のみ
        for class_id in self.classes.keys():
            for timeslot in self.timeslots:
                class_vars = [
                    var for (lid, uid, ts, room_id, tid), var in self.variables.items()
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
                            var for (lid, uid, ts, room_id, tid), var in self.variables.items()
                            if lid == base_lesson.id and uid == unit_index and ts == timeslot
                        ]
                        
                        if not base_vars:
                            continue
                        
                        # 他の同期Lessonも同じtimeslotに配置されるようにする
                        for other_lesson in sync_lessons[1:]:
                            if unit_index < other_lesson.units:
                                other_vars = [
                                    var for (lid, uid, ts, room_id, tid), var in self.variables.items()
                                    if lid == other_lesson.id and uid == unit_index and ts == timeslot
                                ]
                                
                                if other_vars:
                                    # base_varsが選択されている ⇔ other_varsが選択されている
                                    # sum(base_vars) == sum(other_vars)
                                    self.model.Add(sum(base_vars) == sum(other_vars))

        # --- 追加制約: 品質の向上 ---
        
        # 制約7: 同じクラスで同じ科目は1日1回まで（単位数が多い場合は許容）
        # (例: 週4コマなら1日1回。週6コマならどこかで1日2回必要)
        import math
        
        # クラスごとの科目単位数を集計
        class_subject_units: Dict[str, Dict[str, int]] = {}
        for lesson in self.lessons.values():
            for class_id in lesson.class_ids:
                if class_id not in class_subject_units:
                    class_subject_units[class_id] = {}
                if lesson.subject not in class_subject_units[class_id]:
                    class_subject_units[class_id][lesson.subject] = 0
                class_subject_units[class_id][lesson.subject] += lesson.units
        
        # 制約適用
        for class_id in self.classes.keys():
            if class_id not in class_subject_units:
                continue
                
            for subject, total_units in class_subject_units[class_id].items():
                # 1日あたりの最大回数 (基本1回、5コマ超えるなら2回...)
                # 週5日制を前提
                daily_limit = math.ceil(total_units / 5.0)
                
                # 対象となるLessonIDのリスト（このクラス・科目のもの）
                target_lesson_ids = [
                    l.id for l in self.lessons.values() 
                    if class_id in l.class_ids and l.subject == subject
                ]
                
                for weekday in Weekday.all():
                    # その曜日の該当科目の変数を収集
                    subject_vars_on_day = []
                    for period in range(1, 7):
                        ts = TimeSlot(weekday, period)
                        # このtimeslotにある対象Lessonの変数
                        vars_in_slot = [
                            var for (lid, uid, t, r_id, tid), var in self.variables.items()
                            if lid in target_lesson_ids and t == ts
                        ]
                        subject_vars_on_day.extend(vars_in_slot)
                    
                    if subject_vars_on_day:
                        self.model.Add(sum(subject_vars_on_day) <= daily_limit)

        # 制約8: クラスの時間割に空きコマ（中抜け）を作らない
        # 朝から詰める、または連続させる
        for class_id in self.classes.keys():
            for weekday in Weekday.all():
                # 各時限(1-6)が「埋まっているか」を表すブール変数を作成
                is_active = []
                for period in range(1, 7):
                    ts = TimeSlot(weekday, period)
                    
                    # このクラスのこの時間の授業変数すべて
                    vars_in_slot = [
                        var for (lid, uid, t, r_id, tid), var in self.variables.items()
                        if t == ts and class_id in self.lessons[lid].class_ids
                    ]
                    
                    slot_active_var = self.model.NewBoolVar(f"Active_{class_id}_{weekday}_{period}")
                    if vars_in_slot:
                        # 授業が1つでもあれば Active=1
                        self.model.AddMaxEquality(slot_active_var, vars_in_slot)
                    else:
                        # 授業の候補すらなければ Active=0
                        self.model.Add(slot_active_var == 0)
                    
                    is_active.append(slot_active_var)
                
                # 連続性を保証するためのロジック:
                # 0 -> 1 と 1 -> 0 の変化（トランジション）の回数が合計2回以内であれば、
                # 1の塊は1つだけ（または0個）になる。
                # 例: 0 0 1 1 1 0 (OK: 変化2回)
                # 例: 0 1 0 1 0 0 (NG: 変化4回 -> 中抜けあり)
                
                # パディング（前後は0）
                padded_active = [0] + is_active + [0]
                
                transitions = []
                for i in range(len(padded_active) - 1):
                    # i と i+1 が違うなら 1
                    trans_var = self.model.NewBoolVar(f"Trans_{class_id}_{weekday}_{i}")
                    # XORではなく不等価性で実装
                    # (padded_active[i] != padded_active[i+1])
                    
                    # NOTE: padded_activeの要素は IntVar(0/1) または int(0)
                    # 整数0は cp_model では直接扱えない場合があるため、これらを統一的に扱う
                    
                    left = padded_active[i]
                    right = padded_active[i+1]
                    
                    # left != right を表現
                    # trans_var == 1 <-> left + right == 1 (どちらか片方だけ1)
                    # trans_var == 0 <-> left + right != 1 (0+0=0, 1+1=2)
                    
                    # 式: trans_var == (left + right == 1)
                    # これは線形制約ではない論理式なので AddBoolXor などを使うべきだが、
                    # left/rightが定数0の場合があるので注意して構築
                    
                    if isinstance(left, int) and isinstance(right, int):
                        # 両方定数（ありえないが念のため）
                        val = 1 if left != right else 0
                        self.model.Add(trans_var == val)
                    elif isinstance(left, int):
                        # left=0
                        self.model.Add(trans_var == right)
                    elif isinstance(right, int):
                        # right=0
                        self.model.Add(trans_var == left)
                    else:
                        # 両方変数
                        self.model.AddBoolXor([left, right, trans_var])
                    
                    transitions.append(trans_var)
                
                # トランジション回数 <= 2 に制約することで中抜けを禁止
                self.model.Add(sum(transitions) <= 2)
    
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
            
            for (lesson_id, unit_index, timeslot, room_id, teacher_id), var in self.variables.items():
                if solver.Value(var) == 1:
                    lesson = self.lessons[lesson_id]
                    room = self.rooms[room_id]
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
