
import os, json, smtplib, re
import pandas as pd
import streamlit as st
from openai import OpenAI
from email.mime.text import MIMEText

# ── 기본 설정 ─────────────────────────────────────
# 키는 환경변수에서 자동
client = OpenAI()

# 이메일 요청 시 받을 주소 (음성 인식 오류를 피하려고 코드에 고정)
MY_EMAIL = "spider379@naver.com"

# 에이블 대표 이미지 경로 (app.py와 같은 폴더에 둔 파일 이름)
IMAGE_PATH = "able.png"

# 사이드바 메뉴 (아래 셀들도 이 이름으로 화면을 나눔)
PAGES = ["🎙️ AI 비서", "📊 업무 우선순위 분석", "📅 마감 캘린더", "📨 팔로업 메일", "🎧 출근길 브리핑"]

# 대화 기록 최대 개수 (질문 1 + 답변 1 = 2개 → 10이면 최근 5번의 대화)
MAX_HISTORY = 10

# 음성용 텍스트 정리: 마크다운 기호를 빼야 TTS가 매끄럽게 읽음
def to_speech_text(text):
    text = re.sub(r"[#*`>|]", "", text)              # 제목·굵게 등 기호 제거
    text = re.sub(r"^\s*-\s*", "", text, flags=re.M)  # 줄 앞 목록 기호 '-' 제거
    return text[:4000]                                # TTS 입력 길이 한도

# 에이블 역할
sys_role = """
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
- 이메일 요청이 있으면 반드시 send_email 도구를 사용해 실제로 보냅니다. 도구를 쓰지 않고 보냈다고 말하지 않습니다.
- 받는 사람 주소는 [김 대리 이메일 주소]에 적힌 값만 사용합니다.
"""

# ── 이메일 발송 함수 (미션 1) ──
def send_email(to, subject, body):
    sender = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")

    # Secrets에 값이 없으면 연결 전에 바로 안내
    if not sender or not password:
        return {"status": "failed",
                "error": "GMAIL_ADDRESS 또는 GMAIL_APP_PASSWORD가 설정되지 않았습니다."}

    msg = MIMEText(body, "plain", "utf-8")   # 한글 본문 깨짐 방지
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to

    try:
        # 465 포트: 처음부터 SSL로 연결 (클라우드 서버에서 더 안정적)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as s:
            s.login(sender, password)
            s.sendmail(sender, to, msg.as_string())
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# ── 도구 정의 (미션 7)  ──
# description: LLM이 도구를 언제·어떻게 쓸지 판단하는 기준
tools = [{
    "type": "function",
    "name": "send_email",
    "description": "이메일을 발송합니다. 요청받은 내용은 한 통의 이메일로 모아서 보냅니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "to": {"type": "string",
                   "description": "이메일 수신자. 예: 'test@gmail.com'"},
            "subject": {"type": "string",
                        "description": "이메일 제목. 예: '마케팅 전략 초안'"},
            "body": {"type": "string",
                     "description": "이메일 본문. 회의 요약과 김 대리 담당 업무를 모두 포함하고, 마크다운 기호(#, *, -) 없이 일반 텍스트로 작성. 예: '안녕하세요, 김 대리님. 비서 에이블입니다.'"}
        },
        "required": ["to", "subject", "body"],
        "additionalProperties": False
    },
    "strict": True
}]

# ── 업무 우선순위 분석용 출력 스키마 (05 실습 JSON 구조화) ──
priority_schema = {
    "type": "json_schema",
    "name": "priority",
    "schema": {
        "type": "object",
        "properties": {
            "업무목록": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "업무명": {"type": "string"},
                        "기한": {"type": ["string", "null"]},
                        "긴급도": {"type": "string", "enum": ["높음", "낮음"]},
                        "중요도": {"type": "string", "enum": ["높음", "낮음"]},
                        "근거": {"type": "string"}
                    },
                    "required": ["업무명", "기한", "긴급도", "중요도", "근거"],
                    "additionalProperties": False
                }
            },
            "참석자별업무": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "이름": {"type": "string"},
                        "업무수": {"type": "integer"}
                    },
                    "required": ["이름", "업무수"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["업무목록", "참석자별업무"],
        "additionalProperties": False
    }
}

