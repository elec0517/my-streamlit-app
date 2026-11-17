
const defaultFaq = ["에이블스쿨에서는무엇을배우나요?", "DX 트랙의목표는무엇인가요?", "수업은어떻게진행되나요?", "개인노트북이필요한가요?", "어떤취업지원을받을수있나요?", "코딩경험이적으면어떻게따라가나요?", "수강전에무엇을준비하면좋나요?", "용어가낯설때는어떻게하나요?", "하루에얼마나복습하나요?", "막히면답안을봐도될까요?", "배운코딩을어디에활용하나요?", "오류는어떻게질문하나요?", "팀코드를합칠때무엇을준비하나요?", "결석하면장려금에어떤영향이있나요?", "조퇴나외출도결석이되나요?", "병원방문은출석으로인정되나요?", "아르바이트를하면받을수있나요?", "자영업자도대상인가요?", "특별훈련수당도받을수있나요?", "출석률과수당은어떻게계산하나요?", "이전기수와금액이다른이유는무엇인가요?"];
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
async function readUploadedFaq(file) {
  if (pdfFaqCache.has(file)) return pdfFaqCache.get(file);

  const task = (async () => {
    const base = "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/";
    const pdfjs = await import(base + "pdf.min.mjs");
    pdfjs.GlobalWorkerOptions.workerSrc = base + "pdf.worker.min.mjs";

    const bytes = Uint8Array.from(atob(file.data), ch => ch.charCodeAt(0));
    const pdf = await pdfjs.getDocument({data: bytes, isEvalSupported: false}).promise;
    const result = [];

    try {
      for (let n = 1; n <= pdf.numPages; n++) {
        const page = await pdf.getPage(n);
        const content = await page.getTextContent();
        const text = content.items.map(item => item.str ?? "").join(" ");
        const pattern = /(?:^|[^A-Za-z0-9])Q\s*\d{1,3}\s*[.．:：)]?\s*([^?？]{2,150}?)[?？]/gi;

        for (const match of text.matchAll(pattern)) {
          result.push(match[1].replace(/\s+/g, " ").trim() + "?");
        }
      }
    } finally {
      await pdf.destroy();
    }
    return result;
  })();

  pdfFaqCache.set(file, task);
  try {
    return await task;
  } catch (error) {
    pdfFaqCache.delete(file);
    throw error;
  }
}

// ③ 추천 질문 버튼 표시
hooks.questions = (body, c) => {
  if (c?.mode === "mentor") return;
  if (c?.messages.length && staged.length === 0) return;

  const chatId = c?.id ?? "home";
  const attached = [...(c?.docs ?? []), ...staged];
  const group = el("div", null, "choices");
  body.append(group);

  // 화면만 다시 그려졌을 때는 기존 두 질문을 유지
  const sameView = previousFaqView
    && previousFaqView.chatId === chatId
    && previousFaqView.files.length === attached.length
    && previousFaqView.files.every((file, i) => file === attached[i]);

  if (!sameView) {
    const selection = attached.length
      ? Promise.all(attached.map(readUploadedFaq))
          .then(lists => pickTwoQuestions(lists.flat()))
      : Promise.resolve(pickTwoQuestions(defaultFaq));

    previousFaqView = {chatId, files: attached, selection};
  }

  group.textContent = attached.length ? "첨부한 PDF에서 추천 질문을 찾고 있어요…" : "";

  previousFaqView.selection.then(picked => {
    if (!group.isConnected) return;
    group.replaceChildren();

    if (!picked.length) {
      group.append(el("small", "이 PDF에서 FAQ를 찾지 못했어요. 궁금한 내용을 직접 입력해 주세요."));
      return;
    }
    for (const question of picked) {
      group.append(button(question, () => submit(question)));
    }
  }).catch(() => {
    if (group.isConnected) {
      group.textContent = "첨부 PDF의 추천 질문을 읽지 못했어요. 질문은 직접 입력할 수 있어요.";
    }
  });
};
