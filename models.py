"""
時間割自動生成エンジン - データモデル定義

公立高校の時間割を表現するためのエンティティ定義
"""
from dataclasses import dataclass, field
from typing import List, Optional, Set
from enum import Enum


class Weekday(Enum):
    """曜日の列挙型"""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4

    @classmethod
    def all(cls) -> List['Weekday']:
        """全曜日をリストで取得"""
        return [cls.MONDAY, cls.TUESDAY, cls.WEDNESDAY, cls.THURSDAY, cls.FRIDAY]


class RoomType(Enum):
    """教室タイプの列挙型"""
    GENERAL = "general"          # 普通教室
    SCIENCE = "science"          # 理科室
    GYM = "gym"                  # 体育館
    MUSIC = "music"              # 音楽室
    ART = "art"                  # 美術室
    COMPUTER = "computer"        # コンピュータ室
    HOME_EC = "home_ec"          # 家庭科室


@dataclass(frozen=True)
class TimeSlot:
    """時間枠: 曜日 × 時限"""
    weekday: Weekday
    period: int  # 1-6

    def __post_init__(self):
        if not 1 <= self.period <= 6:
            raise ValueError(f"Period must be between 1 and 6, got {self.period}")

    def __str__(self) -> str:
        weekday_names = {
            Weekday.MONDAY: "月",
            Weekday.TUESDAY: "火",
            Weekday.WEDNESDAY: "水",
            Weekday.THURSDAY: "木",
            Weekday.FRIDAY: "金"
        }
        return f"{weekday_names[self.weekday]}{self.period}"

    @classmethod
    def all_slots(cls) -> List['TimeSlot']:
        """全ての時間枠（5曜日×6時限=30コマ）を生成"""
        slots = []
        for weekday in Weekday.all():
            for period in range(1, 7):
                slots.append(cls(weekday=weekday, period=period))
        return slots


@dataclass
class Teacher:
    """教員エンティティ"""
    id: str
    name: str
    # 担当可能時間マトリクス: availability[weekday.value][period-1] = True/False
    availability: List[List[bool]] = field(default_factory=lambda: [[True] * 6 for _ in range(5)])

    def is_available(self, timeslot: TimeSlot) -> bool:
        """指定時間枠で担当可能かチェック"""
        return self.availability[timeslot.weekday.value][timeslot.period - 1]

    def set_availability(self, timeslot: TimeSlot, available: bool):
        """担当可能時間を設定"""
        self.availability[timeslot.weekday.value][timeslot.period - 1] = available

    @classmethod
    def create_with_full_availability(cls, id: str, name: str) -> 'Teacher':
        """全時間帯で担当可能な教員を作成"""
        return cls(id=id, name=name)

    @classmethod
    def create_with_no_availability(cls, id: str, name: str) -> 'Teacher':
        """全時間帯で担当不可の教員を作成（制約設定のベース用）"""
        return cls(id=id, name=name, availability=[[False] * 6 for _ in range(5)])


@dataclass
class Room:
    """教室エンティティ"""
    id: str
    name: str
    room_type: RoomType
    capacity: int

    def __str__(self) -> str:
        return f"{self.name}({self.room_type.value}, 定員{self.capacity})"


@dataclass
class Class:
    """HRクラス（ホームルームクラス）エンティティ"""
    id: str
    name: str  # 例: "1-A", "2-B"
    size: int  # 生徒数

    def __str__(self) -> str:
        return f"{self.name}({self.size}名)"


@dataclass
class Lesson:
    """授業タスクエンティティ"""
    id: str
    subject: str  # 科目名
    units: int  # 週単位数（週に何コマ必要か）
    teacher_ids: List[str]  # 担当教員IDリスト（複数教員による授業も可）
    class_ids: List[str]  # 対象クラスIDリスト（合同クラスも可）
    room_type_required: RoomType  # 必要な教室タイプ
    synchronization_id: Optional[str] = None  # 同期ID（同じIDの授業は同一時間枠に配置）

    def __post_init__(self):
        if self.units < 1:
            raise ValueError(f"Units must be at least 1, got {self.units}")
        if not self.teacher_ids:
            raise ValueError("At least one teacher must be assigned")
        if not self.class_ids:
            raise ValueError("At least one class must be assigned")

    def __str__(self) -> str:
        sync_info = f" [同期:{self.synchronization_id}]" if self.synchronization_id else ""
        return f"{self.subject} (週{self.units}コマ){sync_info}"


@dataclass
class Assignment:
    """授業配置: 1つのLessonを特定のTimeSlot、Room、Teacherに割り当て"""
    lesson: Lesson
    timeslot: TimeSlot
    room: Room
    teacher_id: str  # 実際に担当する教員ID（lesson.teacher_idsから選択）

    def __post_init__(self):
        if self.teacher_id not in self.lesson.teacher_ids:
            raise ValueError(
                f"Teacher {self.teacher_id} is not in lesson's teacher list: {self.lesson.teacher_ids}"
            )

    def __str__(self) -> str:
        return f"{self.timeslot}: {self.lesson.subject} @ {self.room.name} by {self.teacher_id}"


@dataclass
class Timetable:
    """時間割全体: Assignmentのコレクション"""
    assignments: List[Assignment] = field(default_factory=list)

    def add_assignment(self, assignment: Assignment):
        """配置を追加"""
        self.assignments.append(assignment)

    def get_assignments_by_timeslot(self, timeslot: TimeSlot) -> List[Assignment]:
        """特定時間枠の配置を取得"""
        return [a for a in self.assignments if a.timeslot == timeslot]

    def get_assignments_by_teacher(self, teacher_id: str) -> List[Assignment]:
        """特定教員の配置を取得"""
        return [a for a in self.assignments if a.teacher_id == teacher_id]

    def get_assignments_by_room(self, room_id: str) -> List[Assignment]:
        """特定教室の配置を取得"""
        return [a for a in self.assignments if a.room.id == room_id]

    def get_assignments_by_class(self, class_id: str) -> List[Assignment]:
        """特定クラスの配置を取得"""
        return [a for a in self.assignments if class_id in a.lesson.class_ids]

    def get_assignments_by_lesson(self, lesson_id: str) -> List[Assignment]:
        """特定Lessonの全配置を取得"""
        return [a for a in self.assignments if a.lesson.id == lesson_id]

    def __len__(self) -> int:
        return len(self.assignments)

    def __str__(self) -> str:
        return f"Timetable with {len(self.assignments)} assignments"
