"""
時間割自動生成エンジン - サンプルデータと使用例

実際の高校を模したサンプルデータと、ソルバーの使用方法を示すデモスクリプト
"""
from models import (
    Teacher, Room, Class, Lesson, TimeSlot, Weekday, RoomType
)
from solver import TimetableSolver
from backtrack_solver import BacktrackSolver
from utils import (
    print_timetable, print_teacher_schedule, export_to_csv,
    print_statistics, validate_and_print_errors
)
import time


def create_sample_data():
    """サンプルデータの作成"""
    
    # === 教員データ ===
    teachers = [
        Teacher.create_with_full_availability("T001", "田中先生（数学）"),
        Teacher.create_with_full_availability("T002", "佐藤先生（英語）"),
        Teacher.create_with_full_availability("T003", "鈴木先生（国語）"),
        Teacher.create_with_full_availability("T004", "高橋先生（理科）"),
        Teacher.create_with_full_availability("T005", "渡辺先生（社会）"),
        Teacher.create_with_full_availability("T006", "伊藤先生（体育）"),
        Teacher.create_with_full_availability("T007", "山本先生（音楽）"),
        Teacher.create_with_full_availability("T008", "中村先生（美術）"),
    ]
    
    # 一部の教員に稼働制約を追加（例: 水曜午後は不可）
    teachers[6].set_availability(TimeSlot(Weekday.WEDNESDAY, 5), False)
    teachers[6].set_availability(TimeSlot(Weekday.WEDNESDAY, 6), False)
    
    # === 教室データ ===
    rooms = [
        # 普通教室（6室）
        Room("R101", "1-1教室", RoomType.GENERAL, 40),
        Room("R102", "1-2教室", RoomType.GENERAL, 40),
        Room("R103", "1-3教室", RoomType.GENERAL, 40),
        Room("R201", "2-1教室", RoomType.GENERAL, 40),
        Room("R202", "2-2教室", RoomType.GENERAL, 40),
        Room("R203", "2-3教室", RoomType.GENERAL, 40),
        
        # 特別教室
        Room("R301", "理科室1", RoomType.SCIENCE, 40),
        Room("R302", "理科室2", RoomType.SCIENCE, 40),
        Room("R401", "音楽室", RoomType.MUSIC, 40),
        Room("R402", "美術室", RoomType.ART, 40),
        Room("R501", "体育館", RoomType.GYM, 200),
    ]
    
    # === クラスデータ ===
    classes = [
        Class("1A", "1年A組", 35),
        Class("1B", "1年B組", 35),
        Class("1C", "1年C組", 35),
    ]
    
    # === 授業データ ===
    lessons = []
    
    # 1年A組の授業
    lessons.extend([
        Lesson("L1A_Math", "数学1A", 4, ["T001"], ["1A"], RoomType.GENERAL),
        Lesson("L1A_Eng", "英語1A", 4, ["T002"], ["1A"], RoomType.GENERAL),
        Lesson("L1A_Jpn", "国語1A", 4, ["T003"], ["1A"], RoomType.GENERAL),
        Lesson("L1A_Sci", "理科1A", 3, ["T004"], ["1A"], RoomType.SCIENCE),
        Lesson("L1A_Soc", "社会1A", 3, ["T005"], ["1A"], RoomType.GENERAL),
        Lesson("L1A_PE", "体育1A", 3, ["T006"], ["1A"], RoomType.GYM),
        Lesson("L1A_Music", "音楽1A", 2, ["T007"], ["1A"], RoomType.MUSIC),
        Lesson("L1A_Art", "美術1A", 2, ["T008"], ["1A"], RoomType.ART),
    ])
    
    # 1年B組の授業
    lessons.extend([
        Lesson("L1B_Math", "数学1B", 4, ["T001"], ["1B"], RoomType.GENERAL),
        Lesson("L1B_Eng", "英語1B", 4, ["T002"], ["1B"], RoomType.GENERAL),
        Lesson("L1B_Jpn", "国語1B", 4, ["T003"], ["1B"], RoomType.GENERAL),
        Lesson("L1B_Sci", "理科1B", 3, ["T004"], ["1B"], RoomType.SCIENCE),
        Lesson("L1B_Soc", "社会1B", 3, ["T005"], ["1B"], RoomType.GENERAL),
        Lesson("L1B_PE", "体育1B", 3, ["T006"], ["1B"], RoomType.GYM),
        Lesson("L1B_Music", "音楽1B", 2, ["T007"], ["1B"], RoomType.MUSIC),
        Lesson("L1B_Art", "美術1B", 2, ["T008"], ["1B"], RoomType.ART),
    ])
    
    # 1年C組の授業
    lessons.extend([
        Lesson("L1C_Math", "数学1C", 4, ["T001"], ["1C"], RoomType.GENERAL),
        Lesson("L1C_Eng", "英語1C", 4, ["T002"], ["1C"], RoomType.GENERAL),
        Lesson("L1C_Jpn", "国語1C", 4, ["T003"], ["1C"], RoomType.GENERAL),
        Lesson("L1C_Sci", "理科1C", 3, ["T004"], ["1C"], RoomType.SCIENCE),
        Lesson("L1C_Soc", "社会1C", 3, ["T005"], ["1C"], RoomType.GENERAL),
        Lesson("L1C_PE", "体育1C", 3, ["T006"], ["1C"], RoomType.GYM),
        Lesson("L1C_Music", "音楽1C", 2, ["T007"], ["1C"], RoomType.MUSIC),
        Lesson("L1C_Art", "美術1C", 2, ["T008"], ["1C"], RoomType.ART),
    ])
    
    return teachers, rooms, classes, lessons


