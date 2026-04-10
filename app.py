import streamlit as st
from gtts import gTTS
import easyocr
import numpy as np
from PIL import Image
import io
import json
import streamlit.components.v1 as components
from streamlit_local_storage import LocalStorage
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="Kumgok English Class", page_icon="🔊", layout="wide")

# 2. [비장의 무기] 자바스크립트 강제 제어 코드
# 버튼을 누르면 브라우저가 직접 사이드바 버튼을 찾아 클릭하도록 만듭니다.
def sidebar_controller():
    components.html(
        """
        <script>
        var openSidebar = function() {
            var buttons = window.parent.document.getElementsByTagName('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].getAttribute('aria-label') == 'Open sidebar') {
                    buttons[i].click();
                    break;
                }
            }
        };
        // 메인 화면의 특정 버튼과 연결하기 위한 장치
        window.parent.document.addEventListener('keydown', function(e) {
            if (e.key === 'F2') { openSidebar(); }
        });
        </script>
        """,
        height=0,
    )

sidebar_controller()

# --- UI 디자인 (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@600;800&display=swap');
    * { font-family: 'Pretendard', sans-serif; }
    
    .main-title {
        font-size: 3.5rem !important;
        font-weight: 800;
        text-align: center;
        color: #1e293b;
        margin-bottom: 30px;
    }

    /* 기록 확인 버튼 스타일 - 좌측 상단 고정 */
    .record-btn {
        background-color: #4f46e5 !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        cursor: pointer;
        border: none;
        margin-bottom: 20px;
    }
    
    #MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# 3. 모델 및 저장소 로드
local_storage = LocalStorage("kumgok_english")
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)
reader = load_ocr()

# 4. 사이드바 영역
with st.sidebar:
    st.markdown("## 📚 나의 학습 기록")
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
        st.info("기록이 아직 없어요!")

# 5. 메인 화면 상단
col_btn, _ = st.columns([1, 4])
with col_btn:
    # [핵심 변경] 버튼 클릭 시 서버 새로고침 없이 바로 사이드바를 여는 HTML 버튼
    st.components.v1.html(
        """
        <button onclick="window.parent.document.querySelector('button[aria-label=\\'Open sidebar\\']').click()" 
        style="background-color: #4f46e5; color: white; border: none; padding: 12px 24px; border-radius: 10px; font-weight: bold; font-size: 16px; cursor: pointer; width: 100%;">
        📋 기록 확인하기
        </button>
        """,
        height=60,
    )

st.markdown("<div class='main-title'>Kumgok English Class</div>", unsafe_allow_html=True)

# 6. 입력 섹션
input_mode = st.radio("방법 선택", ["⌨️ 직접 입력", "📷 사진 촬영", "📁 앨범 사진"], horizontal=True)

if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

captured_text = ""
if input_mode == "📷 사진 촬영":
    img_src = st.camera_input("교과서를 촬영하세요")
    if img_src:
        with st.spinner('글자를 읽는 중...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)
elif input_mode == "📁 앨범 사진":
    img_src = st.file_uploader("사진을 선택해주세요", type=['jpg','png','jpeg'])
    if img_src:
        with st.spinner('글자를 읽는 중...'):
            result = reader.readtext(np.array(Image.open(img_src)), detail=0)
            captured_text = " ".join(result)

if captured_text:
    st.session_state.input_text = captured_text

# 7. 출력 및 음성 재생 섹션
st.subheader("📝 문장 확인")
final_text = st.text_area("내용을 확인하거나 수정하세요", value=st.session_state.input_text, height=150)

if st.button("🔊 영어로 읽어주기", type="primary", use_container_width=True):
    if final_text.strip():
        with st.spinner('음성 준비 중...'):
            tts = gTTS(text=final_text, lang='en')
            audio_data = io.BytesIO()
            tts.write_to_fp(audio_data)
            # 재생과 저장을 동시에 처리
            st.audio(audio_data.getvalue(), format="audio/mp3")
            
            # 기록 저장
            now = datetime.now()
            date_str = f"{now.month}/{now.day}"
            today_count = sum(1 for item in history_list if item['time'].startswith(date_str)) + 1
            time_label = f"{date_str}_{today_count}"
            
            if not history_list or history_list[-1]['text'] != final_text:
                history_list.append({"time": time_label, "text": final_text})
                local_storage.setItem("study_history", json.dumps(history_list))
                st.toast(f"기록 완료: {time_label}")
    else:
        st.warning("문장을 입력해주세요.")
