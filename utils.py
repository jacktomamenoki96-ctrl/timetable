"""
時間割自動生成エンジン - ユーティリティ関数

時間割の表示、出力、入力データ検証など
"""
from typing import List, Dict, Optional
import csv
from models import Timetable, TimeSlot, Weekday, Teacher, Room, Class, Lesson
from constraints import validate_input_data


def print_timetable(timetable: Timetable, class_id: Optional[str] = None):
    """
    時間割を見やすく表形式で表示
    
    Args:
        timetable: 表示する時間割
        class_id: 特定のクラスIDを指定すると、そのクラスの時間割のみ表示
    """
    from typing import Optional
    
    # 時間枠ごとにグループ化
    slots_dict: Dict[TimeSlot, List] = {}
    for timeslot in TimeSlot.all_slots():
        slots_dict[timeslot] = []
    
    for assignment in timetable.assignments:
        # クラスフィルタ
        if class_id and class_id not in assignment.lesson.class_ids:
            continue
        
        slots_dict[assignment.timeslot].append(assignment)
    
    # ヘッダー
    print("\n" + "=" * 100)
    if class_id:
        print(f"時間割 - クラス {class_id}")
    else:
        print("時間割 - 全体")
    print("=" * 100)
    
    # 曜日ごとに表示
    weekday_names = {
        Weekday.MONDAY: "月曜日",
        Weekday.TUESDAY: "火曜日",
        Weekday.WEDNESDAY: "水曜日",
        Weekday.THURSDAY: "木曜日",
        Weekday.FRIDAY: "金曜日"
    }
    
    for weekday in Weekday.all():
        print(f"\n【{weekday_names[weekday]}】")
        print("-" * 100)
        
        for period in range(1, 7):
            timeslot = TimeSlot(weekday=weekday, period=period)
            assignments = slots_dict[timeslot]
            
            if assignments:
                print(f"{period}時限目:")
                for assignment in assignments:
                    class_names = ", ".join(assignment.lesson.class_ids)
                    print(f"  - {assignment.lesson.subject} ({class_names}) | " +
                          f"教室: {assignment.room.name} | 教員: {assignment.teacher_id}")
            else:
                print(f"{period}時限目: (空き)")
    
    print("\n" + "=" * 100 + "\n")


def print_teacher_schedule(timetable: Timetable, teacher_id: str, teacher_name: str):
    """
    特定教員のスケジュールを表示
    
    Args:
        timetable: 時間割
        teacher_id: 教員ID
        teacher_name: 教員名
    """
    print(f"\n教員スケジュール - {teacher_name} ({teacher_id})")
    print("=" * 80)
    
    assignments = timetable.get_assignments_by_teacher(teacher_id)
    
    # 曜日・時限でグループ化
    schedule: Dict[TimeSlot, List] = {}
    for assignment in assignments:
        if assignment.timeslot not in schedule:
            schedule[assignment.timeslot] = []
        schedule[assignment.timeslot].append(assignment)
    
    # 曜日ごとに表示
    weekday_names = {
        Weekday.MONDAY: "月",
        Weekday.TUESDAY: "火",
        Weekday.WEDNESDAY: "水",
        Weekday.THURSDAY: "木",
        Weekday.FRIDAY: "金"
    }
    
    for weekday in Weekday.all():
        print(f"\n{weekday_names[weekday]}曜日:")
        for period in range(1, 7):
            timeslot = TimeSlot(weekday=weekday, period=period)
            if timeslot in schedule:
                for assignment in schedule[timeslot]:
                    class_names = ", ".join(assignment.lesson.class_ids)
                    print(f"  {period}限: {assignment.lesson.subject} ({class_names}) @ {assignment.room.name}")
            else:
                print(f"  {period}限: -")
    
    print("\n" + "=" * 80 + "\n")


def export_to_csv(timetable: Timetable, filename: str):
    """
    時間割をCSVファイルに出力
    
    Args:
        timetable: 出力する時間割
        filename: 出力ファイル名
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # ヘッダー
        writer.writerow([
            '曜日', '時限', '科目', 'クラス', '教室', '教員ID', '同期ID'
        ])
        
        # データ
        weekday_names = {
            Weekday.MONDAY: "月",
            Weekday.TUESDAY: "火",
            Weekday.WEDNESDAY: "水",
            Weekday.THURSDAY: "木",
            Weekday.FRIDAY: "金"
        }
        
        for assignment in sorted(
            timetable.assignments,
            key=lambda a: (a.timeslot.weekday.value, a.timeslot.period)
        ):
            writer.writerow([
                weekday_names[assignment.timeslot.weekday],
                assignment.timeslot.period,
                assignment.lesson.subject,
                ", ".join(assignment.lesson.class_ids),
                assignment.room.name,
                assignment.teacher_id,
                assignment.lesson.synchronization_id or ""
            ])
    
    print(f"時間割を {filename} に出力しました")


def print_statistics(timetable: Timetable):
    """
    時間割の統計情報を表示
    
    Args:
        timetable: 時間割
    """
    print("\n時間割統計情報")
    print("=" * 60)
    
    # 総授業数
    print(f"総配置数: {len(timetable.assignments)} コマ")
    
    # 教員ごとの授業数
    teacher_counts: Dict[str, int] = {}
    for assignment in timetable.assignments:
        teacher_id = assignment.teacher_id
        teacher_counts[teacher_id] = teacher_counts.get(teacher_id, 0) + 1
    
    print("\n教員別授業数:")
    for teacher_id, count in sorted(teacher_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {teacher_id}: {count}コマ")
    
    # 教室ごとの使用数
    room_counts: Dict[str, int] = {}
    for assignment in timetable.assignments:
        room_name = assignment.room.name
        room_counts[room_name] = room_counts.get(room_name, 0) + 1
    
    print("\n教室別使用数:")
    for room_name, count in sorted(room_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {room_name}: {count}コマ")
    
    # 時間枠ごとの使用率
    timeslot_counts: Dict[TimeSlot, int] = {}
    for assignment in timetable.assignments:
        timeslot = assignment.timeslot
        timeslot_counts[timeslot] = timeslot_counts.get(timeslot, 0) + 1
    
    print("\n時間枠別配置数（混雑状況）:")
    weekday_names = {
        Weekday.MONDAY: "月",
        Weekday.TUESDAY: "火",
        Weekday.WEDNESDAY: "水",
        Weekday.THURSDAY: "木",
        Weekday.FRIDAY: "金"
    }
    
    for weekday in Weekday.all():
        print(f"\n  {weekday_names[weekday]}曜日:")
        for period in range(1, 7):
            timeslot = TimeSlot(weekday=weekday, period=period)
            count = timeslot_counts.get(timeslot, 0)
            bar = "■" * count
            print(f"    {period}限: {bar} ({count})")
    
    print("\n" + "=" * 60 + "\n")


def validate_and_print_errors(
    teachers: List[Teacher],
    rooms: List[Room],
    classes: List[Class],
    lessons: List[Lesson]
) -> bool:
    """
    入力データを検証し、エラーがあれば表示
    
    Returns:
        データが有効か
    """
    is_valid, errors = validate_input_data(teachers, rooms, classes, lessons)
    
    if not is_valid:
        print("\n入力データに問題があります:")
        print("=" * 60)
        for error in errors:
            print(f"  ✗ {error}")
        print("=" * 60 + "\n")
    else:
        print("\n✓ 入力データの検証に成功しました\n")
    
    return is_valid
