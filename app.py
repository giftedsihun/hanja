import streamlit as st
import pandas as pd
import re
import random

# --- 데이터 로딩 및 전처리 함수 ---
@st.cache_data
def load_hanja_data(file_path):
    """
    텍스트 파일에서 한자 데이터를 읽어와 DataFrame으로 변환합니다.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return None

    # 정규 표현식을 사용하여 "한자 (뜻 음)" 형식의 모든 데이터를 찾습니다.
    # 예: 佳 (아름다울 가)
    matches = re.findall(r'(\w)\s*\(([^)]+?)\s+?(\S+?)\)', content)
    
    hanja_list = []
    for match in matches:
        hanja, meaning, sound = match
        hanja_list.append({
            "hanja": hanja.strip(),
            "meaning": meaning.strip(),
            "sound": sound.strip()
        })
        
    if not hanja_list:
        return pd.DataFrame()

    return pd.DataFrame(hanja_list)

# --- Streamlit 앱 UI 구성 ---

# 앱 제목 설정
st.set_page_config(page_title="한자 암기 프로그램", layout="wide")
st.title("한자 암기 프로그램")

# 데이터 로드
df = load_hanja_data('hanja_data.txt')

if df is None:
    st.error("`hanja_data.txt` 파일을 찾을 수 없습니다.")
    st.info("제공된 한자 목록을 복사하여 `hanja_data.txt` 파일을 생성한 후, 이 앱과 같은 폴더에 저장해주세요.")
elif df.empty:
    st.error("한자 데이터를 불러오지 못했습니다. `hanja_data.txt` 파일의 내용을 확인해주세요.")
else:
    # 세션 상태 초기화
    if 'hanja_quiz_idx' not in st.session_state:
        st.session_state.hanja_quiz_idx = random.randint(0, len(df) - 1)
    if 'meaning_quiz_idx' not in st.session_state:
        st.session_state.meaning_quiz_idx = random.randint(0, len(df) - 1)
    if 'meaning_quiz_options' not in st.session_state:
        st.session_state.meaning_quiz_options = []

    # 사이드바 메뉴
    with st.sidebar:
        st.header("메뉴")
        choice = st.radio(
            "학습 메뉴를 선택하세요",
            ["한자 보고 뜻/음 맞추기", "뜻/음 보고 한자 맞추기", "전체 한자 목록"],
            label_visibility="collapsed"
        )
        st.info(f"총 {len(df)}개의 한자가 로드되었습니다.")

    # --- 1. 한자 보고 뜻/음 맞추기 ---
    if choice == "한자 보고 뜻/음 맞추기":
        st.header("📖 한자 보고 뜻과 음 맞추기")
        
        current_hanja = df.iloc[st.session_state.hanja_quiz_idx]
        
        st.markdown(f"<div style='text-align: center; font-size: 120px; margin: 20px;'>{current_hanja['hanja']}</div>", unsafe_allow_html=True)
        
        with st.form(key='hanja_quiz_form'):
            col1, col2 = st.columns(2)
            with col1:
                meaning_input = st.text_input("뜻을 입력하세요:")
            with col2:
                sound_input = st.text_input("음을 입력하세요:")
            
            submitted = st.form_submit_button("정답 확인")

            if submitted:
                correct_meaning = current_hanja['meaning']
                correct_sound = current_hanja['sound']
                
                is_meaning_correct = (meaning_input.strip() == correct_meaning)
                is_sound_correct = (sound_input.strip() == correct_sound)

                if is_meaning_correct and is_sound_correct:
                    st.success("🎉 정답입니다!")
                else:
                    feedback = "🤔 아쉬워요! "
                    if not is_meaning_correct:
                        feedback += f"뜻: **{correct_meaning}** "
                    if not is_sound_correct:
                        feedback += f"음: **{correct_sound}**"
                    st.error(feedback)
                
                st.info(f"정답: **{correct_meaning} {correct_sound}**")

        if st.button("다음 문제"):
            st.session_state.hanja_quiz_idx = random.randint(0, len(df) - 1)
            st.rerun()

    # --- 2. 뜻/음 보고 한자 맞추기 ---
    elif choice == "뜻/음 보고 한자 맞추기":
        st.header("✍️ 뜻과 음 보고 한자 맞추기")

        def generate_meaning_quiz():
            correct_idx = random.randint(0, len(df) - 1)
            st.session_state.meaning_quiz_idx = correct_idx
            correct_answer = df.iloc[correct_idx]

            wrong_answers_df = df.drop(index=correct_idx).sample(4)
            
            options_df = pd.concat([pd.DataFrame([correct_answer]), wrong_answers_df])
            options = options_df['hanja'].tolist()
            random.shuffle(options)
            st.session_state.meaning_quiz_options = options

        if not st.session_state.meaning_quiz_options:
            generate_meaning_quiz()

        current_hanja = df.iloc[st.session_state.meaning_quiz_idx]
        options = st.session_state.meaning_quiz_options

        st.markdown(f"<h2 style='text-align: center; margin: 20px;'>{current_hanja['meaning']} {current_hanja['sound']}</h2>", unsafe_allow_html=True)
        
        cols = st.columns(5)
        for i, option in enumerate(options):
            if cols[i].button(option, key=f"option_{i}", use_container_width=True):
                if option == current_hanja['hanja']:
                    st.success("🎉 정답입니다! 다음 문제로 넘어갑니다.")
                    with st.spinner('새로운 문제를 불러오는 중...'):
                        generate_meaning_quiz()
                    st.rerun()
                else:
                    st.error("🤔 틀렸습니다. 다시 시도해보세요.")
        
        st.divider()
        if st.button("다른 문제로 변경"):
            generate_meaning_quiz()
            st.rerun()

    # --- 3. 전체 한자 목록 ---
    elif choice == "전체 한자 목록":
        st.header("📚 전체 한자 목록")
        st.dataframe(df, height=600, use_container_width=True)


