import streamlit as st
from gtts import gTTS
import easyocr
import numpy as np
from PIL import Image
import io
import json
from streamlit_local_storage import LocalStorage
from datetime import datetime

# 1. 페이지 설정 및 상태 초기화
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "collapsed"

st.set_page_config(
    page_title="Kumgok English Class", 
    page_icon="🔊", 
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- 상호작용 및 디자인 강화 CSS ---
st.markdown("""
    <style>
    /* 폰트 및 배경 */
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@600;800&display=swap');
    * { font-family: 'Pretendard', sans-serif; }

    /* 메인 타이틀 */
    .main-title {
        font-size: 3.5rem !important;
        font-weight: 800;
        text-align: center;
        color: #1e293b;
        margin-top: 20px;
        margin-bottom: 40px;
    }

    /* [중요] 기록 확인 버튼 - 시인성 극대화 */
    div[data-testid="column"] .stButton button {
        background-color: #4f46e5 !important;
        color: white !important;
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        height: 60px !important;
        width: 100% !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        border: none !important;
    }

    /* 읽어주기 버튼 - 강조 */
    .stButton>button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
        height: 70px !important;
        font-size: 1.6rem !important;
    }

    /* 사이드바 내부 스타일 */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
    }

    /* 기본 UI 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    [data-testid="stSidebarCollapseButton"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# 2. 유틸리티 로드
local_storage = LocalStorage("kumgok_english")
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)
reader = load_ocr()

# 3. 사이드바 영역
with st.sidebar:
    st.markdown("## 📚 나의 학습 기록")
    saved_history = local_storage.getItem("study_history")
    history_list = json.loads(saved_history) if saved_history else []

    if history_list:
        for i, item in enumerate(reversed(history_list[-15:])):
            with st.expander(f"📝 {item['time']} 기록"):
                st.write(item['text'])
                if st.button("🔊 다시 듣기", key=f"re_{i}", use_container_width=True):
                    st.session_state.input_text = item['text']
                    st.rerun()
        st.divider()
        if st.button("🗑️ 전체 삭제", use_container_width=True):
            local_storage.removeItem("study_history")
            st.rerun()
    
    if st.button("닫기 ✖", use_container_width=True):
        st.session_state.sidebar_state = "collapsed"
        st.rerun()

# 4. 메인 화면 레이아웃
# 상단에 기록 확인 버튼을 크게 배치
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("📋 기록 확인하기"):
        st.session_state.sidebar_state = "expanded"
        st.rerun()

st.markdown("<div class='main-title'>Kumgok English Class</div>", unsafe_allow_html=True)

# 입력 섹션
input_mode = st.radio("공부할 방법을 골라주세요", ["⌨️ 직접 입력", "📷 사진 촬영", "📁 앨범 사진"], horizontal=True)

if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

captured_text = ""
if input_mode == "📷 사진 촬영":
    img_src = st.camera_input("교과서 문장을 찍어주세요")
    if img_src:
        with st.spinner('글자를 읽고 있어요...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)
elif input_mode == "📁 앨범 사진":
    img_src = st.file_uploader("사진을 선택해주세요", type=['jpg','png','jpeg'])
    if img_src:
        with st.spinner('글자를 읽고 있어요...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)

if captured_text:
    st.session_state.input_text = captured_text

# 출력 섹션
st.subheader("📝 문장 확인")
final_text = st.text_area("내용을 확인하거나 수정하세요", value=st.session_state.input_text, height=150)

if st.button("🔊 영어로 읽어주기", type="primary", use_container_width=True) and final_text:
    with st.spinner('음성 준비 중...'):
        tts = gTTS(text=final_text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        st.audio(fp, format="audio/mp3")
    
    # 기록 저장
    now = datetime.now()
    date_str = f"{now.month}/{now.day}"
    today_count = sum(1 for item in history_list if item['time'].startswith(date_str)) + 1
    time_label = f"{date_str}_{today_count}"
    
    if not history_list or history_list[-1]['text'] != final_text:
        history_list.append({"time": time_label, "text": final_text})
        local_storage.setItem("study_history", json.dumps(history_list))
        st.rerun()