# 우선순위 분석 프롬프트 템플릿
priority_template = """
다음 회의록을 분석하세요.

1. 김 대리에게 배정된 업무를 모두 추출하세요.
   - 기한은 회의록에서 해당 업무에 명시된 표현 그대로 적고, 없으면 null로 하세요.
   - 긴급도: 기한이 가깝거나 회의에서 서둘러야 한다고 언급되면 '높음', 아니면 '낮음'
   - 중요도: 신제품 출시와 매출에 직접 영향을 주면 '높음', 보조 업무면 '낮음'
   - 근거: 판단 이유를 회의록 내용에 근거해 한 문장으로 쓰세요.
2. 회의 참석자(김 대리 포함)별로 새로 배정된 업무 수를 세세요.
   업무를 전달하거나 회의록을 정리하는 일은 업무로 세지 않습니다.

회의록에 없는 내용은 지어내지 마세요.

[회의록]
{meeting}
"""

# 긴급도 × 중요도 → 분류 (파이썬으로 정해서 결과 일관되게)
def classify(urgent, important):
    if urgent == "높음" and important == "높음":
        return "즉시 착수"
    elif important == "높음":
        return "순차 진행"
    else:
        return "위임 검토"

# ── 에이블에게 질문하기 (음성·텍스트 대화 공통) ──
def ask_able(question):
    """질문 → LLM 호출(이메일 도구 포함) → (답변, 이메일 발송 결과) 반환"""
    # 프롬프트: 질문 + 고정 이메일 주소 + 회의록
    prompt = f"""
{question}

[김 대리 이메일 주소]
{MY_EMAIL}

[미팅 내용]
{st.session_state.meeting_text}
"""

    # '메일'이 들어 있으면 이메일 도구를 반드시 사용, 아니면 LLM이 판단
    if "메일" in question:
        choice = {"type": "function", "name": "send_email"}
    else:
        choice = "auto"

    # 1단계: 역할 → 이전 대화(멀티턴) → 이번 질문 + 도구 정의 전달
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[{"role": "system", "content": sys_role}]
              + st.session_state.messages
              + [{"role": "user", "content": prompt}],
        tools=tools,
        tool_choice=choice,
        parallel_tool_calls=False,
        temperature=0
    )

    tool_calls = [item for item in response.output if item.type == "function_call"]
    if not tool_calls:
        return response.output_text, None

    # 2단계: LLM이 정한 인자(to, subject, body)로 이메일 함수 실행
    tool_outputs = []
    email = None
    for item in tool_calls:
        if item.name == "send_email":
            args = json.loads(item.arguments)
            result = send_email(**args)
            email = {"to": args["to"], **result}
            tool_outputs.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(result, ensure_ascii=False)
            })

    # 3단계: 실행 결과를 LLM에 돌려주고 최종 답변 받기
    final_response = client.responses.create(
        model="gpt-4o-mini",
        previous_response_id=response.id,
        input=tool_outputs,
        temperature=0
    )
    return final_response.output_text, email

# ══════════════════════════════════════════════════
# 화면 공통: 제목 · 소개 · 세션 상태 · 사이드바 메뉴
# ══════════════════════════════════════════════════
st.set_page_config(page_title="AI 개인비서 에이블", page_icon="🤖", layout="wide")
st.title("🤖 AI 개인비서 에이블")
st.caption("음성이나 대화로 질문하시면 답변해 드립니다.")

# 소개 영역: 왼쪽 이미지 / 오른쪽 역할·핵심 기능
left, right = st.columns([1, 5])
with left:
    if os.path.exists(IMAGE_PATH):
        st.image(IMAGE_PATH, width=180)
    else:
        st.info("🖼️ 이미지 준비 중")
with right:
    st.markdown("""
#### 김 대리의 AI 개인비서, 에이블
- 📝 회의록을 분석해 **요약하고 내 업무를 찾아** 드립니다.
- 🎙️ **음성이나 대화로 질문**하면 글과 음성으로 답하고, 요청 시 **이메일**로 보냅니다.
- 📅 업무 **우선순위**를 정리하고 마감일을 **캘린더**에 표시합니다.
""")
st.divider()

