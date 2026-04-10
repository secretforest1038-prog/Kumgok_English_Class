import streamlit as st
from gtts import gTTS
import easyocr
import numpy as np
from PIL import Image
import io
import json
from streamlit_local_storage import LocalStorage
from datetime import datetime

# 1. 페이지 설정 (사이드바 기본 숨김 처리)
st.set_page_config(
    page_title="중학교 영어 발음 도우미", 
    page_icon="📸", 
    layout="wide",
    initial_sidebar_state="collapsed" # 사이드바를 접힌 상태로 시작
)

# UI 요소 숨기기 CSS
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stApp [data-testid="stToolbar"] {display: none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 2. 로컬 저장소 및 OCR 초기화
local_storage = LocalStorage("english_learner")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])
reader = load_ocr()

# 3. 사이드바 (학습 기록 관리)
with st.sidebar:
    st.header("📚 나의 학습 기록")
    saved_history = local_storage.getItem("study_history")
    history_list = json.loads(saved_history) if saved_history else []

    if history_list:
        # 최신 순서대로 표시
        for i, item in enumerate(reversed(history_list)):
            # item['time']에 저장된 "4/5_1" 형식 표시
            with st.expander(f"📌 {item['time']} 기록"):
                st.write(item['text'])
                if st.button("🔊 다시 듣기", key=f"re_{i}"):
                    st.session_state.input_text = item['text']
                    st.rerun()
        
        st.divider()
        if st.button("🗑️ 전체 기록 삭제"):
            local_storage.removeItem("study_history")
            st.rerun()
    else:
        st.info("왼쪽 화살표를 닫고 학습을 시작하세요!")

# 4. 메인 화면 - 입력부 (순서 조정: 입력 -> 촬영 -> 앨범)
st.title("🏫 English Pronunciation Helper")
input_mode = st.radio("방법 선택:", ["⌨️ 직접 입력", "📷 사진 촬영", "📁 앨범 선택"], horizontal=True)

if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

# 입력 방식별 로직
captured_text = ""
if input_mode == "⌨️ 직접 입력":
    pass # 아래 text_area에서 직접 처리
elif input_mode == "📷 사진 촬영":
    img_src = st.camera_input("문장을 찍으세요")
    if img_src:
        with st.spinner('글자를 읽는 중...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)
elif input_mode == "📁 앨범 선택":
    img_src = st.file_uploader("사진을 선택하세요", type=['jpg','png','jpeg'])
    if img_src:
        with st.spinner('글자를 읽는 중...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)

if captured_text:
    st.session_state.input_text = captured_text

# 5. 메인 화면 - 출력부 (속도 조절 삭제)
final_text = st.text_area("문장 확인 및 수정:", value=st.session_state.input_text, height=150)

if st.button("🔊 발음 듣기", type="primary") and final_text:
    # 음성 생성
    tts = gTTS(text=final_text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    st.audio(fp, format="audio/mp3")
    
    # 6. 기록 저장 로직 (4/5_1 형식)
    now = datetime.now()
    date_str = now.strftime("%m/%d").replace("0", "") # 04/05 -> 4/5 형태
    
    # 같은 날짜의 기록 개수 확인하여 순번 정하기
    today_count = sum(1 for item in history_list if item['time'].startswith(date_str)) + 1
    time_label = f"{date_str}_{today_count}"
    
    # 중복 저장 방지 및 추가
    if not history_list or history_list[-1]['text'] != final_text:
        history_list.append({"time": time_label, "text": final_text})
        local_storage.setItem("study_history", json.dumps(history_list))
        st.toast(f"{time_label} 기록 완료!") # 하단에 잠깐 알림 표시