def create_sample_data_with_sync():
    """同期制約を含むサンプルデータ（選択科目のシミュレーション）"""
    
    teachers, rooms, classes, lessons = create_sample_data()
    
    # 選択科目を追加（音楽・美術は選択制、同じ時間に開講）
    # 1A, 1B, 1Cの音楽・美術を削除して、選択科目として再定義
    lessons = [l for l in lessons if "Music" not in l.id and "Art" not in l.id]
    
    # 選択科目A（音楽）と選択科目B（美術）を同期して配置
    lessons.extend([
        Lesson("L1_Music_Elec", "選択音楽", 2, ["T007"], ["1A", "1B", "1C"], RoomType.MUSIC, synchronization_id="ELEC1"),
        Lesson("L1_Art_Elec", "選択美術", 2, ["T008"], ["1A", "1B", "1C"], RoomType.ART, synchronization_id="ELEC1"),
    ])
    
    return teachers, rooms, classes, lessons


def demo_ortools_solver():
    """OR-Toolsソルバーのデモ"""
    print("\n" + "=" * 80)
    print("OR-Tools ソルバーによる時間割生成デモ")
    print("=" * 80 + "\n")
    
    # サンプルデータ作成
    teachers, rooms, classes, lessons = create_sample_data()
    
    # 入力データの検証
    if not validate_and_print_errors(teachers, rooms, classes, lessons):
        return
    
    # ソルバーの初期化
    solver = TimetableSolver(teachers, rooms, classes, lessons)
    
    print("ソルバーを実行中...")
    start_time = time.time()
    
    # 時間割生成
    timetable = solver.solve(timeout_seconds=120)
    
    elapsed_time = time.time() - start_time
    
    if timetable:
        print(f"✓ 時間割の生成に成功しました！（{elapsed_time:.2f}秒）\n")
        
        # 時間割を表示
        print_timetable(timetable, class_id="1A")
        
        # 統計情報
        print_statistics(timetable)
        
        # 教員スケジュール
        print_teacher_schedule(timetable, "T001", "田中先生（数学）")
        
        # CSV出力
        export_to_csv(timetable, "timetable_output.csv")
    else:
        print(f"✗ 時間割の生成に失敗しました（{elapsed_time:.2f}秒）")


