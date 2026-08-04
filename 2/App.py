"""
학교 수행평가 알림앱
- 학번 기반 로그인 (계정 없이 학번만 입력)
- 학번별 수강 과목 저장 (students.json)
- 과목별 수행평가 저장 (assessments.json) → 학번과 무관하게 같은 과목이면 같은 수행평가가 보임
"""

import streamlit as st
import json
import os
import string
import calendar
from datetime import date

# ------------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------------
st.set_page_config(page_title="수행평가 알림장", page_icon="📚", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STUDENTS_PATH = os.path.join(DATA_DIR, "students.json")
ASSESSMENTS_PATH = os.path.join(DATA_DIR, "assessments.json")

# 학교 지정 과목 (모든 학생 공통, 수정 불가)
FIXED_SUBJECTS = ["독서(일반)", "영어2(일반)", "심화 영어1(일반)", "운동과 건강"]

# 학생 선택 과목 (테마별) — 선택 시 A~Z 분반 알파벳을 붙여 저장
ELECTIVE_THEMES = {
    "🧮 기초": [
        "확률과 통계(일반)", "심화 수학1", "화법과 작문", "읽기",
        "미적분(일반)", "경제 수학", "심화 영어 독해1", "영어권 문화",
    ],
    "🌍 탐구": [
        "한국지리(일반)", "동아시아사(일반)", "사회문화(일반)", "윤리와 사상(일반)",
        "고전과 윤리", "지역 이해", "물리학2", "화학2", "생명과학2",
        "지구과학2", "생활과 과학",
    ],
    "🎨 예술·교양": [
        "미술사", "현대문학 감상", "데이터 과학과 머신러닝", "철학",
        "보건", "환경", "논술", "심리학",
    ],
}
ELECTIVE_BASES = [s for group in ELECTIVE_THEMES.values() for s in group]
ALPHABET = list(string.ascii_uppercase)
WEEKDAY_NAMES = ["일", "월", "화", "수", "목", "금", "토"]


# ------------------------------------------------------------------
# 데이터 저장/불러오기 유틸
# ------------------------------------------------------------------
def init_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(STUDENTS_PATH):
        with open(STUDENTS_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    if not os.path.exists(ASSESSMENTS_PATH):
        with open(ASSESSMENTS_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_students():
    return load_json(STUDENTS_PATH)


def get_assessments():
    return load_json(ASSESSMENTS_PATH)


def split_elective_label(label):
    """'지구과학2A' -> ('지구과학2', 'A') 로 분리. 학교 지정 과목이면 (None, None)."""
    for base in sorted(ELECTIVE_BASES, key=len, reverse=True):
        if label.startswith(base) and len(label) == len(base) + 1 and label[-1] in ALPHABET:
            return base, label[-1]
    return None, None


# ------------------------------------------------------------------
# 세션 상태 초기화
# ------------------------------------------------------------------
def init_session_state():
    defaults = {
        "page": "login",
        "student_id": None,
        "cal_year": date.today().year,
        "cal_month": date.today().month,
        "show_add_form": False,
        "selected_detail": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ------------------------------------------------------------------
# 페이지 1. 로그인 (학번 입력)
# ------------------------------------------------------------------
def render_login():
    st.title("📚 학교 수행평가 알림장")
    st.write("학번을 입력하면 해당 학번의 과목·수행평가 정보로 이동합니다.")
    st.caption("※ 2026학년도 고3 학생 대상으로 제작되었습니다.")

    with st.form("login_form"):
        student_id = st.text_input("학번 (예: 31111)", max_chars=10)
        submitted = st.form_submit_button("입장하기 →", use_container_width=True)

    if submitted:
        student_id = student_id.strip()
        if not student_id.isdigit():
            st.error("학번은 숫자로만 입력해주세요.")
            return
        st.session_state.student_id = student_id
        students = get_students()
        if student_id in students:
            st.session_state.page = "main"
        else:
            st.session_state.page = "select_subjects"
        st.rerun()


# ------------------------------------------------------------------
# 페이지 2. 과목 선택 (최초 진입 / 수정 모드 공용)
# ------------------------------------------------------------------
def render_select_subjects():
    student_id = st.session_state.student_id
    students = get_students()
    existing = students.get(student_id, [])
    is_editing = len(existing) > 0

    # 기존 선택값을 기반으로 기본값 계산 (수정 모드)
    existing_elective_map = {}  # base -> letter
    for label in existing:
        base, letter = split_elective_label(label)
        if base:
            existing_elective_map[base] = letter

    st.title(f"📝 과목 선택 — 학번 {student_id}")
    st.write("현재 수강 중인 과목을 선택해주세요. 선택과목은 분반(알파벳)까지 함께 지정합니다.")

    st.subheader("학교 지정 과목")
    st.caption("모든 학생 공통 과목으로 자동 선택되어 있으며 변경할 수 없습니다.")
    for subj in FIXED_SUBJECTS:
        st.checkbox(subj, value=True, disabled=True, key=f"fixed_{subj}")

    st.subheader("학생 선택 과목")
    st.caption("과목을 체크하면 분반 알파벳(A~Z)을 선택하는 칸이 나타납니다.")

    selected_electives = []  # (base, letter)

    for theme, subjects in ELECTIVE_THEMES.items():
        with st.expander(theme, expanded=True):
            for subj in subjects:
                col_chk, col_letter = st.columns([3, 1])
                default_checked = subj in existing_elective_map
                checked = col_chk.checkbox(subj, value=default_checked, key=f"elec_chk_{subj}")
                if checked:
                    default_letter = existing_elective_map.get(subj, "A")
                    default_idx = ALPHABET.index(default_letter) if default_letter in ALPHABET else 0
                    letter = col_letter.selectbox(
                        "분반", ALPHABET, index=default_idx,
                        key=f"elec_letter_{subj}", label_visibility="collapsed",
                    )
                    selected_electives.append((subj, letter))

    st.divider()

    col1, col2 = st.columns([1, 1])
    save_clicked = col1.button("💾 저장하고 계속하기", type="primary", use_container_width=True)
    if is_editing:
        cancel_clicked = col2.button("취소하고 돌아가기", use_container_width=True)
    else:
        cancel_clicked = False

    if save_clicked:
        final_subjects = list(FIXED_SUBJECTS) + [f"{base}{letter}" for base, letter in selected_electives]
        students[student_id] = final_subjects
        save_json(STUDENTS_PATH, students)
        st.session_state.page = "main"
        st.success("저장되었습니다!")
        st.rerun()

    if cancel_clicked:
        st.session_state.page = "main"
        st.rerun()


# ------------------------------------------------------------------
# 페이지 3. 메인 (사이드바 + 수행평가 추가 + 달력)
# ------------------------------------------------------------------
def render_sidebar(student_id, students):
    with st.sidebar:
        st.markdown(f"## 🎓 학번 {student_id}")
        if st.button("🔓 다른 학번으로 로그인", use_container_width=True):
            for k in ["student_id", "page", "cal_year", "cal_month", "show_add_form", "selected_detail"]:
                st.session_state.pop(k, None)
            init_session_state()
            st.rerun()

        st.divider()
        st.markdown("### 📖 수강 과목")
        subjects = students.get(student_id, [])
        fixed = [s for s in subjects if s in FIXED_SUBJECTS]
        electives = [s for s in subjects if s not in FIXED_SUBJECTS]

        st.caption("학교 지정")
        for s in fixed:
            st.write(f"• {s}")
        st.caption("선택 과목")
        for s in electives:
            st.write(f"• {s}")

        st.divider()
        if st.button("✏️ 과목 수정", use_container_width=True):
            st.session_state.page = "select_subjects"
            st.rerun()


def render_add_assessment_form(student_id, students, assessments):
    subjects = students.get(student_id, [])

    with st.expander("➕ 수행평가 추가", expanded=st.session_state.show_add_form):
        subj = st.selectbox("과목 선택", subjects, key="add_subject_select")
        col_d, col_t = st.columns(2)
        due_date = col_d.date_input("날짜", value=date.today(), key="add_date")
        title = col_t.text_input("제목", placeholder="예: 1차 지필 대비 수행평가", key="add_title")

        if st.button("저장", type="primary", key="add_save_btn"):
            if not title.strip():
                st.warning("제목을 입력해주세요.")
            else:
                assessments.setdefault(subj, [])
                assessments[subj].append({"date": due_date.isoformat(), "title": title.strip()})
                save_json(ASSESSMENTS_PATH, assessments)
                st.session_state.show_add_form = False
                st.success(f"'{subj}' 과목에 수행평가가 추가되었습니다.")
                st.rerun()

        # 해당 과목에 이미 등록된 수행평가 목록 + 삭제 기능
        if subj and assessments.get(subj):
            st.caption(f"'{subj}' 과목의 등록된 수행평가")
            items = sorted(assessments[subj], key=lambda x: x["date"])
            for idx, item in enumerate(items):
                c1, c2 = st.columns([5, 1])
                c1.write(f"{item['date']} — {item['title']}")
                if c2.button("삭제", key=f"del_{subj}_{idx}"):
                    assessments[subj].remove(item)
                    save_json(ASSESSMENTS_PATH, assessments)
                    st.rerun()


def get_assessments_for_day(student_subjects, assessments, day_iso):
    result = []
    for subj in student_subjects:
        for item in assessments.get(subj, []):
            if item["date"] == day_iso:
                result.append((subj, item["title"]))
    return result


def render_calendar(student_id, students, assessments):
    student_subjects = students.get(student_id, [])
    year = st.session_state.cal_year
    month = st.session_state.cal_month
    today = date.today()

    col_prev, col_title, col_next = st.columns([1, 4, 1])
    if col_prev.button("◀", use_container_width=True):
        if month == 1:
            st.session_state.cal_year -= 1
            st.session_state.cal_month = 12
        else:
            st.session_state.cal_month -= 1
        st.rerun()
    col_title.markdown(f"<h3 style='text-align:center'>{year}년 {month}월</h3>", unsafe_allow_html=True)
    if col_next.button("▶", use_container_width=True):
        if month == 12:
            st.session_state.cal_year += 1
            st.session_state.cal_month = 1
        else:
            st.session_state.cal_month += 1
        st.rerun()

    # 요일 헤더 (일요일 시작)
    header_cols = st.columns(7)
    for i, wd in enumerate(WEEKDAY_NAMES):
        color = "red" if i == 0 else ("blue" if i == 6 else "black")
        header_cols[i].markdown(f"<div style='text-align:center;color:{color};font-weight:bold'>{wd}</div>", unsafe_allow_html=True)

    cal_obj = calendar.Calendar(firstweekday=6)  # 일요일 시작
    weeks = cal_obj.monthdayscalendar(year, month)

    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                    continue
                day_date = date(year, month, day)
                is_today = day_date == today
                day_color = "red" if i == 0 else ("blue" if i == 6 else "black")
                bg = "background-color:#FFF3B0;border-radius:6px;" if is_today else ""
                st.markdown(
                    f"<div style='{bg}padding:2px;min-height:70px'>"
                    f"<span style='color:{day_color};font-weight:{'bold' if is_today else 'normal'}'>{day}</span></div>",
                    unsafe_allow_html=True,
                )
                day_items = get_assessments_for_day(student_subjects, assessments, day_date.isoformat())
                for idx, (subj, title) in enumerate(day_items):
                    if st.button(subj, key=f"day_{day_date.isoformat()}_{idx}", use_container_width=True):
                        st.session_state.selected_detail = (day_date.isoformat(), subj, title)

    # 선택된 수행평가 상세 표시
    if st.session_state.selected_detail:
        d, subj, title = st.session_state.selected_detail
        st.info(f"📌 **{d}** · **{subj}**\n\n{title}")


def render_main():
    student_id = st.session_state.student_id
    students = get_students()
    assessments = get_assessments()

    if student_id not in students:
        st.session_state.page = "select_subjects"
        st.rerun()
        return

    render_sidebar(student_id, students)

    st.title("📅 수행평가 알림장")

    if st.button("➕ 수행평가 추가" if not st.session_state.show_add_form else "➖ 접기"):
        st.session_state.show_add_form = not st.session_state.show_add_form
        st.rerun()

    if st.session_state.show_add_form:
        render_add_assessment_form(student_id, students, assessments)

    st.divider()
    render_calendar(student_id, students, assessments)


# ------------------------------------------------------------------
# 라우터
# ------------------------------------------------------------------
def main():
    init_data_files()
    init_session_state()

    page = st.session_state.page
    if page == "login":
        render_login()
    elif page == "select_subjects":
        render_select_subjects()
    else:
        render_main()


if __name__ == "__main__":
    main()
