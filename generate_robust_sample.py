import csv
import os

def generate_sample_data():
    os.makedirs("sample_data_robust", exist_ok=True)
    
    # 1. Teachers (教員)
    teachers = [
        ["teacher_id", "teacher_name"],
        ["T001", "田中先生（数学）"],
        ["T002", "佐藤先生（英語）"],
        ["T003", "鈴木先生（国語）"],
        ["T004", "高橋先生（理科）"],
        ["T005", "渡辺先生（社会）"],
        ["T006", "伊藤先生（体育）"],
        ["T007", "山本先生（音楽）"],
        ["T008", "中村先生（美術）"],
        ["T009", "小林先生（家庭）"],
        ["T010", "加藤先生（情報）"],
    ]
    with open("sample_data_robust/teachers.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(teachers)
    
    # 2. Rooms (教室)
    rooms = [
        ["room_id", "room_name", "room_type", "capacity"],
        ["R101", "1-A教室", "general", "40"],
        ["R102", "1-B教室", "general", "40"],
        ["R103", "1-C教室", "general", "40"],
        ["R_SCI", "理科室", "science", "40"],
        ["R_GYM", "体育館", "gym", "100"],
        ["R_MUS", "音楽室", "music", "40"],
        ["R_ART", "美術室", "art", "40"],
        ["R_COM", "PC室", "computer", "40"],
        ["R_HOM", "家庭科室", "home_ec", "40"],
    ]
    with open("sample_data_robust/rooms.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rooms)
    
    # 3. Classes (クラス)
    classes = [
        ["class_id", "class_name", "size"],
        ["1A", "1年A組", "35"],
        ["1B", "1年B組", "35"],
        ["1C", "1年C組", "35"],
    ]
    with open("sample_data_robust/classes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(classes)
    
    # 4. Lessons (授業)
    # Header
    lessons_data = [["lesson_id", "subject", "units", "teacher_ids", "class_ids", "room_type", "synchronization_id"]]
    
    curriculum = [
        # 科目, 単位数, 教員ID, 教室タイプ
        ("数学I", 5, "T001", "general"),
        ("英語I", 5, "T002", "general"),
        ("国語I", 4, "T003", "general"),
        ("理科基礎", 3, "T004", "science"),
        ("社会総合", 3, "T005", "general"),
        ("音楽", 2, "T007", "music"),
        ("美術", 2, "T008", "art"),
        ("情報", 1, "T010", "computer"),
    ]
    
    # 個別授業の生成
    for cls in ["1A", "1B", "1C"]:
        for subj, unit, tid, rtype in curriculum:
            lessons_data.append([
                f"{cls}_{subj}", # lesson_id
                subj,            # subject
                str(unit),       # units
                tid,             # teacher_ids
                cls,             # class_ids
                rtype,           # room_type
                ""               # synchronization_id
            ])

    # 合同授業: 体育 (3クラス合同, 週3回)
    lessons_data.append([
        "ALL_PE", "体育", "3", "T006", "1A,1B,1C", "gym", ""
    ])
    
    # LHR (各クラス担任, 同時間)
    homeroom_teachers = {"1A": "T001", "1B": "T002", "1C": "T003"}
    for cls in ["1A", "1B", "1C"]:
        lessons_data.append([
            f"{cls}_LHR", "LHR", "1", homeroom_teachers[cls], cls, "general", "LHR_TIME"
        ])
        
    with open("sample_data_robust/lessons.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(lessons_data)
        
    print("Robust sample data generated in 'sample_data_robust/'")

if __name__ == "__main__":
    generate_sample_data()
