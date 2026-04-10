import streamlit as st
from gtts import gTTS
import io

# 1. 페이지 설정 (최소한의 기능)
st.set_page_config(page_title="Kumgok English Class", page_icon="🔊", layout="centered")

# --- UI 스타일링 (깔끔하고 직관적으로) ---
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
        font-size: 1.5rem !important;
        border-radius: 12px !important;
        width: 100% !important;
        border: none !important;
        font-weight: bold !important;
    }

    /* 불필요한 Streamlit 요소 완전 제거 */
    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
        display: none !important;
        visibility: hidden;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 메인 화면 구성
st.markdown("<div class='main-title'>Kumgok English Class</div>", unsafe_allow_html=True)

# 3. 직접 입력 섹션
st.subheader("📝 영어 문장 입력")
input_text = st.text_area(
    "여기에 공부할 영어 문장을 적어주세요.", 
    height=200, 
    placeholder="예: I have a large family. My sister is very funny."
)

# 4. 재생 버튼
st.write("") # 간격 조절
if st.button("🔊 영어로 읽어주기"):
    if input_text.strip():
        with st.spinner('원어민 목소리를 만들고 있어요...'):
            try:
                tts = gTTS(text=input_text, lang='en')
                audio_data = io.BytesIO()
                tts.write_to_fp(audio_data)
                st.audio(audio_data.getvalue(), format="audio/mp3")
            except Exception as e:
                st.error("음성 생성 중 오류가 발생했습니다. 인터넷 연결을 확인해 주세요.")
    else:
        st.warning("먼저 영어 문장을 입력해 주세요!")
