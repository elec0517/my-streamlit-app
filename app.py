from pathlib import Path
import base64
import os
import streamlit as st
import streamlit.components.v1 as components
from rag import rag_pipeline

ROOT = Path(__file__).parent
st.set_page_config(page_title="AIVLE · 학습 도우미", page_icon="🥠", layout="wide", initial_sidebar_state="collapsed")
st.markdown("<style>.stMainBlockContainer{max-width:none;padding:0!important}header[data-testid='stHeader']{display:none}iframe{display:block;border:0}</style>", unsafe_allow_html=True)
chat = components.declare_component("aivle_chat", path=str(ROOT / "ui"))
req = chat(result=st.session_state.get("result"), key="workbench", default=None)
if req and req.get("id") != (st.session_state.get("result") or {}).get("id"):
    result = {"id": req["id"], "chat": req["chat"]}
    try:
        key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("Streamlit Secrets에 OPENAI_API_KEY를 설정해 주세요.")
        if not req.get("files"):
            raise ValueError("먼저 채팅창의 ＋ 버튼으로 백서 PDF를 첨부해 주세요.")

        sources = []
        for doc in req.get("files", []):
            sources.append((doc["name"], base64.b64decode(doc["data"], validate=True)))
        result["text"], result["refs"] = rag_pipeline(req["question"], req["history"], sources, key, st.session_state.setdefault("vectors", {}))
    except (ValueError, FileNotFoundError) as exc:
        result["error"] = str(exc) if isinstance(exc, ValueError) else "백서.pdf 또는 Streamlit Secrets 설정을 확인해 주세요."
    except Exception as exc:
        result["error"] = f"응답을 가져오지 못했어요 ({type(exc).__name__}). API 키와 사용 한도를 확인하고 다시 시도해 주세요."
    st.session_state.result = result
    st.rerun()
