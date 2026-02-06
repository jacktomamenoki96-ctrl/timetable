"""
簡易テスト - OR-Tools不要版

バックトラックソルバーのみを使用した検証テスト
"""
from models import (
    Teacher, Room, Class, Lesson, TimeSlot, Weekday, RoomType
)
from backtrack_solver import BacktrackSolver
from constraints import is_valid_assignment, validate_input_data
from utils import print_timetable, print_statistics


def simple_test():
    """1クラスの簡単なケースでテスト"""
    print("=" * 80)
    print("時間割自動生成エンジン - 簡易テスト")
    print("=" * 80)
    print()
    
    # シンプルなデータセット（1クラスのみ）
    teachers = [
        Teacher.create_with_full_availability("T1", "数学教員"),
        Teacher.create_with_full_availability("T2", "英語教員"),
        Teacher.create_with_full_availability("T3", "理科教員"),
    ]
    
    rooms = [
        Room("R1", "普通教室A", RoomType.GENERAL, 40),
        Room("R2", "普通教室B", RoomType.GENERAL, 40),
        Room("R3", "理科室", RoomType.SCIENCE, 40),
    ]
    
    classes = [
        Class("1A", "1年A組", 35),
    ]
    
    lessons = [
        Lesson("L1", "数学", 3, ["T1"], ["1A"], RoomType.GENERAL),
        Lesson("L2", "英語", 3, ["T2"], ["1A"], RoomType.GENERAL),
        Lesson("L3", "理科", 2, ["T3"], ["1A"], RoomType.SCIENCE),
    ]
    
    print("テストデータ:")
    print(f"  - クラス数: {len(classes)}")
    print(f"  - 教員数: {len(teachers)}")
    print(f"  - 教室数: {len(rooms)}")
    print(f"  - 授業数: {len(lessons)} (総コマ数: {sum(l.units for l in lessons)})")
    print()
    
    # 入力データ検証
    is_valid_input, errors = validate_input_data(teachers, rooms, classes, lessons)
    if not is_valid_input:
        print("入力データエラー:")
        for error in errors:
            print(f"  ✗ {error}")
        return
    
    print("✓ 入力データ検証: OK")
    print()
    
    # ソルバー実行
    print("バックトラックソルバーを実行中...")
    solver = BacktrackSolver(teachers, rooms, classes, lessons)
    
    import time
    start_time = time.time()
    timetable = solver.solve(max_attempts=10000)
    elapsed_time = time.time() - start_time
    
    if timetable:
        print(f"✓ 時間割生成成功！ ({elapsed_time:.2f}秒, {solver.attempt_count}回試行)")
        print()
        
        # 制約チェック
        teachers_dict = {t.id: t for t in teachers}
        is_valid, errors = is_valid_assignment(timetable, teachers_dict, lessons)
        
        if is_valid:
            print("✓ 全ハード制約を満たしています")
        else:
            print("✗ 制約違反が検出されました:")
            for error in errors:
                print(f"  - {error}")
        print()
        
        # 時間割表示
        print_timetable(timetable, class_id="1A")
        print_statistics(timetable)
        
    else:
        print(f"✗ 時間割生成失敗 ({elapsed_time:.2f}秒)")


if __name__ == "__main__":
    simple_test()
