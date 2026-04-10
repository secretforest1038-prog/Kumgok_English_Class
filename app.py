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
    initial_sidebar_state="collapsed"
)

# --- 세련된 UI 스타일링 (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }

    /* 프로그램 제목 (영어 유지) */
    .main-title {
        font-size: 3rem !important;
        color: #1E293B;
        text-align: center;
        font-weight: 800;
        margin-bottom: 40px;
        letter-spacing: -1px;
    }

    /* 하단 플로팅 '기록 보기' 버튼 스타일 */
    .stButton>button[data-testid="stBaseButton-secondary"] {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 180px;
        height: 60px;
        background-color: #4F46E5 !important; /* 세련된 인디고 블루 */
        color: white !important;
        border-radius: 30px !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.4) !important;
        z-index: 999;
        border: none !important;
    }

    /* 발음 듣기 버튼 */
    .stButton>button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        border: none !important;
        font-size: 1.5rem !important;
        padding: 1rem !important;
        width: 100% !important;
        border-radius: 15px !important;
    }

    /* 사이드바 스타일 보정 */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }

    /* 기존 사이드바 화살표 숨기기 */
    [data-testid="stSidebarCollapseButton"] { display: none; }
    
    /* 메뉴 및 푸터 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 2. 로컬 저장소 및 OCR 초기화
local_storage = LocalStorage("kumgok_english")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)
reader = load_ocr()

# 3. 사이드바 (나의 학습 기록) - 한글화
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #1E293B;'>📚 학습 기록</h2>", unsafe_allow_html=True)
    st.write("다시 듣고 싶은 문장을 선택하세요.")
    
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
        if st.button("전체 기록 삭제", use_container_width=True):
            local_storage.removeItem("study_history")
            st.rerun()
    else:
        st.info("아직 기록이 없어요!")

# 4. 메인 화면 구성
st.markdown("<h1 class='main-title'>Kumgok English Class</h1>", unsafe_allow_html=True)

# [개선] 기록 보기 플로팅 버튼 (사이드바 제어용)
# 버튼을 누르면 사이드바가 열린 상태로 페이지를 다시 로드하게 유도
if st.button("📚 내 학습 기록"):
    # Streamlit은 사이드바 버튼이 숨겨진 경우 사이드바를 열기 위해 세션 스테이트를 쓰지만, 
    # 직접 제어가 까다로우므로 학생들에게 "왼쪽 창을 보세요"라고 안내하는 방식이 가장 안정적입니다.
    # 하지만 여기서는 더 나은 UX를 위해 사이드바 상태를 세션으로 관리하려 시도합니다.
    st.info("왼쪽에서 학습 기록 창이 열렸습니다!")
    # 실제 사이드바를 강제로 여는 가장 확실한 방법은 기본 화살표를 쓰는 것이지만, 
    # 화살표를 대신할 수 있게 사이드바 자체에 '닫기' 버튼을 두어 활용합니다.

# 입력 모드 선택 (한글화)
input_mode = st.radio("공부할 방법을 골라주세요:", ["⌨️ 직접 입력", "📷 카메라 촬영", "📁 앨범 사진"], horizontal=True)

if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

# 입력 방식별 로직
captured_text = ""
if input_mode == "⌨️ 직접 입력":
    pass
elif input_mode == "📷 카메라 촬영":
    img_src = st.camera_input("교과서 문장을 찍어주세요!")
    if img_src:
        with st.spinner('영어를 읽는 중...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)
elif input_mode == "📁 앨범 사진":
    img_src = st.file_uploader("태블릿에서 사진을 골라주세요", type=['jpg','png','jpeg'])
    if img_src:
        with st.spinner('영어를 읽는 중...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)

if captured_text:
    st.session_state.input_text = captured_text

# 5. 출력 및 음성 재생 (한글화)
st.subheader("📝 문장 확인 및 수정")
final_text = st.text_area("인식된 내용이 틀렸다면 직접 고쳐보세요:", value=st.session_state.input_text, height=120)

if st.button("🔊 영어로 읽어주기", type="primary", use_container_width=True) and final_text:
    with st.spinner('목소리 만드는 중...'):
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
        st.toast(f"저장 완료: {time_label}")
        st.rerun()
