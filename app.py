import streamlit as st
import pandas as pd
import random
from hanja_list import hanja_data # hanja_list.py에서 데이터 임포트

# --- 데이터 로딩 및 전처리 함수 ---
@st.cache_data
def load_hanja_data_from_list(data_list):
    """
    파이썬 리스트에서 한자 데이터를 DataFrame으로 변환합니다.
    """
    if not data_list:
        return pd.DataFrame()
    return pd.DataFrame(data_list)

# --- Streamlit 앱 UI 구성 ---
st.set_page_config(page_title="한자 암기 프로그램", layout="wide")
st.title("한자 암기 프로그램")

# --- 데이터 로드 ---
df_all = load_hanja_data_from_list(hanja_data)

if df_all.empty:
    st.error("한자 데이터를 불러오지 못했습니다. `hanja_list.py` 파일의 내용을 확인해주세요.")
else:
    # --- 사이드바 UI --- 
    with st.sidebar:
        st.header("메뉴")
        menu_choice = st.radio(
            "학습 메뉴를 선택하세요",
            ["한자 보고 뜻/음 맞추기", "뜻/음 보고 한자 맞추기", "단어집 목록"],
            key="main_menu"
        )

        st.header("한자 분류")
        category_choice = st.radio(
            "분류를 선택하세요",
            ["전체", "중학교용", "고등학교용"],
            key="category_choice",
            on_change=lambda: st.session_state.update(quiz_idx=0, options=[]) # 필터 변경 시 퀴즈 리셋
        )

    # --- 데이터 필터링 ---
    if category_choice == "전체":
        df = df_all
    else:
        df = df_all[df_all["category"] == category_choice].reset_index(drop=True)

    if "quiz_idx" not in st.session_state:
        st.session_state.quiz_idx = 0
    if "options" not in st.session_state:
        st.session_state.options = []

    if df.empty:
        st.warning("선택된 분류에 해당하는 한자가 없습니다.")
    else:
        # --- 메인 화면 --- 
        if menu_choice == "단어집 목록":
            st.header(f"📖 {category_choice} 한자 목록")
            st.dataframe(df, height=600, use_container_width=True)

        elif menu_choice == "한자 보고 뜻/음 맞추기":
            st.header("📖 한자 보고 뜻과 음 맞추기")
            
            if st.session_state.quiz_idx >= len(df):
                st.session_state.quiz_idx = 0

            current_hanja = df.iloc[st.session_state.quiz_idx]
            
            st.markdown(f"<div style=\'text-align: center; font-size: 120px; margin: 20px;\'>{current_hanja["hanja"]}</div>", unsafe_allow_html=True)
            
            with st.form(key="hanja_quiz_form"):
                col1, col2 = st.columns(2)
                with col1:
                    meaning_input = st.text_input("뜻을 입력하세요:")
                with col2:
                    sound_input = st.text_input("음을 입력하세요:")
                
                submitted = st.form_submit_button("정답 확인")

                if submitted:
                    is_meaning_correct = (meaning_input.strip() == current_hanja["meaning"])
                    is_sound_correct = (sound_input.strip() == current_hanja["sound"])

                    if is_meaning_correct and is_sound_correct:
                        st.success("🎉 정답입니다!")
                    else:
                        feedback = f"🤔 오답입니다. 정답: **{current_hanja["meaning"]} {current_hanja["sound"]}**"
                        st.error(feedback)

            if st.button("다음 문제"):
                st.session_state.quiz_idx = random.randint(0, len(df) - 1)
                st.rerun()

        elif menu_choice == "뜻/음 보고 한자 맞추기":
            st.header("✍️ 뜻과 음 보고 한자 맞추기")

            def generate_quiz():
                if len(df) < 5:
                    st.warning("퀴즈를 출제하기에 한자 개수가 부족합니다. (최소 5개 필요)")
                    return
                
                correct_idx = random.randint(0, len(df) - 1)
                st.session_state.quiz_idx = correct_idx
                correct_answer = df.iloc[correct_idx]

                wrong_answers_df = df.drop(index=correct_idx).sample(4)
                
                options_df = pd.concat([pd.DataFrame([correct_answer]), wrong_answers_df])
                options = options_df["hanja"].tolist()
                random.shuffle(options)
                st.session_state.options = options

            if not st.session_state.options or st.session_state.quiz_idx >= len(df):
                generate_quiz()
            
            if st.session_state.options:
                current_hanja = df.iloc[st.session_state.quiz_idx]

                st.markdown(f"<h2 style=\'text-align: center; margin: 20px;\'>{current_hanja["meaning"]} {current_hanja["sound"]}</h2>", unsafe_allow_html=True)
                
                cols = st.columns(5)
                for i, option in enumerate(st.session_state.options):
                    if cols[i].button(option, key=f"option_{i}", use_container_width=True):
                        if option == current_hanja["hanja"]:
                            st.success("🎉 정답입니다! 다음 문제로 넘어갑니다.")
                            with st.spinner(\'새로운 문제를 불러오는 중...\'):
                                generate_quiz()
                            st.rerun()
                        else:
                            st.error(f"🤔 틀렸습니다. 정답은 \'{current_hanja["hanja"]}\' 입니다.")
                
                st.divider()
                if st.button("다른 문제로 변경"):
                    generate_quiz()
                    st.rerun()