# 세션 상태 초기화 (S04: 처음 한 번만)
if "messages" not in st.session_state:
    st.session_state.messages = []        # 대화 히스토리 (음성·텍스트 대화 공통)
if "meeting_text" not in st.session_state:
    st.session_state.meeting_text = ""    # 업로드한 회의록 (메뉴를 옮겨도 유지)
if "notice" not in st.session_state:
    st.session_state.notice = None        # 최근 처리 결과 (인식된 질문, 이메일 발송 결과)
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None    # 최근 답변 음성
    st.session_state.play_audio = False   # 새 답변일 때만 자동 재생

# 사이드바 메뉴: 누른 메뉴의 기능만 화면에 표시
with st.sidebar:
    st.header("🤖 에이블 메뉴")
    if "🍃 오늘의 할 일" not in PAGES:
        PAGES.append("🍃 오늘의 할 일")
    page = st.radio("기능 선택", PAGES, label_visibility="collapsed")
    st.divider()

meeting_text = st.session_state.meeting_text   # 모든 메뉴에서 같은 회의록 사용
# AI 비서 화면 상단에 오늘의 할 일을 표시할 공간
today_todo_area = st.container()

# ══════════════════════════════════════════════════
# 메뉴 1: AI 비서 (회의록 · 음성 요청 · 실시간 대화)
# ══════════════════════════════════════════════════
if page == PAGES[0]:
    col_left, col_right = st.columns([1, 1], gap="large")

    # ── 왼쪽: 회의록 업로드 + 음성 요청 ──
    with col_left:
        st.subheader("📄 회의록")
        uploaded_file = st.file_uploader("회의록 파일 업로드 (txt)", type=["txt"])
        if uploaded_file is not None:
            st.session_state.meeting_text = uploaded_file.read().decode("utf-8")
            meeting_text = st.session_state.meeting_text

        if meeting_text == "":
            st.info("회의록 파일을 업로드하면 회의 내용을 바탕으로 답변합니다.")
        else:
            st.success("회의록이 준비되었습니다.")
            with st.expander("회의록 미리보기"):
                st.text_area("회의록 내용", meeting_text, height=200, label_visibility="collapsed")

        st.divider()
        st.subheader("🎙️ 음성으로 요청하기")
        audio_value = st.audio_input("무엇을 도와드릴까요?")
        voice_on = st.toggle("🔊 답변을 음성으로 듣기", value=True)
        run_voice = st.button("실행", type="primary", width="stretch")

        # 최근 처리 결과: 인식된 질문(STT 정확성 확인), 이메일 발송 결과
        notice = st.session_state.notice
        if notice:
            if notice["source"] == "voice":
                st.markdown("#### 🎙️ 인식된 질문")
                st.info(notice["question"])
            if notice["email"]:
                if notice["email"]["status"] == "success":
                    st.success(f"📧 {notice['email']['to']}(으)로 이메일을 보냈습니다.")
                else:
                    st.error(f"이메일 발송 실패: {notice['email'].get('error')}")

    # ── 오른쪽: 에이블과 실시간 대화 (음성 질문도 함께 표시) ──
    with col_right:
        st.subheader("💬 에이블과 실시간 대화")
        with st.container(height=500, border=True):
            if not st.session_state.messages:
                st.caption("아직 대화가 없습니다. 아래에 메시지를 입력하거나 음성으로 요청해 보세요.")
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # 최근 답변 음성 (새 답변일 때만 자동 재생)
        if st.session_state.last_audio:
            st.audio(st.session_state.last_audio, format="audio/mp3",
                     autoplay=st.session_state.play_audio)
            st.session_state.play_audio = False

        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_area("에이블에게 메시지 보내기",
                                      placeholder="어떤 업무를 도와드릴까요?")
            submitted = st.form_submit_button("💬 에이블에게 보내기",
                                              type="primary", width="stretch")

        if st.button("🗑️ 대화 기록 지우기", width="stretch"):
            st.session_state.messages = []
            st.session_state.notice = None
            st.session_state.last_audio = None
            st.rerun()

    # ── 질문 처리: 음성(실행 버튼) 또는 텍스트(보내기 버튼) ──
    question, source = None, None
    if run_voice:
        if audio_value is None:
            col_left.warning("먼저 마이크 버튼을 눌러 질문을 녹음해 주세요.")
        else:
            try:
                with col_left, st.spinner("음성을 인식하고 있습니다.."):
                    # STT: 녹음은 파일이 아니라 메모리 데이터 → (파일명, 바이트)로 전달
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=("recording.wav", audio_value.getvalue())
                    )
                question, source = transcript.text, "voice"
            except Exception as e:
                col_left.error(f"음성 인식 오류: {e}")
    elif submitted and user_input.strip():
        question, source = user_input.strip(), "text"

    if question:
        done = False
        try:
            with col_right, st.spinner("답변을 준비하고 있습니다.."):
                answer, email = ask_able(question)

                # 대화 히스토리 저장 (질문·답변 한 쌍씩, 최근 MAX_HISTORY개만 유지)
                st.session_state.messages.append({"role": "user", "content": question})
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.messages = st.session_state.messages[-MAX_HISTORY:]
                st.session_state.notice = {"source": source, "question": question, "email": email}

                # LLM 최종 응답을 음성으로 즉시 재생 (미션 5·6 TTS)
                if voice_on:
                    speech = client.audio.speech.create(
                        model="gpt-4o-mini-tts",
                        voice="nova",
                        input=to_speech_text(answer),
                        instructions="비서가 담당자에게 얘기하는 정중한 말투로 빠뜨리지 말고 또박또박 읽어주세요."
                    )
                    st.session_state.last_audio = speech.content
                    st.session_state.play_audio = True
            done = True
        except Exception as e:
            col_right.error(f"오류가 발생했습니다: {e}")
        if done:
            st.rerun()   # 대화창을 새 답변까지 다시 그림


