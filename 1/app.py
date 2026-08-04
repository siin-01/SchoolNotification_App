import streamlit as st
import json
import os
from datetime import datetime, date
import calendar

# ---------------------------------------------------------
# 1. 데이터 파일 및 세션 초기화
# ---------------------------------------------------------
STUDENTS_FILE = "students_data.json"
EVALUATIONS_FILE = "evaluations_data.json"

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 앱 실행 시 세션 상태 초기화
if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "edit_subject_mode" not in st.session_state:
    st.session_state.edit_subject_mode = False
if "cal_year" not in st.session_state:
    st.session_state.cal_year = datetime.now().year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = datetime.now().month

# ---------------------------------------------------------
# 2. 과목 데이터 정의 (2026년 고3)
# ---------------------------------------------------------
FIXED_SUBJECTS = ["독서(일반)", "영어2(일반)", "심화 영어1(일반)", "운동과 건강"]

SELECT_SUBJECTS = {
    "기초": [
        "확률과 통계(일반)", "심화 수학1", "화법과 작문", "읽기", 
        "미적분(일반)", "경제 수학", "심화 영어 독해1", "영어권 문화"
    ],
    "탐구": [
        "한국지리(일반)", "동아시아사(일반)", "사회문화(일반)", "윤리와 사상(일반)", 
        "고전과 윤리", "지역 이해", "물리학2", "화학2", "생명과학2", "지구과학2", "생활과 과학"
    ],
    "예술, 교양": [
        "미술사", "현대문학 감상", "데이터 과학과 머신러닝", 
        "철학", "보건", "환경", "논술", "심리학"
    ]
}

ALPHABET_LIST = [chr(i) for i in range(ord('A'), ord('Z') + 1)]

# ---------------------------------------------------------
# 3. 학번 입력 화면 (초기 접속)
# ---------------------------------------------------------
if not st.session_state.student_id:
    st.title("🏫 학교 수행평가 알림앱")
    st.subheader("학번 입력")
    
    input_id = st.text_input("학번을 입력하세요 (예: 31111)", max_chars=10)
    if st.button("접속하기", type="primary"):
        if input_id.strip():
            st.session_state.student_id = input_id.strip()
            st.rerun()
        else:
            st.warning("학번을 올바르게 입력해주세요.")
    st.stop()

# ---------------------------------------------------------
# 4. 학번 기반 과목 설정 화면 (최초 1회 또는 수정 시)
# ---------------------------------------------------------
students_data = load_json(STUDENTS_FILE)
current_id = st.session_state.student_id

# 수강 정보가 없거나 수정 모드인 경우
if current_id not in students_data or st.session_state.edit_subject_mode:
    st.title(f"⚙️ [{current_id}] 수강 과목 선택")
    st.caption("2026학년도 고등학교 3학년 대상 지정 및 선택 과목 설정")
    
    st.markdown("### 📌 학교 지정 과목 (자동 선택)")
    for sub in FIXED_SUBJECTS:
        st.checkbox(sub, value=True, disabled=True, key=f"fixed_{sub}")
        
    st.markdown("---")
    st.markdown("### ✏️ 학생 선택 과목")
    st.info("과목을 체크한 후 분반 알파벳(A~Z)을 지정해주세요.")
    
    # 기존 설정 불러오기
    existing_user_data = students_data.get(current_id, {})
    existing_user_selects = existing_user_data.get("selected_subjects", {}) # {"화학2": "A"}
    
    selected_result = {}
    
    for category, sub_list in SELECT_SUBJECTS.items():
        st.subheader(f"[{category}]")
        for sub in sub_list:
            col1, col2 = st.columns([3, 2])
            is_checked_default = sub in existing_user_selects
            default_letter = existing_user_selects.get(sub, "A")
            
            with col1:
                is_checked = st.checkbox(sub, value=is_checked_default, key=f"check_{sub}")
            with col2:
                letter = st.selectbox(
                    f"{sub} 분반", 
                    ALPHABET_LIST, 
                    index=ALPHABET_LIST.index(default_letter) if default_letter in ALPHABET_LIST else 0,
                    key=f"letter_{sub}",
                    disabled=not is_checked,
                    label_visibility="collapsed"
                )
            
            if is_checked:
                selected_result[sub] = letter

    if st.button("저장하고 저장된 과목으로 이동", type="primary"):
        students_data[current_id] = {
            "fixed_subjects": FIXED_SUBJECTS,
            "selected_subjects": selected_result # {"지구과학2": "A", ...}
        }
        save_json(STUDENTS_FILE, students_data)
        st.session_state.edit_subject_mode = False
        st.success("수강 과목 정보가 저장되었습니다!")
        st.rerun()
        
    st.stop()

# ---------------------------------------------------------
# 5. 메인 화면 (사이드바 + 달력 + 수행평가 관리)
# ---------------------------------------------------------
user_info = students_data[current_id]
user_fixed = user_info.get("fixed_subjects", [])
user_selected = user_info.get("selected_subjects", {})

