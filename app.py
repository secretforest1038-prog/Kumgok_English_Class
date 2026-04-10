import streamlit as st
from gtts import gTTS
import easyocr
import numpy as np
from PIL import Image
import io
import json
from streamlit_local_storage import LocalStorage

# 1. 페이지 설정 및 UI 숨기기
st.set_page_config(page_title="중학교 영어 발음 도우미", page_icon="📸", layout="wide")

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
        for i, item in enumerate(reversed(history_list[-10:])):
            with st.expander(f"{item['time']} - 기록"):
                st.write(item['text'])
                if st.button("🔊 다시 듣기", key=f"re_{i}"):
                    st.session_state.input_text = item['text']
                    st.rerun()
    else:
        st.info("학습 기록이 없습니다.")

# 4. 메인 화면 - 입력부
st.title("🏫 English Pronunciation Helper")
input_mode = st.radio("방법 선택:", ["📷 촬영", "📁 앨범", "⌨️ 입력"], horizontal=True)

if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

# 이미지 처리 로직
img_src = None
if input_mode == "📷 촬영":
    img_src = st.camera_input("문장을 찍으세요")
elif input_mode == "📁 앨범":
    img_src = st.file_uploader("사진 선택", type=['jpg','png','jpeg'])

if img_src:
    image = Image.open(img_src)
    with st.spinner('글자를 읽는 중...'):
        result = reader.readtext(np.array(image), detail=0)
        st.session_state.input_text = " ".join(result)

# 5. 메인 화면 - 출력부
final_text = st.text_area("문장 확인 및 수정:", value=st.session_state.input_text, height=100)
speed = st.radio("속도:", ["Normal", "Slow"], horizontal=True)

if st.button("🔊 발음 듣기", type="primary") and final_text:
    tts = gTTS(text=final_text, lang='en', slow=(speed=="Slow"))
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    st.audio(fp, format="audio/mp3")
    
    # 기록 저장
    from datetime import datetime
    new_entry = {"time": datetime.now().strftime("%H:%M"), "text": final_text}
    if not history_list or history_list[-1]['text'] != final_text:
        history_list.append(new_entry)
        local_storage.setItem("study_history", json.dumps(history_list))
        st.rerun()