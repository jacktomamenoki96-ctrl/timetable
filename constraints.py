"""
時間割自動生成エンジン - ハード制約検証

全てのハード制約をチェックする検証関数群
"""
from typing import List, Tuple, Dict, Set
from collections import defaultdict
from models import Timetable, Assignment, TimeSlot, Teacher, Room, Class, Lesson


def check_teacher_conflict(timetable: Timetable) -> Tuple[bool, List[str]]:
    """
    教員競合チェック: 同一教員が同じTimeSlotに複数の授業を担当していないか
    
    Returns:
        (違反なし, エラーメッセージリスト)
    """
    errors = []
    # TimeSlot × Teacher の組み合わせでグループ化
    teacher_slots: Dict[Tuple[TimeSlot, str], List[Assignment]] = defaultdict(list)
    
    for assignment in timetable.assignments:
        key = (assignment.timeslot, assignment.teacher_id)
        teacher_slots[key].append(assignment)
    
    # 同一時間枠に2つ以上の授業がある教員を検出
    for (timeslot, teacher_id), assignments in teacher_slots.items():
        if len(assignments) > 1:
            lesson_names = [a.lesson.subject for a in assignments]
            errors.append(
                f"教員競合: 教員 {teacher_id} が {timeslot} に複数の授業を担当 " +
                f"({', '.join(lesson_names)})"
            )
    
    return len(errors) == 0, errors


def check_room_conflict(timetable: Timetable) -> Tuple[bool, List[str]]:
    """
    教室競合チェック: 同一教室が同じTimeSlotに複数の授業で使用されていないか
    
    Returns:
        (違反なし, エラーメッセージリスト)
    """
    errors = []
    # TimeSlot × Room の組み合わせでグループ化
    room_slots: Dict[Tuple[TimeSlot, str], List[Assignment]] = defaultdict(list)
    
    for assignment in timetable.assignments:
        key = (assignment.timeslot, assignment.room.id)
        room_slots[key].append(assignment)
    
    # 同一時間枠に2つ以上の授業がある教室を検出
    for (timeslot, room_id), assignments in room_slots.items():
        if len(assignments) > 1:
            lesson_names = [a.lesson.subject for a in assignments]
            errors.append(
                f"教室競合: 教室 {assignments[0].room.name} が {timeslot} に複数の授業で使用 " +
                f"({', '.join(lesson_names)})"
            )
    
    return len(errors) == 0, errors


def check_class_conflict(timetable: Timetable) -> Tuple[bool, List[str]]:
    """
    クラス競合チェック: 同一HRクラスが同じTimeSlotに複数の授業を受講していないか
    
    Returns:
        (違反なし, エラーメッセージリスト)
    """
    errors = []
    # TimeSlot × Class の組み合わせでグループ化
    class_slots: Dict[Tuple[TimeSlot, str], List[Assignment]] = defaultdict(list)
    
    for assignment in timetable.assignments:
        for class_id in assignment.lesson.class_ids:
            key = (assignment.timeslot, class_id)
            class_slots[key].append(assignment)
    
    # 同一時間枠に2つ以上の授業があるクラスを検出
    for (timeslot, class_id), assignments in class_slots.items():
        if len(assignments) > 1:
            lesson_names = [a.lesson.subject for a in assignments]
            errors.append(
                f"クラス競合: クラス {class_id} が {timeslot} に複数の授業を受講 " +
                f"({', '.join(lesson_names)})"
            )
    
    return len(errors) == 0, errors