# 저장된 최종 과목 명칭 리스트 생성 (예: ["독서(일반)", "지구과학2A"])
my_subject_list = list(user_fixed) + [f"{sub}{letter}" for sub, letter in user_selected.items()]

# [사이드바 구성]
with st.sidebar:
    st.markdown(f"## 👤 학번: **{current_id}**")
    st.markdown("---")
    st.markdown("### 📚 현재 수강 과목")
    for s in my_subject_list:
        st.write(f"- {s}")
        
    st.markdown("---")
    if st.button("✏️ 수강 과목 수정"):
        st.session_state.edit_subject_mode = True
        st.rerun()
        
    if st.button("🚪 학번 변경 (로그아웃)"):
        st.session_state.student_id = None
        st.session_state.edit_subject_mode = False
        st.rerun()

# [메인 페이지]
st.title("📅 수행평가 알림 달력")

# 1. 수행평가 추가 구역
with st.expander("➕ 수행평가 추가하기", expanded=False):
    evaluations_data = load_json(EVALUATIONS_FILE)
    
    with st.form("add_evaluation_form"):
        selected_sub_for_eval = st.selectbox("과목 선택", my_subject_list)
        eval_date = st.date_input("수행평가 날짜", value=date.today())
        eval_title = st.text_input("수행평가 제목/내용 (예: 1차 형성평가, 포트폴리오 제출)")
        
        submit_btn = st.form_submit_button("등록하기")
        
        if submit_btn:
            if not eval_title.strip():
                st.error("수행평가 제목을 입력해주세요.")
            else:
                date_str = eval_date.strftime("%Y-%m-%d")
                
                if date_str not in evaluations_data:
                    evaluations_data[date_str] = []
                
                evaluations_data[date_str].append({
                    "subject": selected_sub_for_eval,
                    "title": eval_title.strip()
                })
                
                save_json(EVALUATIONS_FILE, evaluations_data)
                st.success(f"[{selected_sub_for_eval}] {eval_title} 일정이 등록되었습니다!")
                st.rerun()

# 2. 달력 탐색 컨트롤 (월 이동)
evaluations_data = load_json(EVALUATIONS_FILE)

col_prev, col_title, col_next = st.columns([1, 4, 1])
with col_prev:
    if st.button("◀ 이전 달"):
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1
        st.rerun()

with col_next:
    if st.button("다음 달 ▶"):
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1
        st.rerun()

with col_title:
    st.markdown(
        f"<h3 style='text-align: center;'>{st.session_state.cal_year}년 {st.session_state.cal_month}월</h3>", 
        unsafe_allow_html=True
    )

# 3. 큰 달력 그리드 렌더링
year = st.session_state.cal_year
month = st.session_state.cal_month
today_str = date.today().strftime("%Y-%m-%d")

# 요일 헤더
days_of_week = ["월", "화", "수", "목", "금", "토", "일"]
cols = st.columns(7)
for idx, day in enumerate(days_of_week):
    cols[idx].markdown(f"**<div style='text-align: center;'>{day}</div>**", unsafe_allow_html=True)

# 해당 월의 주차별 날짜 가져오기
month_calendar = calendar.monthcalendar(year, month)

for week in month_calendar:
    cols = st.columns(7)
    for idx, day in enumerate(week):
        with cols[idx]:
            if day == 0:
                st.write("") # 빈 날짜
            else:
                curr_date_str = f"{year}-{month:02d}-{day:02d}"
                is_today = (curr_date_str == today_str)
                
                # 오늘 날짜 스타일 지정
                border_style = "border: 2px solid #FF4B4B;" if is_today else "border: 1px solid #ddd;"
                bg_style = "background-color: #f0f2f6;" if is_today else ""
                
                st.markdown(
                    f"<div style='{border_style} {bg_style} padding: 4px; border-radius: 5px; min-height: 80px;'>"
                    f"<b>{day}</b></div>", 
                    unsafe_allow_html=True
                )
                
                # 해당 날짜의 수행평가 일정 불러오기
                if curr_date_str in evaluations_data:
                    day_evals = evaluations_data[curr_date_str]
                    for item_idx, item in enumerate(day_evals):
                        # 본인이 수강하는 과목의 수행평가만 표시
                        if item["subject"] in my_subject_list:
                            btn_label = f"📌 {item['subject']}"
                            # 과목 버튼 클릭 시 수행평가 제목 팝업(dialog)
                            if st.button(btn_label, key=f"btn_{curr_date_str}_{item_idx}"):
                                @st.dialog(f"[{item['subject']}] 수행평가 상세")
                                def show_detail():
                                    st.write(f"**날짜:** {curr_date_str}")
                                    st.write(f"**과목:** {item['subject']}")
                                    st.write(f"**수행평가 내용:** {item['title']}")
                                show_detail()
