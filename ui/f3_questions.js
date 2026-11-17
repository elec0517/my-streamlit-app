

const pdfFaqCache = new WeakMap();
let previousFaqView = null;

// 현재 후보에서 중복 없이 최대 두 개 뽑기
function pickTwoQuestions(items) {
  const pool = [...new Set(items)];
  const picked = [];
  while (pool.length && picked.length < 2) {
    const index = Math.floor(Math.random() * pool.length);
    picked.push(pool.splice(index, 1)[0]);
  }
  return picked;
}

// 사용자가 채팅창에 첨부한 PDF에서 FAQ 읽기
// 업로드한 PDF에서 기존 질문을 찾고, 본문을 조합해 새 질문도 만들기
async function readUploadedFaq(file) {
  if (pdfFaqCache.has(file)) return pdfFaqCache.get(file);

  const task = (async () => {
    const base = "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/";
    const pdfjs = await import(base + "pdf.min.mjs");
    pdfjs.GlobalWorkerOptions.workerSrc = base + "pdf.worker.min.mjs";

    const bytes = Uint8Array.from(atob(file.data), ch => ch.charCodeAt(0));
    const pdf = await pdfjs.getDocument({
      data: bytes,
      isEvalSupported: false
    }).promise;

    const candidates = new Set();

    try {
      for (let n = 1; n <= pdf.numPages; n++) {
        const page = await pdf.getPage(n);
        const content = await page.getTextContent();

        // PDF의 줄바꿈을 살려 제목·질문·표의 내용이 한 줄로 섞이는 것을 줄여요.
        const pageText = content.items
          .map(item => (item.str ?? "") + (item.hasEOL ? "\n" : " "))
          .join("");

        const lines = pageText
          .split("\n")
          .map(line => line.replace(/\s+/g, " ").trim())
          .filter(Boolean);

        // PDF에서 '출 석'처럼 글자가 떨어져 추출되는 경우도 검색해요.
        const compact = pageText.replace(/\s+/g, "").toLowerCase();
        const has = word => compact.includes(word.toLowerCase());

        // 1. Q번호가 없어도 물음표로 끝나는 질문을 찾아요.
        for (const line of lines) {
          const match = line.match(/^(?:Q\s*\d{1,3}\s*[.．:：)]?\s*)?(.{4,100}?[?？])/i);
          if (match) candidates.add(match[1].trim());
        }

        // 2. 같은 페이지에서 함께 발견된 내용으로 질문을 조합해요.
        if (has("출석") || has("출결") || has("불인정")) {
          const reasons = [
            "토익", "토스", "예비군", "민방위", "면접",
            "입원", "조퇴", "외출", "결석"
          ];

          for (const reason of reasons.filter(has)) {
            candidates.add(`백서의 출결 기준에서 ‘${reason}’은 어떻게 처리되나요?`);
          }
        }

        if (has("훈련장려금") || has("훈련지원금")) {
          const benefit = has("훈련장려금") ? "훈련장려금" : "훈련지원금";
          for (const topic of ["출석률", "아르바이트", "자영업자"].filter(has)) {
            candidates.add(`백서에서 ‘${topic}’은 ${benefit} 지급 조건과 어떤 관련이 있나요?`);
          }
        }

        if (has("복습") && has("스터디")) {
          candidates.add("선배 에이블러는 복습스터디에서 그날 배운 내용을 어떻게 복습했나요?");
        }

        if (has("코드") && (has("통합") || has("협업"))) {
          candidates.add("팀원의 코드를 합칠 때 백서에서는 어떤 준비를 권하나요?");
        }

        if (has("임베딩") && has("벡터")) {
          candidates.add("백서에 나온 임베딩과 벡터 저장소는 문서 검색에서 각각 어떤 역할을 하나요?");
        }

        // 3. 위 주제에 해당하지 않는 PDF도 본문에서 질문을 만들어요.
        // 짧은 본문을 인용하므로 문서에 없는 주제를 임의로 붙이지 않아요.
        const passage = lines.find(line =>
          line.length >= 18 &&
          line.length <= 100 &&
          /[가-힣]/.test(line) &&
          /(?:다|요|함|됨)[.!]?$/.test(line) &&
          !/[?？]|https?:\/\//i.test(line)
        );

        if (passage) {
          candidates.add(`백서에서 “${passage}”라고 한 내용을 쉽게 설명해 주세요.`);
        }
      }
    } finally {
      await pdf.destroy();
    }

    return [...candidates];
  })();

  pdfFaqCache.set(file, task);

  try {
    return await task;
  } catch (error) {
    pdfFaqCache.delete(file);
    throw error;
  }
}

// ③ 현재 대화에 PDF가 있을 때만 추천 질문 표시
hooks.questions = (body, c) => {
  const attached = [...(c?.docs ?? []), ...staged];

  // 첫 화면이나 첨부를 취소한 상태에서는 추천 질문을 숨긴다.
  if (attached.length === 0) {
    previousFaqView = null;
    return;
  }

  // 이미 대화 중이면 새 PDF를 첨부했을 때만 추천을 다시 보여준다.
  if (c?.messages.length && staged.length === 0) return;

  const chatId = c?.id ?? "home";
  const group = el("div", null, "choices");
  body.append(group);

  const sameView = previousFaqView
    && previousFaqView.chatId === chatId
    && previousFaqView.files.length === attached.length
    && previousFaqView.files.every((file, i) => file === attached[i]);

  if (!sameView) {
    const selection = Promise.all(attached.map(readUploadedFaq))
      .then(lists => pickTwoQuestions(lists.flat()));

    previousFaqView = {chatId, files: attached, selection};
  }

  group.textContent = "첨부한 PDF에서 추천 질문을 찾고 있어요…";

  previousFaqView.selection.then(picked => {
    if (!group.isConnected) return;
    group.replaceChildren();

    if (picked.length === 0) {
      group.append(el("small", "추천 질문을 찾지 못했어요. 궁금한 내용을 직접 입력해 주세요."));
      return;
    }

    for (const question of picked) {
      group.append(button(question, () => submit(question)));
    }
  }).catch(() => {
    if (group.isConnected) {
      group.textContent = "PDF를 읽지 못했어요. 텍스트를 선택할 수 있는 PDF인지 확인해 주세요.";
    }
  });
};
