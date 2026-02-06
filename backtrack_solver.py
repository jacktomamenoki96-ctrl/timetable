"""
時間割自動生成エンジン - バックトラックソルバー

純粋Pythonでのバックトラック実装（OR-Toolsの代替/比較用）
"""
from typing import List, Dict, Optional, Set, Tuple
from models import (
    Teacher, Room, Class, Lesson, TimeSlot, Assignment, Timetable,
    Weekday, RoomType
)
from constraints import (
    check_teacher_conflict,
    check_room_conflict,
    check_class_conflict,
    check_room_type,
    check_teacher_availability
)


class BacktrackSolver:
    """再帰的バックトラックによる時間割生成"""
    
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
        self.lessons = list(lessons)
        
        self.timeslots = TimeSlot.all_slots()
        
        # 同期グループの構築
        self.sync_groups: Dict[str, List[Lesson]] = {}
        for lesson in self.lessons:
            if lesson.synchronization_id:
                if lesson.synchronization_id not in self.sync_groups:
                    self.sync_groups[lesson.synchronization_id] = []
                self.sync_groups[lesson.synchronization_id].append(lesson)
    
    def solve(self, max_attempts: int = 10000) -> Optional[Timetable]:
        """
        バックトラックで時間割を生成
        
        Args:
            max_attempts: 最大試行回数
        
        Returns:
            生成された時間割（解が見つからない場合はNone）
        """
        # Lessonを配置の難しさでソート（MRVヒューリスティック）
        sorted_lessons = self._sort_lessons_by_difficulty()
        
        # 各Lessonの配置タスクを作成（units分だけコピー）
        tasks: List[Tuple[Lesson, int]] = []  # (lesson, unit_index)
        for lesson in sorted_lessons:
            for unit_index in range(lesson.units):
                tasks.append((lesson, unit_index))
        
        timetable = Timetable()
        self.attempt_count = 0
        self.max_attempts = max_attempts
        
        if self._backtrack(tasks, 0, timetable):
            return timetable
        else:
            print(f"解が見つかりませんでした（{self.attempt_count}回試行）")
            return None
    
    def _sort_lessons_by_difficulty(self) -> List[Lesson]:
        """
        Lessonを配置の難しさでソート（難しいものから優先）
        
        基準:
        1. 同期制約があるLesson
        2. 担当可能な教員が少ない
        3. 必要な教室タイプが少ない
        4. 週単位数が多い
        """
        def difficulty_score(lesson: Lesson) -> Tuple:
            # 同期制約がある場合は優先度が高い
            has_sync = 1 if lesson.synchronization_id else 0
            
            # 担当可能な教員数（少ないほど難しい）
            num_teachers = len(lesson.teacher_ids)
            
            # 適切な教室数（少ないほど難しい）
            num_rooms = len([r for r in self.rooms.values() if r.room_type == lesson.room_type_required])
            
            # 週単位数（多いほど難しい）
            units = lesson.units
            
            # タプルで返す（降順でソート）
            return (-has_sync, num_teachers, num_rooms, -units)
        
        return sorted(self.lessons, key=difficulty_score)
    
    def _backtrack(
        self,
        tasks: List[Tuple[Lesson, int]],
        task_index: int,
        timetable: Timetable
    ) -> bool:
        """
        再帰的バックトラック
        
        Args:
            tasks: 配置すべきタスクのリスト
            task_index: 現在のタスクインデックス
            timetable: 現在の時間割
        
        Returns:
            解が見つかったか
        """
        # 試行回数の上限チェック
        self.attempt_count += 1
        if self.attempt_count > self.max_attempts:
            return False
        
        # 全てのタスクが配置された
        if task_index >= len(tasks):
            return True
        
        lesson, unit_index = tasks[task_index]
        
        # 同期制約がある場合の処理
        if lesson.synchronization_id:
            sync_lessons = self.sync_groups[lesson.synchronization_id]
            # 同期グループの最初のLessonの場合のみ配置を試みる
            if lesson == sync_lessons[0]:
                return self._place_synchronized_lessons(sync_lessons, unit_index, tasks, task_index, timetable)
            else:
                # 他の同期Lessonは既に配置済みなのでスキップ
                return self._backtrack(tasks, task_index + 1, timetable)
        
        # 通常のLesson配置
        # 既に配置済みのtimeslotを取得
        already_used_timeslots = {
            a.timeslot for a in timetable.assignments
            if a.lesson.id == lesson.id
        }
        
        # 配置可能なtimeslotを試す
        for timeslot in self.timeslots:
            # 同じLessonは異なるtimeslotに配置
            if timeslot in already_used_timeslots:
                continue
            
            # 適切な教室と教員の組み合わせを試す
            for room in self.rooms.values():
                if room.room_type != lesson.room_type_required:
                    continue
                
                for teacher_id in lesson.teacher_ids:
                    teacher = self.teachers[teacher_id]
                    
                    # 教員が担当可能な時間かチェック
                    if not teacher.is_available(timeslot):
                        continue
                    
                    # 配置を試みる
                    assignment = Assignment(
                        lesson=lesson,
                        timeslot=timeslot,
                        room=room,
                        teacher_id=teacher_id
                    )
                    
                    # 制約チェック
                    if self._is_valid_placement(timetable, assignment):
                        # 配置を追加
                        timetable.add_assignment(assignment)
                        
                        # 次のタスクへ
                        if self._backtrack(tasks, task_index + 1, timetable):
                            return True
                        
                        # バックトラック
                        timetable.assignments.pop()
        
        return False
    
    def _place_synchronized_lessons(
        self,
        sync_lessons: List[Lesson],
        unit_index: int,
        tasks: List[Tuple[Lesson, int]],
        task_index: int,
        timetable: Timetable
    ) -> bool:
        """
        同期制約のあるLessonを同時に配置
        
        Args:
            sync_lessons: 同期グループのLesson群
            unit_index: 配置する単位インデックス
            tasks: 全タスクリスト
            task_index: 現在のタスクインデックス
            timetable: 現在の時間割
        
        Returns:
            配置に成功したか
        """
        # 全ての同期Lessonで既に使用されているtimeslotを収集
        already_used_timeslots = set()
        for lesson in sync_lessons:
            for a in timetable.assignments:
                if a.lesson.id == lesson.id:
                    already_used_timeslots.add(a.timeslot)
        
        # 各timeslotで全ての同期Lessonを配置できるか試す
        for timeslot in self.timeslots:
            if timeslot in already_used_timeslots:
                continue
            
            # 各同期Lessonの配置を試みる
            sync_assignments = []
            placement_failed = False
            
            for lesson in sync_lessons:
                # 適切な教室と教員を見つける
                placed = False
                
                for room in self.rooms.values():
                    if room.room_type != lesson.room_type_required:
                        continue
                    
                    for teacher_id in lesson.teacher_ids:
                        teacher = self.teachers[teacher_id]
                        
                        if not teacher.is_available(timeslot):
                            continue
                        
                        assignment = Assignment(
                            lesson=lesson,
                            timeslot=timeslot,
                            room=room,
                            teacher_id=teacher_id
                        )
                        
                        # 一時的な時間割で制約チェック
                        temp_timetable = Timetable(assignments=timetable.assignments + sync_assignments)
                        
                        if self._is_valid_placement(temp_timetable, assignment):
                            sync_assignments.append(assignment)
                            placed = True
                            break
                    
                    if placed:
                        break
                
                if not placed:
                    placement_failed = True
                    break
            
            # 全ての同期Lessonの配置に成功した場合
            if not placement_failed and len(sync_assignments) == len(sync_lessons):
                # 全ての配置を追加
                for assignment in sync_assignments:
                    timetable.add_assignment(assignment)
                
                # 次のタスクへ（同期グループの数だけスキップ）
                next_task_index = task_index + len(sync_lessons)
                if self._backtrack(tasks, next_task_index, timetable):
                    return True
                
                # バックトラック
                for _ in sync_assignments:
                    timetable.assignments.pop()
        
        return False
    
    def _is_valid_placement(self, timetable: Timetable, new_assignment: Assignment) -> bool:
        """
        新しい配置が制約を満たすかチェック
        
        Args:
            timetable: 現在の時間割
            new_assignment: 新しい配置
        
        Returns:
            制約を満たすか
        """
        # 一時的に配置を追加
        temp_timetable = Timetable(assignments=timetable.assignments + [new_assignment])
        
        # 各制約をチェック
        is_valid, _ = check_teacher_conflict(temp_timetable)
        if not is_valid:
            return False
        
        is_valid, _ = check_room_conflict(temp_timetable)
        if not is_valid:
            return False
        
        is_valid, _ = check_class_conflict(temp_timetable)
        if not is_valid:
            return False
        
        return True