def demo_backtrack_solver():
    """バックトラックソルバーのデモ"""
    print("\n" + "=" * 80)
    print("バックトラック ソルバーによる時間割生成デモ")
    print("=" * 80 + "\n")
    
    # サンプルデータ作成（クラスを減らして高速化）
    teachers, rooms, classes, lessons = create_sample_data()
    
    # 1クラスのみに絞る（バックトラックは遅いため）
    classes = [classes[0]]
    lessons = [l for l in lessons if "1A" in l.id]
    
    # 入力データの検証
    if not validate_and_print_errors(teachers, rooms, classes, lessons):
        return
    
    # ソルバーの初期化
    solver = BacktrackSolver(teachers, rooms, classes, lessons)
    
    print("ソルバーを実行中...")
    start_time = time.time()
    
    # 時間割生成
    timetable = solver.solve(max_attempts=50000)
    
    elapsed_time = time.time() - start_time
    
    if timetable:
        print(f"✓ 時間割の生成に成功しました！（{elapsed_time:.2f}秒）\n")
        
        # 時間割を表示
        print_timetable(timetable, class_id="1A")
    else:
        print(f"✗ 時間割の生成に失敗しました（{elapsed_time:.2f}秒）")


def demo_synchronized_lessons():
    """同期制約のデモ（選択科目）"""
    print("\n" + "=" * 80)
    print("同期制約（選択科目）のデモ")
    print("=" * 80 + "\n")
    
    # 同期制約を含むサンプルデータ
    teachers, rooms, classes, lessons = create_sample_data_with_sync()
    
    # 入力データの検証
    if not validate_and_print_errors(teachers, rooms, classes, lessons):
        return
    
    print("同期ID 'ELEC1' を持つ授業:")
    for lesson in lessons:
        if lesson.synchronization_id == "ELEC1":
            print(f"  - {lesson.subject} (対象: {', '.join(lesson.class_ids)})")
    print()
    
    # ソルバーの初期化
    solver = TimetableSolver(teachers, rooms, classes, lessons)
    
    print("ソルバーを実行中...")
    start_time = time.time()
    
    # 時間割生成
    timetable = solver.solve(timeout_seconds=120)
    
    elapsed_time = time.time() - start_time
    
    if timetable:
        print(f"✓ 時間割の生成に成功しました！（{elapsed_time:.2f}秒）\n")
        
        # 選択科目の配置を確認
        print("選択科目の配置状況:")
        for lesson in lessons:
            if lesson.synchronization_id == "ELEC1":
                assignments = timetable.get_assignments_by_lesson(lesson.id)
                for assignment in assignments:
                    print(f"  - {lesson.subject}: {assignment.timeslot}")
        print()
        
        # 各クラスの時間割を表示
        for class_obj in classes:
            print_timetable(timetable, class_id=class_obj.id)
    else:
        print(f"✗ 時間割の生成に失敗しました（{elapsed_time:.2f}秒）")


if __name__ == "__main__":
    # デモを実行
    print("\n" + "=" * 80)
    print("時間割自動生成エンジン - デモプログラム")
    print("=" * 80)
    
    print("\n実行するデモを選択してください:")
    print("1. OR-Tools ソルバー（標準）")
    print("2. バックトラック ソルバー（1クラスのみ）")
    print("3. 同期制約デモ（選択科目）")
    print("4. 全て実行")
    
    choice = input("\n選択 (1-4): ").strip()
    
    if choice == "1":
        demo_ortools_solver()
    elif choice == "2":
        demo_backtrack_solver()
    elif choice == "3":
        demo_synchronized_lessons()
    elif choice == "4":
        demo_ortools_solver()
        demo_backtrack_solver()
        demo_synchronized_lessons()
    else:
        print("無効な選択です")
