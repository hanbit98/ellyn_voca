import streamlit as st
import pandas as pd
import random
import re
import time

# 페이지 설정 (가장 윗부분에 있어야 함)
st.set_page_config(page_title="둘째의 단어 시험", layout="centered")

# ------------------ 세션 상태 초기화 ------------------
if 'quiz_state' not in st.session_state:
    st.session_state.quiz_state = 'setup'  # setup, quiz, result
if 'current_q_idx' not in st.session_state:
    st.session_state.current_q_idx = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'feedback_msg' not in st.session_state:
    st.session_state.feedback_msg = None # 정답/오답 메시지 저장용
if 'input_value' not in st.session_state:
    st.session_state.input_value = "" # 입력창 값 제어용

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

# 정답 제출 시 실행될 콜백 함수
def submit_answer():
    # 현재 문제 정보 가져오기
    idx = st.session_state.current_q_idx
    q_data = st.session_state.quiz_data[idx]
    
    # 사용자 입력값 (앞뒤 공백 제거)
    user_input = st.session_state.input_value.strip()
    
    # 정답 비교
    if user_input.lower() == q_data['answer'].lower():
        st.session_state.score += 1
        st.session_state.feedback_msg = ("correct", f"⭕ 정답입니다! ({q_data['answer']})")
    else:
        st.session_state.feedback_msg = ("wrong", f"❌ 틀렸습니다! 정답은 **{q_data['answer']}** 였습니다.")
    
    # 다음 문제로 인덱스 증가
    st.session_state.current_q_idx += 1
    
    # 입력창 비우기 (다음 입력을 위해)
    st.session_state.input_value = ""

# ------------------ 메인 UI ------------------

st.title("📝 둘째의 단어 시험")

# 데이터 로드
df = load_data("vocab.csv")
if df.empty:
    st.stop()

# [State 1] 시험 범위 선택 화면
if st.session_state.quiz_state == 'setup':
    st.subheader("시험 범위를 선택하세요")
    lesson_list = sorted(df['Lesson'].unique())
    selected_lesson = st.selectbox("Lesson 선택", lesson_list)
    
    # 버튼도 엔터로 넘어가게 하고 싶지만, selectbox 때문에 버튼 클릭 필요
    if st.button("시험 시작하기 (Start)", use_container_width=True):
        lesson_df = df[df['Lesson'] == selected_lesson]
        
        if lesson_df.empty:
            st.error("단어가 없습니다.")
        else:
            # 문제 생성
            quiz_list = []
            for _, row in lesson_df.iterrows():
                # Type A (뜻)
                quiz_list.append({
                    'type': 'A',
                    'question': row['Meaning'],
                    'answer': row['Word'].strip(),
                    'hint': row['Part'],
                    'display_hint': "뜻을 보고 단어를 쓰세요"
                })
                # Type B (예문)
                target = row['Word'].strip()
                pattern = re.compile(re.escape(target), re.IGNORECASE)
                hidden_ex = pattern.sub("______", row['Example'])
                quiz_list.append({
                    'type': 'B',
                    'question': hidden_ex,
                    'answer': target,
                    'hint': row['Part'],
                    'display_hint': "빈칸에 알맞은 단어를 쓰세요"
                })
            
            random.shuffle(quiz_list)
            st.session_state.quiz_data = quiz_list
            st.session_state.total_q = len(quiz_list)
            st.session_state.current_q_idx = 0
            st.session_state.score = 0
            st.session_state.feedback_msg = None
            st.session_state.quiz_state = 'quiz'
            st.rerun()

# [State 2] 퀴즈 진행 화면
elif st.session_state.quiz_state == 'quiz':
    
    # 1. 진행 상황 체크
    current_idx = st.session_state.current_q_idx
    total_q = st.session_state.total_q
    
    # 2. 모든 문제 종료 시 결과 화면으로
    if current_idx >= total_q:
        st.session_state.quiz_state = 'result'
        st.rerun()

    # 3. 이전 문제 결과 피드백 표시 (화면 상단)
    # 다음 문제가 나와도 이전 문제의 결과를 위에 보여줍니다.
    if st.session_state.feedback_msg:
        msg_type, msg_text = st.session_state.feedback_msg
        if msg_type == "correct":
            st.success(msg_text)
        else:
            st.error(msg_text)
    else:
        st.info("준비되면 아래 빈칸에 정답을 쓰고 Enter를 치세요!")

    # 4. 현재 문제 표시
    q_data = st.session_state.quiz_data[current_idx]
    
    st.markdown(f"### Q{current_idx + 1}. {q_data['display_hint']}")
    
    # 문제 박스 (가독성을 위해 스타일링)
    st.markdown(f"""
        <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; font-size:20px; margin-bottom:20px;">
            <b>{q_data['question']}</b>
            <br><span style="color:blue; font-size:16px;">(힌트: {q_data['hint']})</span>
        </div>
    """, unsafe_allow_html=True)
    
    # 5. 입력창 (가장 중요: on_change 사용)
    # key='input_value'를 통해 세션 변수와 연결
    # on_change=submit_answer를 통해 엔터를 치면 submit_answer 함수가 실행됨
    st.text_input(
        label="정답 입력",
        key="input_value",
        on_change=submit_answer,
        label_visibility="collapsed",
        placeholder="여기에 정답을 쓰고 Enter를 누르세요"
    )
    
    # 진행률 바
    st.progress((current_idx) / total_q)

# [State 3] 결과 화면
elif st.session_state.quiz_state == 'result':
    st.balloons()
    st.title("🎉 시험 종료!")
    
    score = st.session_state.score
    total = st.session_state.total_q
    
    # 점수 표시
    st.metric(label="최종 점수", value=f"{score}점", delta=f"{total}문제 중 {score}개 정답")
    
    if score == total:
        st.success("완벽해요! 💯")
    elif score >= total * 0.8:
        st.info("아주 잘했어요! 🌟")
    else:
        st.warning("조금 더 연습해봐요! 💪")

    # 다시 하기 버튼
    if st.button("처음으로 돌아가기"):
        st.session_state.quiz_state = 'setup'
        st.session_state.score = 0
        st.session_state.current_q_idx = 0
        st.session_state.feedback_msg = None
        st.rerun()