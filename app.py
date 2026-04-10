import streamlit as st
from gtts import gTTS
import easyocr
import numpy as np
from PIL import Image
import io
import json
from streamlit_local_storage import LocalStorage
from datetime import datetime

# 1. 페이지 설정 (사이드바 항상 열림 상태로 고정)
st.set_page_config(
    page_title="Kumgok English Class", 
    page_icon="🔊", 
    layout="wide",
    initial_sidebar_state="expanded" # 항상 열려 있도록 설정
)

# --- UI 스타일링 (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@600;800&display=swap');
    * { font-family: 'Pretendard', sans-serif; }
    
    .main-title {
        font-size: 3rem !important;
        font-weight: 800;
        text-align: center;
        color: #1e293b;
        margin-bottom: 20px;
    }

    /* 사이드바 너비 고정 및 스타일 */
    [data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 300px !important;
        background-color: #f8fafc !important;
        border-right: 2px solid #e2e8f0;
    }

    /* 읽어주기 버튼 스타일 */
    .stButton>button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        height: 70px !important;
        font-size: 1.6rem !important;
        border-radius: 12px !important;
        width: 100% !important;
        border: none !important;
    }

    /* 사이드바 내부 폰트 조절 */
    .sidebar-text { font-size: 1.1rem; color: #334155; }

    /* 불필요한 기본 버튼들 완전 제거 */
    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stSidebarCollapseButton"] {
        visibility: hidden; display: none;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 모델 및 저장소 로드
local_storage = LocalStorage("kumgok_english")
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)
reader = load_ocr()

# 3. [고정형] 사이드바 영역
with st.sidebar:
    st.markdown("## 📚 나의 학습 기록")
    st.info("왼쪽 기록을 누르면 다시 공부할 수 있어요!")
    
    saved_history = local_storage.getItem("study_history")
    history_list = json.loads(saved_history) if saved_history else []

    if history_list:
        for i, item in enumerate(reversed(history_list[-15:])):
            with st.expander(f"📝 {item['time']} 기록"):
                st.write(item['text'])
                if st.button("다시 듣기", key=f"re_{i}", use_container_width=True):
                    st.session_state.input_text = item['text']
                    st.rerun()
        st.divider()
        if st.button("전체 삭제", use_container_width=True):
            local_storage.removeItem("study_history")
            st.rerun()
    else:
        st.write("아직 기록이 없어요!")

# 4. 메인 화면 구성
st.markdown("<div class='main-title'>Kumgok English Class</div>", unsafe_allow_html=True)

# 입력 세션 상태 관리
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

# 입력 모드 선택
input_mode = st.radio("공부할 방법을 골라주세요", ["⌨️ 직접 입력", "📷 사진 촬영", "📁 앨범 사진"], horizontal=True)

captured_text = ""
if input_mode == "📷 사진 촬영":
    img_src = st.camera_input("교과서 문장을 촬영하세요")
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

# 5. 출력 및 음성 재생 섹션
st.subheader("📝 문장 확인")
final_text = st.text_area("내용을 확인하거나 수정하세요", value=st.session_state.input_text, height=150)

# 재생 및 저장 로직
if st.button("🔊 영어로 읽어주기", type="primary"):
    if final_text.strip():
        with st.spinner('음성 준비 중...'):
            # 1. 음성 생성 및 즉시 재생
            tts = gTTS(text=final_text, lang='en')
            audio_data = io.BytesIO()
            tts.write_to_fp(audio_data)
            st.audio(audio_data.getvalue(), format="audio/mp3")
            
            # 2. 기록 저장 (월/일_순번)
            now = datetime.now()
            date_str = f"{now.month}/{now.day}"
            today_count = sum(1 for item in history_list if item['time'].startswith(date_str)) + 1
            time_label = f"{date_str}_{today_count}"
            
            if not history_list or history_list[-1]['text'] != final_text:
                history_list.append({"time": time_label, "text": final_text})
                local_storage.setItem("study_history", json.dumps(history_list))
                st.toast(f"저장 완료: {time_label}")
                # 주의: 여기서 st.rerun()을 하면 재생 중인 오디오가 끊길 수 있으므로 제외하거나 
                # toast로만 알림을 줍니다.
    else:
        st.warning("문장을 입력해주세요.")