# ══════════════════════════════════════════════════
# 메뉴 2: 업무 우선순위 분석 (아이젠하워 매트릭스)
# ══════════════════════════════════════════════════
if page == PAGES[1]:
    st.subheader("📊 업무 우선순위 분석")
    st.caption("업로드한 회의록에서 김 대리 업무를 긴급도 × 중요도로 분류합니다.")

    if st.button("우선순위 분석"):
        if meeting_text == "":
            st.warning("먼저 회의록 파일을 업로드해 주세요.")
        else:
            try:
                with st.spinner("업무를 분석하고 있습니다.."):
                    response = client.responses.create(
                        model="gpt-4o-mini",
                        input=[{"role": "user",
                                "content": priority_template.format(meeting=meeting_text)}],
                        text={"format": priority_schema},   # 정해진 JSON 형식으로만 답변
                        temperature=0
                    )
                    data = json.loads(response.output_text)   # JSON 문자열 → 딕셔너리

                # ── ① 업무 집중도 (R&R 밸런스) ──────────
                df_people = pd.DataFrame(data["참석자별업무"])
                kim = df_people[df_people["이름"].str.contains("김")]["업무수"].sum()
                total = df_people["업무수"].sum()

                st.markdown("#### ⚖️ 업무 집중도")
                col1, col2 = st.columns(2)
                col1.metric("김 대리 배정 업무", f"{kim}건")
                col2.metric("전체 배정 업무 중 비중",
                            f"{kim / total * 100:.0f}%" if total else "-")

                # 김 대리 업무가 3건 이상이거나 절반 이상이면 경보
                if kim >= 3 or (total and kim / total >= 0.5):
                    st.error("🚨 김 대리에게 업무가 집중되어 있습니다. 우선순위와 위임을 검토하세요.")
                else:
                    st.success("업무 배분이 적정한 수준입니다.")

                st.bar_chart(df_people.set_index("이름")["업무수"])

                # ── ② 우선순위 매트릭스 ──────────────────
                df_task = pd.DataFrame(data["업무목록"])
                df_task["기한"] = df_task["기한"].fillna("기한 미정").replace("null", "기한 미정")
                df_task["분류"] = df_task.apply(
                    lambda r: classify(r["긴급도"], r["중요도"]), axis=1)

                st.markdown("#### 🗂️ 우선순위 가이드")
                cols = st.columns(3)
                for col, group, icon in zip(cols,
                                            ["즉시 착수", "순차 진행", "위임 검토"],
                                            ["🔴", "🟡", "🔵"]):
                    col.markdown(f"**{icon} {group}**")
                    tasks = df_task[df_task["분류"] == group]
                    if tasks.empty:
                        col.caption("해당 업무 없음")
                    for _, t in tasks.iterrows():
                        col.info(f"**{t['업무명']}**\n\n⏰ {t['기한']}")

                # ── ③ 판단 근거 표 ───────────────────────
                st.markdown("#### 📋 판단 근거")
                st.dataframe(df_task[["분류", "업무명", "기한", "긴급도", "중요도", "근거"]],
                             hide_index=True)
                st.caption("※ 중요도는 회의 내용을 바탕으로 한 에이블의 판단입니다.")

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")


