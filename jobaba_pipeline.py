from source import BOARD, SAMPLE, SAMPLE_BODY, FIELDS, listing, notice_body
from urllib.parse import urlsplit
import os
from llm import draft

def new_state():
    return {"mode": "", "address": "", "seen": set(), "incoming": False, "items": {}}


def action(state, name, data):
    if name == "register":
        mode = data["mode"]
        address = data["address"].strip()
        parsed = urlsplit(address)
        if (parsed.scheme, parsed.netloc, parsed.path) != ("https", "www.seongnam.go.kr", "/pm010401/list"):
            raise ValueError("성남시청 채용공고 목록 주소를 입력하세요.")
        if mode not in {"demo", "live"}:
            raise ValueError("지원하는 모드를 선택하세요.")
        if mode == "live" and not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("실제 연동 모드를 사용하려면 서버에 OPENAI_API_KEY를 설정하세요.")
        existing = set(listing(address)) if mode == "live" else set()
        state.update(mode=mode, address=address, seen=existing, incoming=False, items={})
        return f"게시판 등록 완료 · 기존 공고 {len(existing)}건 확인"
    if name == "publish" and state["mode"] == "demo":
        state["incoming"] = True
        return "시연 게시판에 공고가 올라왔어요. 다음 확인 주기에 감지해요."
    if name == "scan":
        if not state["mode"]:
            raise ValueError("게시판을 먼저 등록하세요.")
        demo = state["mode"] == "demo"
        ids = (["155167"] if state["incoming"] else []) if demo else listing(state["address"])
        pending = [item for item in ids if item not in state["seen"]]
        for item in pending[:5]:
            url = f"https://www.seongnam.go.kr/pm010401/{item}"
            body = SAMPLE_BODY if demo else notice_body(url)
            values, evidence = (
                (SAMPLE.copy(), {k: f"{k}  {v}" for k, v in SAMPLE.items()})
                if demo else draft(body)
            )
            state["items"][item] = {
                "id": item, "url": url, "body": body,
                "values": values, "evidence": evidence, "status": "검수 대기",
            }
            state["seen"].add(item)
        return f"신규 공고 {min(len(pending), 5)}건 확인"
    if name == "approve":
        item = state["items"][data["id"]]
        if item["status"] != "검수 대기":
            raise ValueError("이미 승인한 공고입니다.")
        values = {key: data["values"].get(key, "").strip() for key in FIELDS}
        if any(not value for value in values.values()):
            raise ValueError("빈 항목을 확인하고 입력한 뒤 승인하세요.")
        item.update(values=values, status="모의 승인 완료")
        return "모의 승인 완료"
    raise ValueError("사용할 수 없는 기능입니다.")

