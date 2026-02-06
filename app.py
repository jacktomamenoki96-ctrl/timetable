"""
時間割自動生成エンジン - Streamlit Webアプリケーション

Streamlitを使用したインタラクティブな時間割生成アプリ
"""
import streamlit as st
import pandas as pd
import io
from typing import Dict, List, Optional
from models import (
    Teacher, Room, Class, Lesson, TimeSlot, Timetable,
    Weekday, RoomType
)
from backtrack_solver import BacktrackSolver
from constraints import is_valid_assignment, validate_input_data
try:
    from solver import TimetableSolver
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


# ページ設定
st.set_page_config(
    page_title="時間割自動生成システム",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)


def parse_csv_teachers(df: pd.DataFrame) -> List[Teacher]:
    """
    CSVから教員データを読み込み
    
    期待されるカラム: teacher_id, teacher_name, availability_matrix (オプション)
    """
    teachers = []
    for _, row in df.iterrows():
        teacher_id = str(row['teacher_id'])
        teacher_name = str(row['teacher_name'])
        
        # 担当可能時間マトリクスがあれば読み込み（なければ全時間可）
        if 'availability_matrix' in row and pd.notna(row['availability_matrix']):
            # "1,1,1,1,1,1;1,1,1,1,1,1;..." のような形式を期待
            try:
                matrix_str = str(row['availability_matrix'])
                matrix = []
                for day_str in matrix_str.split(';'):
                    day_values = [bool(int(x)) for x in day_str.split(',')]
                    matrix.append(day_values)
                teacher = Teacher(id=teacher_id, name=teacher_name, availability=matrix)
            except:
                teacher = Teacher.create_with_full_availability(teacher_id, teacher_name)
        else:
            teacher = Teacher.create_with_full_availability(teacher_id, teacher_name)
        
        teachers.append(teacher)
    
    return teachers


def parse_csv_rooms(df: pd.DataFrame) -> List[Room]:
    """
    CSVから教室データを読み込み
    
    期待されるカラム: room_id, room_name, room_type, capacity
    """
    rooms = []
    for _, row in df.iterrows():
        room_id = str(row['room_id'])
        room_name = str(row['room_name'])
        room_type_str = str(row['room_type']).lower()
        capacity = int(row['capacity'])
        
        # RoomTypeにマッピング
        room_type_map = {
            'general': RoomType.GENERAL,
            'science': RoomType.SCIENCE,
            'gym': RoomType.GYM,
            'music': RoomType.MUSIC,
            'art': RoomType.ART,
            'computer': RoomType.COMPUTER,
            'home_ec': RoomType.HOME_EC,
        }
        
        room_type = room_type_map.get(room_type_str, RoomType.GENERAL)
        room = Room(id=room_id, name=room_name, room_type=room_type, capacity=capacity)
        rooms.append(room)
    
    return rooms


def parse_csv_classes(df: pd.DataFrame) -> List[Class]:
    """
    CSVからクラスデータを読み込み
    
    期待されるカラム: class_id, class_name, size
    """
    classes = []
    for _, row in df.iterrows():
        class_id = str(row['class_id'])
        class_name = str(row['class_name'])
        size = int(row['size'])
        
        cls = Class(id=class_id, name=class_name, size=size)
        classes.append(cls)
    
    return classes


def parse_csv_lessons(df: pd.DataFrame) -> List[Lesson]:
    """
    CSVから授業データを読み込み
    
    期待されるカラム: lesson_id, subject, units, teacher_ids, class_ids, room_type, synchronization_id (オプション)
    """
    lessons = []
    for _, row in df.iterrows():
        lesson_id = str(row['lesson_id'])
        subject = str(row['subject'])
        units = int(row['units'])
        
        # カンマ区切りのIDリストを解析
        teacher_ids = [t.strip() for t in str(row['teacher_ids']).split(',')]
        class_ids = [c.strip() for c in str(row['class_ids']).split(',')]
        
        room_type_str = str(row['room_type']).lower()
        room_type_map = {
            'general': RoomType.GENERAL,
            'science': RoomType.SCIENCE,
            'gym': RoomType.GYM,
            'music': RoomType.MUSIC,
            'art': RoomType.ART,
            'computer': RoomType.COMPUTER,
            'home_ec': RoomType.HOME_EC,
        }
        room_type = room_type_map.get(room_type_str, RoomType.GENERAL)
        
        # 同期IDはオプション
        sync_id = None
        if 'synchronization_id' in row and pd.notna(row['synchronization_id']):
            sync_id = str(row['synchronization_id'])
        
        lesson = Lesson(
            id=lesson_id,
            subject=subject,
            units=units,
            teacher_ids=teacher_ids,
            class_ids=class_ids,
            room_type_required=room_type,
            synchronization_id=sync_id
        )
        lessons.append(lesson)
    
    return lessons


