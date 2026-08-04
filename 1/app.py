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

if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "edit_subject_mode" not in st.session_state:
    st.session_state.edit_subject_mode = False
if "cal_year" not in st.session_state:
    st.session_state.cal_year = datetime.now().year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = datetime.now().month

# ---------------------------------------------------------
# 2. 과목 데이터 정의 ((일반) 제거 및 고전 읽기 반영)
# ---------------------------------------------------------
FIXED_SUBJECTS = ["독서", "영어2", "심화 영어1", "운동과 건강"]

SELECT_SUBJECTS = {
    "기초": [
        "확률과 통계", "심화 수학1", "화법과 작문", "고전 읽기", 
        "미적분", "경제 수학", "심화 영어 독해1", "영어권 문화"
    ],
    "탐구": [
        "한국지리", "동아시아사", "사회문화", "윤리와 사상", 
        "고전과 윤리", "지역 이해", "물리학2", "화학2", "생명과학2", "지구과학2", "생활과 과학"
    ],
    "예술, 교양": [
        "미술사", "현대문학 감상", "데이터 과학과 머신러닝", 
        "철학", "보건", "환경", "논술", "심리학"
    ]
}

ALPHABET_LIST = [chr(i) for i in range(ord('A'), ord('Z') + 1)]

# ---------------------------------------------------------
# 3. 로그인 화면 (숫자 5자리 검증)
# ---------------------------------------------------------
if not st.session_state.student_id:
    st.title("학교 수행평가 알림앱")
    
    input_id = st.text_input("학번을 입력하세요 (예: 30101)", max_chars=5)
    
    if st.button("로그인", type="primary"):
        clean_id = input_id.strip()
        if clean_id.isdigit() and len(clean_id) == 5:
            st.session_state.student_id = clean_id
            st.rerun()
        else:
            st.error("학번은 숫자로 된 5자리여야 합니다.")
    st.stop()

# ---------------------------------------------------------
# 4. 수강 과목 설정 화면 (최초 로그인 또는 수정 시)
# ---------------------------------------------------------
students_data = load_json(STUDENTS_FILE)
current_id = st.session_state.student_id

if current_id not in students_data or st.session_state.edit_subject_mode:
    st.title(f"[{current_id}] 수강 과목 선택")
    
    st.markdown("### 학교 지정 과목")
    for sub in FIXED_SUBJECTS:
        st.checkbox(sub, value=True, disabled=True, key=f"fixed_{sub}")
        
    st.markdown("---")
    st.markdown("### 학생 선택 과목")
    st.caption("과목을 선택한 후 분반 알파벳(A~Z)을 지정해주세요.")
    
    existing_user_data = students_data.get(current_id, {})
    existing_user_selects = existing_user_data.get("selected_subjects", {})
    
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

    if st.button("저장하고 이동", type="primary"):
        students_data[current_id] = {
            "fixed_subjects": FIXED_SUBJECTS,
            "selected_subjects": selected_result
        }
        save_json(STUDENTS_FILE, students_data)
        st.session_state.edit_subject_mode = False
        st.rerun()
        
    st.stop()

# ---------------------------------------------------------
# 5. 메인 화면 (사이드바 고정 + 수행평가 추가 + 달력)
# ---------------------------------------------------------
user_info = students_data[current_id]
user_fixed = user_info.get("fixed_subjects", [])
user_selected = user_info.get("selected_subjects", {})

my_subject_list = list(user_fixed) + [f"{sub}{letter}" for sub, letter in user_selected.items()]

# [사이드바 UI 구성 - 고정 노출]
with st.sidebar:
    st.markdown("## 수행평가 일정")
    st.markdown(f"### {current_id}")
    st.markdown("---")
    st.markdown("#### 수강과목")
    for s in my_subject_list:
        st.write(f"- {s}")
        
    st.markdown("---")
    if st.button("과목 수정"):
        st.session_state.edit_subject_mode = True
        st.rerun()
        
    if st.button("다른학번으로 로그인"):
        st.session_state.student_id = None
        st.session_state.edit_subject_mode = False
        st.rerun()