def check_synchronization(timetable: Timetable, lessons: List[Lesson]) -> Tuple[bool, List[str]]:
    """
    同時実施制約チェック: 同じSynchronization_IDを持つLessonが全て同一TimeSlotに配置されているか
    
    Args:
        timetable: チェック対象の時間割
        lessons: 全てのLessonリスト（同期IDをグループ化するため）
    
    Returns:
        (違反なし, エラーメッセージリスト)
    """
    errors = []
    
    # Synchronization_IDごとにLessonをグループ化
    sync_groups: Dict[str, List[Lesson]] = defaultdict(list)
    for lesson in lessons:
        if lesson.synchronization_id:
            sync_groups[lesson.synchronization_id].append(lesson)
    
    # 各同期グループについて、全てのLessonが同じTimeSlotに配置されているかチェック
    for sync_id, sync_lessons in sync_groups.items():
        # 各Lessonが配置されているTimeSlotを収集
        lesson_timeslots: Dict[str, Set[TimeSlot]] = {}
        
        for lesson in sync_lessons:
            assignments = [a for a in timetable.assignments if a.lesson.id == lesson.id]
            timeslots = {a.timeslot for a in assignments}
            lesson_timeslots[lesson.id] = timeslots
        
        # 全てのLessonのTimeSlotが一致しているかチェック
        if len(lesson_timeslots) > 0:
            # 各Lessonの全配置について、他のLessonも同じTimeSlotに配置されているかチェック
            for lesson in sync_lessons:
                lesson_slots = lesson_timeslots.get(lesson.id, set())
                
                for timeslot in lesson_slots:
                    # 他の同期Lessonも同じTimeSlotに配置されているかチェック
                    for other_lesson in sync_lessons:
                        if other_lesson.id != lesson.id:
                            other_slots = lesson_timeslots.get(other_lesson.id, set())
                            if timeslot not in other_slots:
                                errors.append(
                                    f"同期制約違反: 同期ID '{sync_id}' のLesson '{lesson.subject}' と " +
                                    f"'{other_lesson.subject}' が同じTimeSlotに配置されていない " +
                                    f"('{lesson.subject}'は{timeslot}に配置)"
                                )
    
    return len(errors) == 0, errors


def check_room_type(timetable: Timetable) -> Tuple[bool, List[str]]:
    """
    設備制約チェック: Lessonが要求するRoom_TypeとAssignされたRoomのタイプが一致しているか
    
    Returns:
        (違反なし, エラーメッセージリスト)
    """
    errors = []
    
    for assignment in timetable.assignments:
        required_type = assignment.lesson.room_type_required
        actual_type = assignment.room.room_type
        
        if required_type != actual_type:
            errors.append(
                f"教室タイプ不一致: Lesson '{assignment.lesson.subject}' は {required_type.value} が必要だが、" +
                f"{actual_type.value} の教室 '{assignment.room.name}' が割り当てられている ({assignment.timeslot})"
            )
    
    return len(errors) == 0, errors


def check_teacher_availability(
    timetable: Timetable,
    teachers: Dict[str, Teacher]
) -> Tuple[bool, List[str]]:
    """
    教員稼働制約チェック: Teacherの担当可能時間内にLessonが配置されているか
    
    Args:
        timetable: チェック対象の時間割
        teachers: 教員ID -> Teacherオブジェクトの辞書
    
    Returns:
        (違反なし, エラーメッセージリスト)
    """
    errors = []
    
    for assignment in timetable.assignments:
        teacher_id = assignment.teacher_id
        teacher = teachers.get(teacher_id)
        
        if teacher is None:
            errors.append(
                f"教員不明: 教員ID '{teacher_id}' が見つかりません " +
                f"(Lesson '{assignment.lesson.subject}', {assignment.timeslot})"
            )
            continue
        
        if not teacher.is_available(assignment.timeslot):
            errors.append(
                f"教員稼働制約違反: 教員 '{teacher.name}' ({teacher_id}) は {assignment.timeslot} に " +
                f"担当不可だが、Lesson '{assignment.lesson.subject}' が割り当てられている"
            )
    
    return len(errors) == 0, errors


