import streamlit as st
import pandas as pd
import random
import re
import time

# 페이지 설정
st.set_page_config(page_title="😁엘린이의 단어 시험❤️", layout="centered")

# 스타일 적용: 입력창 폰트 크기 키우기
st.markdown("""
    <style>
    .stTextInput input {
        font-size: 28px !important;
        padding: 15px !important;
        line-height: 1.5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------ 세션 상태 초기화 ------------------
if 'quiz_state' not in st.session_state:
    st.session_state.quiz_state = 'setup'
if 'current_q_idx' not in st.session_state:
    st.session_state.current_q_idx = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'incorrect_questions' not in st.session_state:
    st.session_state.incorrect_questions = [] 
if 'feedback_msg' not in st.session_state:
    st.session_state.feedback_msg = None 
if 'input_value' not in st.session_state:
    st.session_state.input_value = "" 

# ------------------ 함수 정의 ------------------

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"CSV 파일을 읽을 수 없습니다: {e}")
        return pd.DataFrame()

def submit_answer():
    idx = st.session_state.current_q_idx
    q_data = st.session_state.quiz_data[idx]
    user_input = st.session_state.input_value.strip()
    
    # 정답 비교
    if user_input.lower() == q_data['answer'].lower():
        st.session_state.score += 1
        st.session_state.feedback_msg = ("correct", f"⭕ 정답입니다! ({q_data['answer']})")
    else:
        st.session_state.feedback_msg = ("wrong", f"❌ 틀렸습니다! 정답은 **{q_data['answer']}** 였습니다.")
        # 틀린 문제를 목록에 추가
        st.session_state.incorrect_questions.append(q_data)
    
    st.session_state.current_q_idx += 1
    st.session_state.input_value = ""

# ------------------ 메인 UI ------------------

st.title("😁엘린이의 단어 시험❤️")

df = load_data("vocab.csv")
if df.empty:
    st.stop()

# [State 1] 설정 화면
if st.session_state.quiz_state == 'setup':
    st.subheader("시험 범위를 선택하세요")
    
    # A열(Lesson) 기준으로 리스트 만들기
    if len(df.columns) > 0:
        lesson_col = df.columns[0]
        lesson_list = sorted(df[lesson_col].astype(str).unique())
        selected_lesson = st.selectbox("Lesson 선택", lesson_list)
    else:
        st.error("CSV 파일에 데이터가 없습니다.")
        st.stop()
    
    if st.button("시험 시작하기 (Start)", use_container_width=True):
        lesson_df = df[df[lesson_col].astype(str) == selected_lesson]
        
        if lesson_df.empty:
            st.error("선택한 레슨에 단어가 없습니다.")
        else:
            quiz_list = []
            is_wordly = selected_lesson.strip().lower().startswith("wordly")

            for _, row in lesson_df.iterrows():
                # [핵심 수정] 이름(Header) 대신 엑셀의 열 순서(인덱스)로 강제 지정해서 가져오기
                # C열(2)=단어, D열(3)=품사, E열(4)=뜻, F열(5)=예문
                word = str(row.iloc[2]).replace('nan', '').strip() if len(row) > 2 else ''
                part = str(row.iloc[3]).replace('nan', '').strip() if len(row) > 3 else ''
                meaning = str(row.iloc[4]).replace('nan', '').strip() if len(row) > 4 else ''
                example = str(row.iloc[5]).replace('nan', '').strip() if len(row) > 5 else ''

                # 단어가 비어있으면 건너뛰기
                if not word:
                    continue

                # Type A (뜻 문제)
                if meaning:
                    fmt_mean = meaning.replace('\r\n', '<br>').replace('\n', '<br>')
                    fmt_mean = re.sub(r'\s+(?=\d+\.\s|(?:n|v|adj|adv|prep|conj|pron|phrase)\.\s)', '<br>', fmt_mean)
                    if fmt_mean.startswith('<br>'): fmt_mean = fmt_mean[4:]
                    
                    quiz_list.append({
                        'type': 'A',
                        'question': fmt_mean, 
                        'answer': word,
                        'hint': part, 
                        'display_hint': "뜻을 보고 단어를 쓰세요"
                    })
                
                # Type B (예문 문제) - Wordly 제외
                if example and not is_wordly:
                    target = word
                    pattern = re.compile(re.escape(target), re.IGNORECASE)
                    hidden_ex = pattern.sub("______", example)
                    
                    fmt_ex = hidden_ex.replace('\r\n', '<br>').replace('\n', '<br>')
                    fmt_ex = re.sub(r'\s+(?=\d+\.\s|(?:n|v|adj|adv|prep|conj|pron|phrase)\.\s)', '<br><br>', fmt_ex)
                    if fmt_ex.startswith('<br><br>'): fmt_ex = fmt_ex[8:]
                    
                    quiz_list.append({
                        'type': 'B',
                        'question': fmt_ex,
                        'answer': target,
                        'hint': part,
                        'display_hint': "빈칸에 알맞은 단어를 쓰세요"
                    })
            
            if not quiz_list:
                st.error("문제를 생성할 수 없습니다. 데이터가 있는지 확인해주세요.")
            else:
                random.shuffle(quiz_list)
                st.session_state.quiz_data = quiz_list
                st.session_state.total_q = len(quiz_list)
                st.session_state.current_q_idx = 0
                st.session_state.score = 0
                st.session_state.incorrect_questions = [] 
                st.session_state.feedback_msg = None
                st.session_state.quiz_state = 'quiz'
                st.rerun()

# [State 2] 퀴즈 진행
elif st.session_state.quiz_state == 'quiz':
    current_idx = st.session_state.current_q_idx
    total_q = st.session_state.total_q
    
    if current_idx >= total_q:
        st.session_state.quiz_state = 'result'
        st.rerun()

    if st.session_state.feedback_msg:
        msg_type, msg_text = st.session_state.feedback_msg
        if msg_type == "correct":
            st.success(msg_text)
        else:
            st.error(msg_text)
    else:
        st.info("준비되면 아래 빈칸에 정답을 쓰고 Enter를 치세요!")

    q_data = st.session_state.quiz_data[current_idx]
    
    st.markdown(f"### Q{current_idx + 1}. {q_data['display_hint']}")
    
    display_question = q_data['question']
    hint_html = ""
    if q_data['hint']: 
        hint_html = f'<br><br><span style="color:blue; font-size:16px;">(힌트: {q_data["hint"]})</span>'

    st.markdown(f"""
        <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; font-size:20px; margin-bottom:20px; line-height: 1.6;">
            <b>{display_question}</b>
            {hint_html}
        </div>
    """, unsafe_allow_html=True)
    
    st.text_input(
        label="정답 입력",
        key="input_value",
        on_change=submit_answer,
        label_visibility="collapsed",
        placeholder="여기에 정답을 입력하세요"
    )
    
    st.progress((current_idx) / total_q)

# [State 3] 결과
elif st.session_state.quiz_state == 'result':
    
    if st.session_state.feedback_msg:
        msg_type, msg_text = st.session_state.feedback_msg
        st.markdown("### 마지막 문제 결과:")
        if msg_type == "correct":
            st.success(msg_text)
        else:
            st.error(msg_text)
        st.markdown("---")

    st.balloons()
    st.title("🎉 시험 종료!")
    
    score = st.session_state.score
    total = st.session_state.total_q
    incorrect_count = len(st.session_state.incorrect_questions)
    
    st.metric(label="최종 점수", value=f"{score}점", delta=f"{total}문제 중 {score}개 정답")
    
    if score == total:
        st.success("완벽해요! 엘린이 최고! 💯")
    else:
        if score >= total * 0.8:
            st.info("아주 잘했어요! 틀린 것만 다시 해볼까요? 🌟")
        else:
            st.warning("수고했어요! 틀린 문제를 복습해봐요! 💪")

    st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        if incorrect_count > 0:
            if st.button(f"틀린 문제만 다시 풀기 ({incorrect_count}개)", type="primary", use_container_width=True):
                st.session_state.quiz_data = st.session_state.incorrect_questions.copy()
                random.shuffle(st.session_state.quiz_data)
                st.session_state.incorrect_questions = [] 
                st.session_state.total_q = len(st.session_state.quiz_data)
                st.session_state.current_q_idx = 0
                st.session_state.score = 0
                st.session_state.feedback_msg = None
                st.session_state.quiz_state = 'quiz'
                st.rerun()
        else:
            st.write("틀린 문제가 없습니다! 👍")

    with col2:
        if st.button("처음으로 (레슨 선택)", use_container_width=True):
            st.session_state.quiz_state = 'setup'
            st.session_state.score = 0
            st.session_state.current_q_idx = 0
            st.session_state.incorrect_questions = []
            st.session_state.feedback_msg = None
            st.rerun()