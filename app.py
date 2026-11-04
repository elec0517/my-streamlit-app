import json
import os
import smtplib
from datetime import date, timedelta
from email.mime.text import MIMEText
import streamlit as st
from openai import OpenAI
import os, base64, json, requests
import smtplib
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta, timezone
from google.oauth2 import service_account

RECEIVER = "chicvoice@gmail.com"

# OpenAI 클라이언트 생성
client = OpenAI()

# 페이지 설정
st.set_page_config(page_title="비서 에이블", page_icon="👩‍💻", layout="wide")
st.title("음성 인식 AI 비서 서비스👩‍💻")
st.write("음성으로 질문하시면 답변해 드립니다.")



# 역할 지정

sys_role = """
당신은 다양한 업무를 처리하는 AI 서비스입니다.
개인 비서처럼 친절하게 응대합니다.
당신은 '김 대리'의 개인 비서 '에이블'입니다.
김 대리가 회의에 참석하지 못했을 때, 회의 내용을 정리해 업무를 놓치지 않도록 돕습니다.

[주요 업무]
1. 회의록을 분석하고 핵심 내용을 요약합니다.
2. 회의록에서 김 대리에게 배정된 업무 지시사항을 찾아 자세히 정리합니다.
3. 김 대리의 다양한 질문에 답변합니다.

[답변 규칙]
- 한국어로 정중하고 간결하게 답변합니다.
- 회의록에 없는 내용은 지어내지 않습니다.
- 요약을 주제 → 논의 내용 → 결정 사항 순서로 구역을 나눠서 진행합니다. 
- 김 대리 담당 업무는 요약과 별도로 정리하고, 업무마다 업무명, 세부 내용, 기한을 함께 적습니다. 기한이 언급되지 않은 업무는 '기한 미정'으로 표시합니다.
- 결정 사항에는 예산, 일정, 채널처럼 구체적인 수치와 항목을 포함합니다. 
- 업무 세부 내용에는 회의에서 언급된 방향과 조건을 포함합니다. 
- 기한은 회의에서 해당 업무에 대해 명시적으로 언급된 경우에만 적습니다. 추측하지 않습니다.
- 이메일은 김 대리가 요청한 경우에만 보내고 이메일 본문은 마크다운 기호 없이 작성합니다.
"""


# 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []




# 지시 영역

with st.form("task_form"):
    uploaded_file = st.file_uploader("텍스트 파일 업로드", type=["txt"])
    meeting_date = st.date_input("회의 날짜", value=None)
    audio_value = st.audio_input("무엇을 도와드릴까요?")
    submit = st.form_submit_button("실행")



# 버튼을 눌렀을 때만 실행
if submit:
    st.session_state.pop("mail_text", None)
    # 업로드 된 파일이 있으면 디코딩
    text = ""
    if uploaded_file is not None:
        text = uploaded_file.read().decode("utf-8")

    # 녹음이 없으면 녹음 요청
    if audio_value is None:
        st.warning("음성을 녹음해주세요.")
        st.stop()

    # 시스템 메세지
    system_content = sys_role
    if text:
        system_content += f"\n\n다음 내용을 참고하세요:\n{text}"
    input_messages = [{"role": "system", "content": system_content}]

    # STT: 음성 → 텍스트
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=("audio.wav", audio_value, "audio/wav"))

    # 사용자 메시지
    input_messages.append({"role": "user", "content": transcript.text})

    # LLM 호출 및 응답 듣기
    with st.spinner("답변을 준비하고 있습니다..."):
        # LLM 호출
        response = client.responses.create(
            model="gpt-4o-mini",
            input=input_messages
        )
        answer = response.output_text.strip()

        if response.status != "completed" or not answer:
            st.error("답변이 완료되지 않았어요. 다시 실행해주세요.")
        elif text.strip():
            # 아래 수정창과 이메일 버튼이 함께 사용하는 값
            st.session_state["mail_text"] = answer
        else:
               # 응답 출력
            st.subheader("AI 답변")
            st.write(answer)


if "mail_text" in st.session_state:
    st.subheader("회의 요약")
    st.text_area("메일로 보낼 내용을 확인하고 수정하세요", key="mail_text", height=280)

if st.button("📧 이메일 전송"):
    body = st.session_state.get("mail_text", "").strip()
    sender = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not body:
        st.warning("먼저 회의록을 요약해주세요.")
    elif not sender or not password:
        st.error("Streamlit Secrets의 Gmail 주소와 앱 비밀번호를 확인해주세요.")
    else:
        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = "회의 요약 및 김 대리 담당 업무"
            msg["From"] = sender
            msg["To"] = RECEIVER

            with st.spinner("메일을 보내고 있어요..."):
                with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                    server.starttls()
                    server.login(sender, password)
                    server.send_message(msg)

            st.success(f"{RECEIVER}로 요약 메일을 보냈어요.")

        except smtplib.SMTPAuthenticationError:
            st.error("Gmail 로그인에 실패했어요. 발신 주소와 앱 비밀번호를 확인해주세요.")
        except Exception as e:
            st.error(f"메일 전송 결과를 확인하지 못했어요. ({type(e).__name__})")

from hashlib import sha256

st.subheader("📅 구글 캘린더 일정")

task_name = st.text_input("업무 이름", key="task_name")
deadline = st.date_input("마감일 확인·수정", value=None, key="deadline")

evidence = st.session_state.get("deadline_evidence")
if evidence:
    st.caption(f"회의록 근거 · {evidence}")

if st.button("📅 일정 등록"):
    if not task_name.strip() or deadline is None:
        st.warning("업무 이름과 마감일을 확인해주세요.")
    else:
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError

            with st.spinner("구글 캘린더에 저장하고 있어요..."):
                credentials = service_account.Credentials.from_service_account_info(
                    dict(st.secrets["gcp_service_account"]),
                    scopes=["https://www.googleapis.com/auth/calendar.events"],
                )
                calendar = build(
                    "calendar", "v3",
                    credentials=credentials,
                    cache_discovery=False,
                )
                calendar_id = st.secrets["calendar"]["id"]
                event_id = sha256(
                    f"{task_name.strip()}|{deadline.isoformat()}".encode("utf-8")
                ).hexdigest()

                event = {
                    "id": event_id,
                    "summary": task_name.strip(),
                    "description": st.session_state.get("mail_text", ""),
                    "start": {"date": deadline.isoformat()},
                    "end": {"date": (deadline + timedelta(days=1)).isoformat()},
                }

                try:
                    saved = calendar.events().insert(
                        calendarId=calendar_id, body=event
                    ).execute()
                    st.success(f"{deadline}에 종일 일정을 등록했어요.")
                except HttpError as e:
                    if e.resp.status != 409:
                        raise
                    saved = calendar.events().get(
                        calendarId=calendar_id, eventId=event_id
                    ).execute()
                    st.info("같은 업무와 날짜로 이미 등록된 일정이 있어요.")

            if saved.get("htmlLink"):
                st.link_button("등록한 일정 보기", saved["htmlLink"])

        except Exception as e:
            st.error(f"캘린더 저장을 확인하지 못했어요. ({type(e).__name__})")
            status = getattr(getattr(e, "resp", None), "status", None)
            if status is not None:
                st.caption(f"Google API 응답 코드 {status}")