# ── 사이드바 아래쪽: 회의록 상태 · 저장된 대화 ──
with st.sidebar:
    st.subheader("📋 회의록 상태")
    if st.session_state.meeting_text:
        st.success("회의록 준비됨")
    else:
        st.warning("회의록 없음 · 'AI 비서' 메뉴에서 업로드")
    st.metric("저장된 대화", f"{len(st.session_state.messages) // 2}건")


# === ABLE_TODAY_PAGE ===

if page == "🍃 오늘의 할 일":
    st.subheader("🍃 오늘의 할 일")
    today = kst_today()
    st.caption(f"{today:%Y.%m.%d} · 김 대리님의 업무")

    schedule = st.session_state.get("schedule", [])

    tasks = [
        (i, item)
        for i, item in enumerate(schedule)
        if item.get("kind") == "김 대리 업무"
    ]

    if not tasks:
        st.info(
            "'📅 마감 캘린더' 메뉴에서 "
            "'회의록에서 일정 추출'을 먼저 눌러주세요."
        )

    else:
        def today_group(item):
            if not item.get("use") or not item.get("due"):
                return "🗓️ 기한 확인 필요"
            if item["due"] < today:
                return "⚠️ 기한 경과"
            if item["due"] == today:
                return "🔥 오늘 마감"
            return "📋 앞으로 할 일"

        def save_today_done(index, key):
            st.session_state.schedule[index]["done"] = (
                st.session_state[key]
            )
            # 캘린더의 완료 입력창도 새 상태로 갱신
            st.session_state.sched_ver += 1

        pending = [
            (i, item) for i, item in tasks
            if not item.get("done", False)
        ]

        done = [
            (i, item) for i, item in tasks
            if item.get("done", False)
        ]

        c1, c2, c3 = st.columns(3)
        c1.metric("남은 업무", len(pending))
        c2.metric(
            "오늘 마감",
            sum(
                today_group(item) == "🔥 오늘 마감"
                for _, item in pending
            ),
        )
        c3.metric("완료", len(done))

        version = st.session_state.get("sched_ver", 0)

        for group in [
            "⚠️ 기한 경과",
            "🔥 오늘 마감",
            "📋 앞으로 할 일",
            "🗓️ 기한 확인 필요",
        ]:
            items = [
                (i, item) for i, item in pending
                if today_group(item) == group
            ]

            if not items:
                continue

            st.markdown(f"#### {group}")

            items.sort(
                key=lambda pair: (
                    pair[1]["due"]
                    if pair[1].get("use") and pair[1].get("due")
                    else date.max
                )
            )

            for i, item in items:
                key = f"today_page_{version}_{i}"

                with st.container(border=True):
                    st.checkbox(
                        item["name"],
                        value=False,
                        key=key,
                        on_change=save_today_done,
                        args=(i, key),
                    )

                    if item.get("use") and item.get("due"):
                        st.caption(
                            f"마감일: {item['due']:%Y.%m.%d}"
                        )
                    else:
                        st.caption("정확한 마감일을 확인해주세요.")

                    if item.get("expr"):
                        st.caption(
                            f"회의록 표현: {item['expr']}"
                        )

        if not pending:
            st.success("모든 담당 업무를 완료했어요! 🎉")

        with st.expander(f"✅ 완료한 업무 {len(done)}건"):
            for i, item in done:
                key = f"today_page_done_{version}_{i}"

                st.checkbox(
                    item["name"],
                    value=True,
                    key=key,
                    on_change=save_today_done,
                    args=(i, key),
                )

            st.caption(
                "체크를 해제하면 미완료 목록으로 돌아가요."
            )