def timetable_to_dataframe(timetable: Timetable) -> pd.DataFrame:
    """時間割をpandas DataFrameに変換"""
    weekday_names = {
        Weekday.MONDAY: "月",
        Weekday.TUESDAY: "火",
        Weekday.WEDNESDAY: "水",
        Weekday.THURSDAY: "木",
        Weekday.FRIDAY: "金"
    }
    
    data = []
    for assignment in timetable.assignments:
        data.append({
            "曜日": weekday_names[assignment.timeslot.weekday],
            "時限": assignment.timeslot.period,
            "科目": assignment.lesson.subject,
            "クラス": ", ".join(assignment.lesson.class_ids),
            "教室": assignment.room.name,
            "教員ID": assignment.teacher_id,
            "同期ID": assignment.lesson.synchronization_id or ""
        })
    
    df = pd.DataFrame(data)
    # 曜日と時限でソート
    weekday_order = ["月", "火", "水", "木", "金"]
    df["曜日"] = pd.Categorical(df["曜日"], categories=weekday_order, ordered=True)
    df = df.sort_values(["曜日", "時限"]).reset_index(drop=True)
    
    return df


def create_class_timetable(timetable: Timetable, class_id: str) -> pd.DataFrame:
    """特定クラスの時間割を2次元表形式で作成"""
    weekday_names = {
        Weekday.MONDAY: "月",
        Weekday.TUESDAY: "火",
        Weekday.WEDNESDAY: "水",
        Weekday.THURSDAY: "木",
        Weekday.FRIDAY: "金"
    }
    
    # 6時限×5曜日の空の表を作成
    periods = list(range(1, 7))
    weekdays = ["月", "火", "水", "木", "金"]
    
    data = {weekday: [""] * 6 for weekday in weekdays}
    
    # 時間割データを埋める
    for assignment in timetable.assignments:
        if class_id in assignment.lesson.class_ids:
            weekday = weekday_names[assignment.timeslot.weekday]
            period_idx = assignment.timeslot.period - 1
            
            cell_text = f"{assignment.lesson.subject}\n({assignment.room.name})"
            data[weekday][period_idx] = cell_text
    
    df = pd.DataFrame(data, index=[f"{p}限" for p in periods])
    
    return df


def create_teacher_timetable(timetable: Timetable, teacher_id: str) -> pd.DataFrame:
    """特定教員の時間割を2次元表形式で作成"""
    weekday_names = {
        Weekday.MONDAY: "月",
        Weekday.TUESDAY: "火",
        Weekday.WEDNESDAY: "水",
        Weekday.THURSDAY: "木",
        Weekday.FRIDAY: "金"
    }
    
    periods = list(range(1, 7))
    weekdays = ["月", "火", "水", "木", "金"]
    
    data = {weekday: [""] * 6 for weekday in weekdays}
    
    for assignment in timetable.assignments:
        if assignment.teacher_id == teacher_id:
            weekday = weekday_names[assignment.timeslot.weekday]
            period_idx = assignment.timeslot.period - 1
            
            cell_text = f"{assignment.lesson.subject}\n({', '.join(assignment.lesson.class_ids)})"
            data[weekday][period_idx] = cell_text
    
    df = pd.DataFrame(data, index=[f"{p}限" for p in periods])
    
    return df


