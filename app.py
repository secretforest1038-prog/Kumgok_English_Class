import streamlit as st
from gtts import gTTS
import easyocr
import numpy as np
from PIL import Image
import io
import json
from streamlit_local_storage import LocalStorage
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(
    page_title="Kumgok English Class", 
    page_icon="🔊", 
    layout="wide",
    initial_sidebar_state="auto" # 기기에 맞춰 자동으로 보이게 설정
)

# --- UI 스타일링 및 버튼 크기 강제 확대 (CSS) ---
st.markdown("""
    <style>
    /* 전체 폰트 및 배경 */
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Nanum Gothic', sans-serif;
    }

    /* 프로그램 제목 스타일 */
    .main-title {
        font-size: 3.5rem !important;
        color: #2E5BFF;
        text-align: center;
        font-weight: bold;
        padding: 20px 0;
        border-bottom: 3px solid #F0F2F6;
        margin-bottom: 30px;
    }

    /* 사이드바 열기/닫기 화살표 버튼 크기 키우기 (가장 중요!) */
    [data-testid="stSidebarCollapseButton"] {
        background-color: #2E5BFF !important;
        color: white !important;
        width: 60px !important;
        height: 60px !important;
        top: 10px !important;
        left: 10px !important;
        border-radius: 50% !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    [data-testid="stSidebarCollapseButton"] svg {
        width: 35px !important;
        height: 35px !important;
    }

    /* 버튼 공통 스타일 */
    .stButton>button {
        border-radius: 12px !important;
        font-weight: bold !important;
    }

    /* 발음 듣기 버튼 (Primary) */
    .stButton>button[data-testid="stBaseButton-primary"] {
        background-color: #FF4B4B !important;
        font-size: 1.8rem !important;
        padding: 1rem 2rem !important;
    }

    /* 안내 문구 스타일 */
    .info-text {
        background-color: #E8F0FE;
        padding: 15px;
        border-radius: 10px;
        color: #1967D2;
        font-weight: bold;
        margin-bottom: 20px;
        text-align: center;
    }

    /* 하단 푸터 및 메뉴 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 2. 로컬 저장소 및 OCR 초기화
local_storage = LocalStorage("kumgok_english")

@st.cache_resource
def load_ocr():
    # 모델 로드 시 진행 바 표시 방지 및 속도 최적화
    return easyocr.Reader(['en'], gpu=False)
reader = load_ocr()

# 3. 사이드바 (나의 학습 기록)
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>📚 My History</h2>", unsafe_allow_html=True)
    st.write("공부했던 기록을 다시 들어보세요!")
    
    saved_history = local_storage.getItem("study_history")
    history_list = json.loads(saved_history) if saved_history else []

    if history_list:
        for i, item in enumerate(reversed(history_list[-15:])): # 최근 15개
            with st.expander(f"📌 {item['time']}", expanded=False):
                st.write(item['text'])
                if st.button("🔊 Re-play", key=f"re_{i}", use_container_width=True):
                    st.session_state.input_text = item['text']
                    st.rerun()
        
        st.divider()
        if st.button("🗑️ Reset All", use_container_width=True):
            local_storage.removeItem("study_history")
            st.rerun()
    else:
        st.info("No history yet!")

# 4. 메인 화면 구성
st.markdown("<h1 class='main-title'>📖 Kumgok English Class</h1>", unsafe_allow_html=True)

# 학생들을 위한 친절한 안내
st.markdown("<div class='info-text'>📍 왼쪽 위의 파란색 동그라미 버튼(>)을 누르면 내 학습 기록이 보여요!</div>", unsafe_allow_html=True)

# 입력 모드 선택
input_mode = st.radio("Choose Method:", ["⌨️ Typing", "📷 Camera", "📁 Album"], horizontal=True)

if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

# 입력 방식별 로직
captured_text = ""
if input_mode == "⌨️ Typing":
    pass
elif input_mode == "📷 Camera":
    img_src = st.camera_input("Take a photo of your textbook!")
    if img_src:
        with st.spinner('Reading English...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)
elif input_mode == "📁 Album":
    img_src = st.file_uploader("Choose a photo from your tablet", type=['jpg','png','jpeg'])
    if img_src:
        with st.spinner('Reading English...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)

if captured_text:
    st.session_state.input_text = captured_text

# 5. 출력 및 음성 재생
st.subheader("📝 Sentence Check")
final_text = st.text_area("Check and edit the sentence:", value=st.session_state.input_text, height=120)

if st.button("🔊 Speak English", type="primary", use_container_width=True) and final_text:
    with st.spinner('Generating voice...'):
        tts = gTTS(text=final_text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        st.audio(fp, format="audio/mp3")
    
    # 6. 기록 저장 (4/10_1 형식)
    now = datetime.now()
    date_str = f"{now.month}/{now.day}"
    
    today_count = sum(1 for item in history_list if item['time'].startswith(date_str)) + 1
    time_label = f"{date_str}_{today_count}"
    
    if not history_list or history_list[-1]['text'] != final_text:
        history_list.append({"time": time_label, "text": final_text})
        local_storage.setItem("study_history", json.dumps(history_list))
        st.toast(f"Saved: {time_label}")
        st.rerun()
