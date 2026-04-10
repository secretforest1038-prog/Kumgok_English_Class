import streamlit as st
from gtts import gTTS
import easyocr
import numpy as np
from PIL import Image
import io
import json
from streamlit_local_storage import LocalStorage
from datetime import datetime

# 1. 페이지 설정 및 상태 관리
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "collapsed"

st.set_page_config(
    page_title="Kumgok English Class", 
    page_icon="🔊", 
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)

# --- 세련된 UI 디자인 (CSS) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Pretendard', sans-serif;
    }}

    /* 제목 스타일 */
    .main-title {{
        font-size: 3.2rem !important;
        color: #1e293b;
        text-align: center;
        font-weight: 800;
        margin: 40px 0;
    }}

    /* [수정] 좌측 학습 기록 버튼 디자인 */
    .stButton>button[data-testid="stBaseButton-secondary"] {{
        position: fixed;
        top: 20px;
        left: 20px;
        width: 160px;
        height: 50px;
        background-color: #ffffff !important;
        color: #4f46e5 !important;
        border: 2px solid #4f46e5 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        z-index: 1000;
        transition: all 0.3s ease;
    }}

    /* 읽어주기 버튼 디자인 */
    .stButton>button[data-testid="stBaseButton-primary"] {{
        background: #4f46e5 !important;
        font-size: 1.4rem !important;
        padding: 0.8rem !important;
        border-radius: 12px !important;
        margin-top: 10px;
    }}

    /* 불필요한 기본 UI 제거 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stToolbar"] {{visibility: hidden;}}
    [data-testid="stSidebarCollapseButton"] {{display: none;}}
    </style>
""", unsafe_allow_html=True)

# 2. 로컬 저장소 및 모델 초기화
local_storage = LocalStorage("kumgok_english")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)
reader = load_ocr()

# --- 사이드바 제어 로직 ---
def toggle_sidebar():
    if st.session_state.sidebar_state == "collapsed":
        st.session_state.sidebar_state = "expanded"
    else:
        st.session_state.sidebar_state = "collapsed"
    # 실제 Streamlit 설정을 강제로 변경하기 위해 쿼리 파라미터나 리런 사용
    st.rerun()

# --- 사이드바 영역 ---
with st.sidebar:
    st.markdown("<h2 style='color: #1e293b;'>📚 학습 기록</h2>", unsafe_allow_html=True)
    
    saved_history = local_storage.getItem("study_history")
    history_list = json.loads(saved_history) if saved_history else []

    if history_list:
        for i, item in enumerate(reversed(history_list[-15:])):
            with st.expander(f"📝 {item['time']} 기록", expanded=False):
                st.write(item['text'])
                if st.button("다시 듣기", key=f"re_{i}", use_container_width=True):
                    st.session_state.input_text = item['text']
                    st.rerun()
        
        st.divider()
        if st.button("전체 삭제", use_container_width=True):
            local_storage.removeItem("study_history")
            st.rerun()
    
    if st.button("창 닫기 ✖", use_container_width=True):
        st.session_state.sidebar_state = "collapsed"
        st.rerun()

# 3. 메인 화면 상단 (좌측 버튼)
if st.button("📋 기록 확인", on_click=toggle_sidebar):
    pass

st.markdown("<h1 class='main-title'>Kumgok English Class</h1>", unsafe_allow_html=True)

# 4. 입력 섹션
input_mode = st.radio("방법 선택", ["⌨️ 직접 입력", "📷 사진 촬영", "📁 앨범 사진"], horizontal=True)

if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

captured_text = ""
if input_mode == "📷 사진 촬영":
    img_src = st.camera_input("교과서를 촬영하세요")
    if img_src:
        with st.spinner('문자 분석 중...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)
elif input_mode == "📁 앨범 사진":
    img_src = st.file_uploader("사진을 선택하세요", type=['jpg','png','jpeg'])
    if img_src:
        with st.spinner('문자 분석 중...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)

if captured_text:
    st.session_state.input_text = captured_text

# 5. 출력 섹션
st.subheader("📝 문장 확인")
final_text = st.text_area("내용을 확인하거나 수정하세요", value=st.session_state.input_text, height=120)

if st.button("🔊 영어로 읽어주기", type="primary", use_container_width=True) and final_text:
    with st.spinner('음성 생성 중...'):
        tts = gTTS(text=final_text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        st.audio(fp, format="audio/mp3")
    
    # 기록 저장 (월/일_순번)
    now = datetime.now()
    date_str = f"{now.month}/{now.day}"
    today_count = sum(1 for item in history_list if item['time'].startswith(date_str)) + 1
    time_label = f"{date_str}_{today_count}"
    
    if not history_list or history_list[-1]['text'] != final_text:
        history_list.append({"time": time_label, "text": final_text})
        local_storage.setItem("study_history", json.dumps(history_list))
        st.rerun()