def export_to_excel(timetable: Timetable, classes: List[Class], teachers: Dict[str, Teacher]) -> bytes:
    """時間割をExcelファイルとしてエクスポート"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 全体の時間割
        df_all = timetable_to_dataframe(timetable)
        df_all.to_excel(writer, sheet_name='全体', index=False)
        
        # クラスごとの時間割
        for cls in classes:
            df_class = create_class_timetable(timetable, cls.id)
            df_class.to_excel(writer, sheet_name=f'クラス_{cls.name}')
        
        # 教員ごとの時間割
        for teacher_id, teacher in teachers.items():
            df_teacher = create_teacher_timetable(timetable, teacher_id)
            # シート名は31文字まで
            sheet_name = f'教員_{teacher.name[:20]}'
            df_teacher.to_excel(writer, sheet_name=sheet_name)
    
    output.seek(0)
    return output.getvalue()


def main():
    st.title("📅 時間割自動生成システム")
    st.markdown("公立高校の時間割を自動生成します。CSVファイルをアップロードして開始してください。")
    
    # サイドバー: パラメータ設定
    st.sidebar.header("⚙️ 設定")
    
    solver_type = st.sidebar.selectbox(
        "ソルバーの種類",
        ["OR-Tools (推奨: 高精度)", "バックトラック法"] if ORTOOLS_AVAILABLE else ["バックトラック法"],
        help="Googleの最適化エンジンを使用し、複雑な制約でも高精度な時間割を生成します"
    )
    
    if solver_type == "バックトラック法":
        max_attempts = st.sidebar.number_input(
            "最大試行回数",
            min_value=1000,
            max_value=100000,
            value=20000,
            step=1000,
            help="バックトラック法の最大試行回数"
        )
    else:
        timeout = st.sidebar.number_input(
            "タイムアウト (秒)",
            min_value=10,
            max_value=600,
            value=120,
            step=10,
            help="最適解を見つけるまでの最大計算時間"
        )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📄 CSVフォーマット")
    st.sidebar.markdown("""
    **教員データ**: `teacher_id`, `teacher_name`
    
    **教室データ**: `room_id`, `room_name`, `room_type`, `capacity`
    
    **クラスデータ**: `class_id`, `class_name`, `size`
    
    **授業データ**: `lesson_id`, `subject`, `units`, `teacher_ids`, `class_ids`, `room_type`
    """)
    
    # メインエリア: データ入力
    st.header("📂 データ入力")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.subheader("教員データ")
        teachers_file = st.file_uploader("教員CSV", type=['csv'], key='teachers_upload')
    
    with col2:
        st.subheader("教室データ")
        rooms_file = st.file_uploader("教室CSV", type=['csv'], key='rooms_upload')
    
    with col3:
        st.subheader("クラスデータ")
        classes_file = st.file_uploader("クラスCSV", type=['csv'], key='classes_upload')
    
    with col4:
        st.subheader("授業データ")
        lessons_file = st.file_uploader("授業CSV", type=['csv'], key='lessons_upload')
    
    # データの読み込みと検証
    if teachers_file and rooms_file and classes_file and lessons_file:
        try:
            # CSVの読み込み
            df_teachers = pd.read_csv(teachers_file)
            df_rooms = pd.read_csv(rooms_file)
            df_classes = pd.read_csv(classes_file)
            df_lessons = pd.read_csv(lessons_file)
            
            # データ変換
            teachers = parse_csv_teachers(df_teachers)
            rooms = parse_csv_rooms(df_rooms)
            classes = parse_csv_classes(df_classes)
            lessons = parse_csv_lessons(df_lessons)
            
            # 入力データ検証
            is_valid, errors = validate_input_data(teachers, rooms, classes, lessons)
            
            if not is_valid:
                st.error("❌ 入力データにエラーがあります:")
                for error in errors:
                    st.error(f"  • {error}")
            else:
                st.success("✅ 入力データの検証に成功しました")
                
                # データサマリー
                st.info(f"📊 データサマリー: 教員 {len(teachers)}名 | 教室 {len(rooms)}室 | クラス {len(classes)}組 | 授業 {len(lessons)}科目 (総{sum(l.units for l in lessons)}コマ)")
                
                # 時間割生成ボタン
                st.markdown("---")
                if st.button("🚀 時間割生成開始", type="primary", use_container_width=True):
                    with st.spinner("時間割を生成中... しばらくお待ちください"):
                        import time
                        start_time = time.time()
                        
                        # ソルバーの選択
                        if solver_type == "OR-Tools (推奨: 高精度)" and ORTOOLS_AVAILABLE:
                            solver = TimetableSolver(teachers, rooms, classes, lessons)
                            timetable = solver.solve(timeout_seconds=timeout)
                        else:
                            solver = BacktrackSolver(teachers, rooms, classes, lessons)
                            timetable = solver.solve(max_attempts=max_attempts)
                        
                        elapsed_time = time.time() - start_time
                        
                        if timetable:
                            # 制約チェック
                            teachers_dict = {t.id: t for t in teachers}
                            is_valid_result, constraint_errors = is_valid_assignment(
                                timetable, teachers_dict, lessons
                            )
                            
                            st.session_state['timetable'] = timetable
                            st.session_state['teachers'] = teachers
                            st.session_state['classes'] = classes
                            st.session_state['generation_time'] = elapsed_time
                            st.session_state['is_valid'] = is_valid_result
                            st.session_state['errors'] = constraint_errors
                            
                            st.rerun()
                        else:
                            st.error(f"❌ 時間割の生成に失敗しました ({elapsed_time:.2f}秒)")
                            st.warning("制約が厳しすぎる可能性があります。データを見直すか、最大試行回数を増やしてください。")
        
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")
            st.exception(e)
    
    # 結果表示
    if 'timetable' in st.session_state:
        st.markdown("---")
        st.header("📋 生成結果")
        
        timetable = st.session_state['timetable']
        teachers = st.session_state['teachers']
        classes = st.session_state['classes']
        generation_time = st.session_state['generation_time']
        is_valid_result = st.session_state['is_valid']
        constraint_errors = st.session_state['errors']
        
        # 生成情報
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("生成時間", f"{generation_time:.2f}秒")
        with col2:
            st.metric("配置数", f"{len(timetable.assignments)}コマ")
        with col3:
            if is_valid_result:
                st.metric("制約チェック", "✅ 成功", delta="違反なし")
            else:
                st.metric("制約チェック", "⚠️ 警告", delta=f"{len(constraint_errors)}件")
        
        if not is_valid_result:
            with st.expander("制約違反の詳細"):
                for error in constraint_errors:
                    st.warning(error)
        
        # タブ表示
        tabs = st.tabs(["📊 全体", "📝 クラス別", "👨‍🏫 教員別", "💾 ダウンロード"])
        
        # 全体タブ
        with tabs[0]:
            st.subheader("全体時間割")
            df_all = timetable_to_dataframe(timetable)
            st.dataframe(df_all, use_container_width=True, height=600)
        
        # クラス別タブ
        with tabs[1]:
            st.subheader("クラス別時間割")
            class_names = [c.name for c in classes]
            selected_class = st.selectbox("クラスを選択", class_names)
            
            # 選択されたクラスのIDを取得
            selected_class_obj = next(c for c in classes if c.name == selected_class)
            df_class = create_class_timetable(timetable, selected_class_obj.id)
            
            st.dataframe(df_class, use_container_width=True)
        
        # 教員別タブ
        with tabs[2]:
            st.subheader("教員別時間割")
            teachers_dict = {t.id: t for t in teachers}
            teacher_names = [f"{t.name} ({t.id})" for t in teachers]
            selected_teacher = st.selectbox("教員を選択", teacher_names)
            
            # 選択された教員のIDを取得
            selected_teacher_id = selected_teacher.split('(')[1].rstrip(')')
            df_teacher = create_teacher_timetable(timetable, selected_teacher_id)
            
            st.dataframe(df_teacher, use_container_width=True)
        
        # ダウンロードタブ
        with tabs[3]:
            st.subheader("Excelダウンロード")
            st.markdown("生成された時間割を Excel ファイルとしてダウンロードできます。")
            
            teachers_dict = {t.id: t for t in teachers}
            excel_data = export_to_excel(timetable, classes, teachers_dict)
            
            st.download_button(
                label="📥 Excelファイルをダウンロード",
                data=excel_data,
                file_name="timetable.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            
            st.info("💡 Excelファイルには、全体の時間割、クラス別時間割、教員別時間割が含まれます。")


if __name__ == "__main__":
    main()
