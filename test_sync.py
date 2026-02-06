"""
複雑ケーステスト - 同期制約を含むテスト

選択科目の同期制約が正しく動作するかを検証
"""
from models import (
    Teacher, Room, Class, Lesson, TimeSlot, Weekday, RoomType
)
from backtrack_solver import BacktrackSolver
from constraints import is_valid_assignment
from utils import print_timetable


def test_synchronization():
    """同期制約のテスト"""
    print("=" * 80)
    print("同期制約（選択科目）のテスト")
    print("=" * 80)
    print()
    
    # データセット
    teachers = [
        Teacher.create_with_full_availability("T1", "数学教員"),
        Teacher.create_with_full_availability("T2", "音楽教員"),
        Teacher.create_with_full_availability("T3", "美術教員"),
    ]
    
    rooms = [
        Room("R1", "1-A教室", RoomType.GENERAL, 20),
        Room("R2", "1-B教室", RoomType.GENERAL, 20),
        Room("R3", "音楽室", RoomType.MUSIC, 40),
        Room("R4", "美術室", RoomType.ART, 40),
    ]
    
    classes = [
        Class("1A", "1年A組", 20),
        Class("1B", "1年B組", 20),
    ]
    
    lessons = [
        # 通常授業
        Lesson("L1", "数学1A", 2, ["T1"], ["1A"], RoomType.GENERAL),
        Lesson("L2", "数学1B", 2, ["T1"], ["1B"], RoomType.GENERAL),
        
        # 選択科目（音楽と美術を同じ時間枠に配置）
        Lesson("L3", "選択音楽", 2, ["T2"], ["1A", "1B"], RoomType.MUSIC, synchronization_id="ELEC"),
        Lesson("L4", "選択美術", 2, ["T3"], ["1A", "1B"], RoomType.ART, synchronization_id="ELEC"),
    ]
    
    print("テストケース:")
    print("  - 1A, 1Bの2クラス")
    print("  - 選択科目: 音楽と美術（同期ID 'ELEC'）")
    print("  - 期待動作: 音楽と美術が必ず同じ時間枠に配置される")
    print()
    
    # ソルバー実行
    print("バックトラックソルバーを実行中...")
    solver = BacktrackSolver(teachers, rooms, classes, lessons)
    
    import time
    start_time = time.time()
    timetable = solver.solve(max_attempts=20000)
    elapsed_time = time.time() - start_time
    
    if timetable:
        print(f"✓ 時間割生成成功！ ({elapsed_time:.2f}秒)")
        print()
        
        # 制約チェック
        teachers_dict = {t.id: t for t in teachers}
        is_valid, errors = is_valid_assignment(timetable, teachers_dict, lessons)
        
        if is_valid:
            print("✓ 全ハード制約を満たしています")
        else:
            print("✗ 制約違反:")
            for error in errors:
                print(f"  - {error}")
        print()
        
        # 同期制約の確認
        music_slots = set()
        art_slots = set()
        
        for assignment in timetable.assignments:
            if assignment.lesson.id == "L3":
                music_slots.add(assignment.timeslot)
            elif assignment.lesson.id == "L4":
                art_slots.add(assignment.timeslot)
        
        print("選択科目の配置確認:")
        print(f"  音楽が配置された時間枠: {[str(s) for s in sorted(music_slots, key=lambda x: (x.weekday.value, x.period))]}")
        print(f"  美術が配置された時間枠: {[str(s) for s in sorted(art_slots, key=lambda x: (x.weekday.value, x.period))]}")
        
        if music_slots == art_slots:
            print("  ✓ 音楽と美術が同じ時間枠に配置されています（同期制約OK）")
        else:
            print("  ✗ 音楽と美術が異なる時間枠に配置されています（同期制約NG）")
        print()
        
        # 時間割表示
        print_timetable(timetable, class_id="1A")
        print_timetable(timetable, class_id="1B")
        
    else:
        print(f"✗ 時間割生成失敗 ({elapsed_time:.2f}秒)")


if __name__ == "__main__":
    test_synchronization()