def check_lesson_units(timetable: Timetable, lessons: List[Lesson]) -> Tuple[bool, List[str]]:
    """
    週単位数チェック: 各Lessonが必要な週単位数だけ配置されているか
    
    Args:
        timetable: チェック対象の時間割
        lessons: 全てのLessonリスト
    
    Returns:
        (違反なし, エラーメッセージリスト)
    """
    errors = []
    
    for lesson in lessons:
        assignments = [a for a in timetable.assignments if a.lesson.id == lesson.id]
        assigned_units = len(assignments)
        
        if assigned_units != lesson.units:
            errors.append(
                f"週単位数不一致: Lesson '{lesson.subject}' (ID: {lesson.id}) は週{lesson.units}コマ必要だが、" +
                f"{assigned_units}コマしか配置されていない"
            )
    
    return len(errors) == 0, errors


def is_valid_assignment(
    timetable: Timetable,
    teachers: Dict[str, Teacher],
    lessons: List[Lesson]
) -> Tuple[bool, List[str]]:
    """
    統合検証関数: 全てのハード制約をチェック
    
    Args:
        timetable: チェック対象の時間割
        teachers: 教員ID -> Teacherオブジェクトの辞書
        lessons: 全てのLessonリスト
    
    Returns:
        (全制約を満たすか, エラーメッセージリスト)
    """
    all_errors = []
    
    # 各制約をチェック
    checks = [
        ("教員競合", check_teacher_conflict(timetable)),
        ("教室競合", check_room_conflict(timetable)),
        ("クラス競合", check_class_conflict(timetable)),
        ("同時実施制約", check_synchronization(timetable, lessons)),
        ("教室タイプ", check_room_type(timetable)),
        ("教員稼働制約", check_teacher_availability(timetable, teachers)),
        ("週単位数", check_lesson_units(timetable, lessons)),
    ]
    
    for check_name, (is_valid, errors) in checks:
        if not is_valid:
            all_errors.extend(errors)
    
    return len(all_errors) == 0, all_errors


def validate_input_data(
    teachers: List[Teacher],
    rooms: List[Room],
    classes: List[Class],
    lessons: List[Lesson]
) -> Tuple[bool, List[str]]:
    """
    入力データの整合性チェック
    
    Returns:
        (データが有効か, エラーメッセージリスト)
    """
    errors = []
    
    # 教員IDの重複チェック
    teacher_ids = [t.id for t in teachers]
    if len(teacher_ids) != len(set(teacher_ids)):
        errors.append("教員IDに重複があります")
    
    # 教室IDの重複チェック
    room_ids = [r.id for r in rooms]
    if len(room_ids) != len(set(room_ids)):
        errors.append("教室IDに重複があります")
    
    # クラスIDの重複チェック
    class_ids = [c.id for c in classes]
    if len(class_ids) != len(set(class_ids)):
        errors.append("クラスIDに重複があります")
    
    # LessonIDの重複チェック
    lesson_ids = [l.id for l in lessons]
    if len(lesson_ids) != len(set(lesson_ids)):
        errors.append("LessonIDに重複があります")
    
    # Lessonの教員IDが存在するかチェック
    teacher_id_set = set(teacher_ids)
    for lesson in lessons:
        for teacher_id in lesson.teacher_ids:
            if teacher_id not in teacher_id_set:
                errors.append(
                    f"Lesson '{lesson.subject}' に存在しない教員ID '{teacher_id}' が指定されています"
                )
    
    # LessonのクラスIDが存在するかチェック
    class_id_set = set(class_ids)
    for lesson in lessons:
        for class_id in lesson.class_ids:
            if class_id not in class_id_set:
                errors.append(
                    f"Lesson '{lesson.subject}' に存在しないクラスID '{class_id}' が指定されています"
                )
    
    # 各クラスの週単位数合計が妥当かチェック（週30コマを超えないか）
    for class_obj in classes:
        total_units = sum(
            lesson.units
            for lesson in lessons
            if class_obj.id in lesson.class_ids
        )
        if total_units > 30:
            errors.append(
                f"クラス '{class_obj.name}' の週単位数合計が {total_units} で、30を超えています"
            )
    
    return len(errors) == 0, errors
