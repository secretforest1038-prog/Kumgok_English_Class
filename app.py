import streamlit as st
from gtts import gTTS
import easyocr
import numpy as np
from PIL import Image
import io
import json
from streamlit_local_storage import LocalStorage
from datetime import datetime

# 1. 페이지 설정 (초등학생 맞춤 UI)
st.set_page_config(
    page_title="초등 영어 발음 친구", 
    page_icon="🔊", 
    layout="wide",
    initial_sidebar_state="collapsed" # 처음엔 숨김
)

# --- 초특급 직관적 UI 스타일링 (CSS) ---
st.markdown("""
    <style>
    /* 전체 글자 크기 키우기 */
    html, body, [class*="css"]  {
        font-size: 1.2rem;
    }
    
    /* 메인 타이틀 스타일 */
    .main-title {
        font-size: 3rem !important;
        color: #FF6B6B; /* 예쁜 주황색 */
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* 학습 기록 보기 버튼 (메인 화면) */
    .stButton>button[data-testid="stBaseButton-secondary"] {
        background-color: #4ECDC4; /* 예쁜 민트색 */
        color: white;
        font-size: 1.5rem !important;
        padding: 15px 30px;
        border-radius: 10px;
        width: 100%;
        margin-bottom: 20px;
    }
    
    /* 발음 듣기 버튼 (메인 화면) */
    .stButton>button[data-testid="stBaseButton-primary"] {
        font-size: 2rem !important;
        padding: 20px 40px;
    }

    /* 사이드바 스타일 정의 */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
        padding: 20px;
    }
    
    /* 사이드바 내 기록 제목 스타일 */
    .sidebar-record-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #333;
    }

    /* 불필요한 UI 숨기기 (메뉴, 푸터 등) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    /* 기본 접기 버튼 숨기기 (우리가 만든 버튼 사용) */
    [data-testid="stSidebarCollapseButton"] {display: none;}
    </style>
""", unsafe_allow_html=True)


# 2. 로컬 저장소 및 OCR 초기화
local_storage = LocalStorage("english_learner")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])
reader = load_ocr()


# --- 사이드바 (나의 학습 기록) ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #333;'>📚 나의 학습 기록</h1>", unsafe_allow_html=True)
    st.write("그동안 공부한 문장들이에요!")
    
    saved_history = local_storage.getItem("study_history")
    history_list = json.loads(saved_history) if saved_history else []

    if history_list:
        for i, item in enumerate(reversed(history_list)):
            # 기록 제목 크기 키움
            with st.expander(f"📌 {item['time']} 기록", expanded=True):
                st.write(item['text'])
                # 다시 듣기 버튼 크기 키움
                if st.button("🔊 다시 듣기", key=f"re_{i}", use_container_width=True):
                    st.session_state.input_text = item['text']
                    st.rerun()
        
        st.divider()
        if st.button("🗑️ 전체 기록 삭제", use_container_width=True):
            local_storage.removeItem("study_history")
            st.rerun()
    else:
        st.info("아직 공부한 기록이 없어요. 문장을 입력하거나 사진을 찍어보세요!")


# --- 메인 화면 구성 ---
# 타이틀 크게 표시
st.markdown("<h1 class='main-title'>🔊 초등 영어 발음 친구</h1>", unsafe_allow_html=True)

# 3. [핵심 수정] 학습 기록 보기 버튼 추가 (크고 직관적)
col_record, _ = st.columns([1, 2])
with col_record:
    if st.button("📚 내 학습 기록 보기", key="show_history"):
        st.write("왼쪽에서 기록창이 열립니다!")
        # 사이드바 강제 열기 (Streamlit 함수 활용)
        st.session_state["sidebar_state"] = "expanded"
        st.rerun()

# 4. 입력부 (순서 조정: 입력 -> 촬영 -> 앨범)
input_mode = st.radio("공부할 방법을 골라주세요:", ["⌨️ 직접 입력", "📷 사진 촬영", "📁 앨범 선택"], horizontal=True)

if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

captured_text = ""
if input_mode == "⌨️ 직접 입력":
    pass
elif input_mode == "📷 사진 촬영":
    img_src = st.camera_input("교과서 문장을 찰칵! 찍어주세요")
    if img_src:
        with st.spinner('글자를 읽는 중... 조금만 기다려주세요!'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)
elif input_mode == "📁 앨범 선택":
    img_src = st.file_uploader("사진을 선택해주세요", type=['jpg','png','jpeg'])
    if img_src:
        with st.spinner('글자를 읽는 중... 조금만 기다려주세요!'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)

if captured_text:
    st.session_state.input_text = captured_text


# 5. 출력부
st.subheader("📝 공부할 문장 확인")
final_text = st.text_area("틀린 글자가 있다면 고쳐주세요:", value=st.session_state.input_text, height=150)

# 발음 듣기 버튼 크게
if st.button("🔊 발음 듣기", type="primary", use_container_width=True) and final_text:
    tts = gTTS(text=final_text, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    st.audio(fp, format="audio/mp3")
    
    # 6. 기록 저장 로직 (4/5_1 형식)
    now = datetime.now()
    date_str = now.strftime("%m/%d").replace("0", "") # 04/05 -> 4/5 형태
    
    today_count = sum(1 for item in history_list if item['time'].startswith(date_str)) + 1
    time_label = f"{date_str}_{today_count}"
    
    if not history_list or history_list[-1]['text'] != final_text:
        history_list.append({"time": time_label, "text": final_text})
        local_storage.setItem("study_history", json.dumps(history_list))
        st.toast(f"{time_label} 기록 완료!")
        st.rerun()
