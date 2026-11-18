import os

import streamlit as st

from rag import retrieve
from llm import draft
from jobaba_pipeline import BOARD, action, new_state

st.set_page_config(page_title="잡아바 공고 검수", page_icon="📋", layout="wide")
st.title("잡아바 공고 등록·검수")
st.caption("게시판 등록 → 신규 공고 감지 → 초안 생성 → 운영자 검수")

if "pipeline" not in st.session_state:
    st.session_state.pipeline = new_state()
    st.session_state.registration = 0

pipeline = st.session_state.pipeline


def run_step(name, data=None):
    try:
        message = action(pipeline, name, data or {})
    except Exception as error:
        st.session_state.feedback = (False, str(error))
        return False
    st.session_state.feedback = (True, message)
    return True


try:
    if not os.environ.get("OPENAI_API_KEY") and "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
except FileNotFoundError:
    pass

with st.form("board"):
    st.subheader("수집 게시판")
    modes = ["발표 시연"]
    if os.environ.get("OPENAI_API_KEY"):
        modes.append("실제 연동")
    mode = st.radio("실행 모드", modes, horizontal=True)
    address = st.text_input("성남시청 채용공고 목록 주소", BOARD)
    register = st.form_submit_button("게시판 등록", type="primary")

if register and run_step("register", {
    "mode": "demo" if mode == "발표 시연" else "live",
    "address": address,
}):
    st.session_state.registration += 1
    st.session_state.last_scan = 0.0

if not pipeline["mode"]:
    if "feedback" in st.session_state:
        st.error(st.session_state.feedback[1])
    st.info("발표 시연은 실제 공고를 바탕으로 준비한 본문과 초안을 사용해요. API 키 없이 실행할 수 있어요.")
    st.stop()

demo = pipeline["mode"] == "demo"
st.caption(
    "발표 시연 · 샘플 본문과 준비된 초안"
    if demo else "실제 연동 · 열린 세션에서 10분마다 확인"
)


@st.fragment(run_every="3s" if demo else "10m")
def review():
    import time

    now = time.monotonic()
    left, right = st.columns(2)
    if demo and left.button("시연 공고 게시", disabled=pipeline["incoming"]):
        if run_step("publish"):
            st.rerun(scope="app")
    manual = right.button("지금 확인")
    auto_demo = demo and pipeline["incoming"] and not pipeline["items"]
    auto_live = not demo and now - st.session_state.last_scan >= 600
    if manual or auto_demo or auto_live:
        st.session_state.last_scan = now
        with st.spinner("새 공고를 확인하고 있어요."):
            run_step("scan")

    if "feedback" in st.session_state:
        success, message = st.session_state.feedback
        (st.success if success else st.error)(message)

    st.subheader("등록 초안 목록")
    items = pipeline["items"]
    if not items:
        st.info("감지된 신규 공고가 아직 없어요.")
        return

    item_id = st.selectbox(
        "검수할 공고", list(items),
        format_func=lambda key: f"{items[key]['values']['공고명'] or key} · {items[key]['status']}",
        key=f"notice_{st.session_state.registration}",
    )
    item = items[item_id]
    with st.expander("RAG가 검색한 시연용 등록 지침"):
        for rule in retrieve(item["body"]):
            st.write(rule)
    if demo and os.environ.get("OPENAI_API_KEY") and item["status"] == "검수 대기":
        if st.button("이 본문으로 LLM 초안 생성"):
            try:
                values, evidence = draft(item["body"])
            except Exception as error:
                st.error(f"초안 생성 실패 · {error}")
            else:
                item.update(values=values, evidence=evidence)
                for field in values:
                    st.session_state.pop(f"{st.session_state.registration}_{item_id}_{field}", None)
                st.rerun(scope="app")
    original, editor = st.columns(2)
    with original:
        st.markdown("#### 시연용 공고 본문" if demo else "#### 수집 본문")
        st.link_button("공식 원문 보기", item["url"])
        st.text(item["body"])
    with editor:
        st.markdown("#### 잡아바 등록 초안")
        st.caption(item["status"])
        approved = item["status"] == "모의 승인 완료"
        values = {}
        for field, value in item["values"].items():
            values[field] = st.text_input(
                field, value=value, disabled=approved,
                key=f"{st.session_state.registration}_{item_id}_{field}",
            )
            st.caption(item["evidence"][field] or "원문 확인 필요")
        if st.button("모의 승인", type="primary", disabled=approved):
            if run_step("approve", {"id": item_id, "values": values}):
                st.rerun(scope="app")
            st.error(st.session_state.feedback[1])


review()
