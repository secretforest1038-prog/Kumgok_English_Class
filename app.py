import streamlit as st
from gtts import gTTS
import easyocr
import numpy as np
from PIL import Image
import io

# 1. 페이지 설정 (심플 모드)
st.set_page_config(page_title="Kumgok English Class", page_icon="🔊", layout="centered")

# --- UI 스타일링 (최대한 심플하게) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@600;800&display=swap');
    * { font-family: 'Pretendard', sans-serif; }
    
    .main-title {
        font-size: 3rem !important;
        font-weight: 800;
        text-align: center;
        color: #1e293b;
        margin: 40px 0;
    }

    /* 읽어주기 버튼 스타일 */
    .stButton>button {
        background: #4f46e5 !important;
        color: white !important;
        height: 60px !important;
        font-size: 1.4rem !important;
        border-radius: 12px !important;
        width: 100% !important;
        border: none !important;
    }

    /* 사이드바 및 불필요한 요소 완전 제거 */
    [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    #MainMenu, footer, [data-testid="stToolbar"] {
        visibility: hidden; display: none;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 모델 로드 (캐싱)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)
reader = load_ocr()

# 3. 메인 화면 구성
st.markdown("<div class='main-title'>Kumgok English Class</div>", unsafe_allow_html=True)

# 입력 세션 관리
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

# 방법 선택
input_mode = st.radio("공부 방법 선택", ["⌨️ 직접 입력", "📷 사진 촬영", "📁 앨범 사진"], horizontal=True)

captured_text = ""
if input_mode == "📷 사진 촬영":
    img_src = st.camera_input("교과서를 촬영하세요")
    if img_src:
        with st.spinner('읽는 중...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)
elif input_mode == "📁 앨범 사진":
    img_src = st.file_uploader("사진을 선택하세요", type=['jpg','png','jpeg'])
    if img_src:
        with st.spinner('읽는 중...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)

if captured_text:
    st.session_state.input_text = captured_text

# 문장 확인 및 수정
st.write("---")
final_text = st.text_area("영어 문장", value=st.session_state.input_text, height=150, placeholder="여기에 영어 문장이 나타납니다.")

# 재생 버튼
if st.button("🔊 영어로 읽어주기"):
    if final_text.strip():
        with st.spinner('목소리 만드는 중...'):
            tts = gTTS(text=final_text, lang='en')
            audio_data = io.BytesIO()
            tts.write_to_fp(audio_data)
            st.audio(audio_data.getvalue(), format="audio/mp3")
    else:
        st.warning("문장을 먼저 입력해주세요.")