# [메인 화면]
evaluations_data = load_json(EVALUATIONS_FILE)

# 1. 수행평가 추가 구역
with st.expander("수행평가 추가", expanded=False):
    with st.form("add_evaluation_form"):
        selected_sub_for_eval = st.selectbox("과목 선택", my_subject_list)
        eval_date = st.date_input("날짜 선택", value=date.today(), format="MM/DD")
        eval_title = st.text_input("제목 입력")
        
        submit_btn = st.form_submit_button("등록")
        
        if submit_btn:
            if not eval_title.strip():
                st.error("제목을 입력해주세요.")
            else:
                date_str = eval_date.strftime("%Y-%m-%d")
                
                if date_str not in evaluations_data:
                    evaluations_data[date_str] = []
                
                evaluations_data[date_str].append({
                    "subject": selected_sub_for_eval,
                    "title": eval_title.strip()
                })
                
                save_json(EVALUATIONS_FILE, evaluations_data)
                st.success("등록되었습니다.")
                st.rerun()

# 2. 월 선택 컨트롤 (연도 제거, 월 표기)
col_prev, col_title, col_next = st.columns([1, 4, 1])
with col_prev:
    if st.button("이전 달"):
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1
        st.rerun()

with col_next:
    if st.button("다음 달"):
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1
        st.rerun()

with col_title:
    st.markdown(
        f"<h3 style='text-align: center;'>{st.session_state.cal_month}월</h3>", 
        unsafe_allow_html=True
    )

# 3. 달력 그리드 렌더링 (높이 고정 & Tooltip 적용)
year = st.session_state.cal_year
month = st.session_state.cal_month
today_str = date.today().strftime("%Y-%m-%d")

days_of_week = ["월", "화", "수", "목", "금", "토", "일"]
cols = st.columns(7)
for idx, day in enumerate(days_of_week):
    cols[idx].markdown(f"**<div style='text-align: center;'>{day}</div>**", unsafe_allow_html=True)

month_calendar = calendar.monthcalendar(year, month)

for week in month_calendar:
    cols = st.columns(7)
    for idx, day in enumerate(week):
        with cols[idx]:
            if day == 0:
                st.write("")
            else:
                curr_date_str = f"{year}-{month:02d}-{day:02d}"
                is_today = (curr_date_str == today_str)
                
                border_style = "border: 2px solid #3366ff;" if is_today else "border: 1px solid #ddd;"
                bg_style = "background-color: #f8f9fa;" if is_today else "background-color: #ffffff;"
                
                # 일별 영역 HTML 생성 (최소 높이 130px로 설정)
                eval_html_items = ""
                if curr_date_str in evaluations_data:
                    for item in evaluations_data[curr_date_str]:
                        if item["subject"] in my_subject_list:
                            # 과목명 옆 i 아이콘 호버 시 제목 표시
                            eval_html_items += f"""
                            <div style="font-size: 11px; margin-top: 3px; background-color: #eee; padding: 2px 4px; border-radius: 3px; display: flex; justify-content: space-between; align-items: center;">
                                <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 80px;">{item['subject']}</span>
                                <span title="{item['title']}" style="cursor: pointer; font-weight: bold; color: #555; margin-left: 2px; padding: 0 3px; background-color: #ddd; border-radius: 50%; font-size: 10px;">i</span>
                            </div>
                            """
                
                cell_html = f"""
                <div style="{border_style} {bg_style} padding: 4px; border-radius: 5px; min-height: 130px; box-sizing: border-box;">
                    <div style="font-size: 12px; font-weight: bold;">{day}</div>
                    {eval_html_items}
                </div>
                """
                st.markdown(cell_html, unsafe_allow_html=True)
                st.write(f"**날짜:** {curr_date_str}")
                st.write(f"**과목:** {item['subject']}")
                st.write(f"**수행평가 내용:** {item['title']}")
                show_detail()
