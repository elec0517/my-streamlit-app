import streamlit as st

st.set_page_config(
    page_title="에이블스쿨 학습 도우미",
    page_icon="📚",
    layout="wide"
)

# 대화 기록 준비
if "messages" not in st.session_state:
    st.session_state.messages = []

# 왼쪽 메뉴
with st.sidebar:
    st.header("📄 백서 업로드")

    uploaded_file = st.file_uploader(
        "AIVLE School 백서를 올려주세요.",
        type=["pdf"]
    )

    if uploaded_file:
        st.success(f"선택한 파일: {uploaded_file.name}")

    st.divider()

    if st.button("🗑️ 대화 삭제", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 메인 화면
st.title("📚 에이블스쿨 학습 도우미")
st.caption("백서를 바탕으로 교육, 학습 방법, 프로젝트에 대해 질문해보세요.")

# 기존 대화 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 질문 입력
question = st.chat_input(
    "궁금한 내용을 입력해주세요.",
    disabled=uploaded_file is None
)

if uploaded_file is None:
    st.info("왼쪽에서 백서 PDF를 먼저 업로드해주세요.")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    answer = (
        "질문이 정상적으로 입력됐어요! "
        "다음 단계에서 백서 검색과 AI 답변 기능을 연결할 예정이에요."
    )

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })
