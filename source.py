import json
import os
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

BOARD = "https://www.seongnam.go.kr/pm010401/list?curPage=1"
SAMPLE_URL = "https://www.seongnam.go.kr/pm010401/155167"
FIELDS = ("공고명", "모집기관", "모집인원", "접수기간", "지원방법")
SAMPLE = dict(zip(FIELDS, (
    "분당구청 구내식당 기간제 조리원 채용", "분당구청 총무과",
    "4명", "2026-11-16 ~ 2026-11-20", "본인 방문 제출",
)))
SAMPLE_BODY = "\n".join(f"{key}  {value}" for key, value in SAMPLE.items())


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.parts = []
        self.hidden = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        if tag in {"p", "br", "li", "tr", "dd", "dt", "div"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def fetch(url, payload=None):
    headers = {"User-Agent": "Jobaba-DX-Prototype/1.0"}
    if payload is not None:
        headers.update({
            "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
            "Content-Type": "application/json",
        })
    request = Request(url, data=payload, headers=headers)
    with urlopen(request, timeout=20) as response:
        return response.read(3_000_000).decode("utf-8", errors="replace")


def listing(address):
    html = fetch(address)
    ids = list(dict.fromkeys(re.findall(r"/pm010401/(\d+)\b", html)))
    if not ids:
        raise ValueError("공고 ID를 찾지 못했습니다. 목록 페이지 구조와 접속 상태를 확인하세요.")
    return ids


def notice_body(url):
    page = Page(fetch(url))
    lines = [" ".join(line.split()) for line in "".join(page.parts).splitlines()]
    text = "\n".join(line for line in lines if line)
    start = text.find("고시공고구분")
    if start == -1:
        raise ValueError("상세 페이지에서 공고 본문 영역을 찾지 못했습니다.")
    text = text[start:].split("이 페이지에 만족하시나요")[0].strip()
    if len(text) < 80:
        raise ValueError("공고 본문 텍스트가 부족합니다.")
    return text[:14000]


