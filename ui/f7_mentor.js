// ⑦ 현재 브라우저에 저장된 대화 전체 삭제
// ④번이 사이드바를 그린 뒤, 맨 아래에 전체 삭제 버튼을 추가한다.
const drawSidebarWithHistory = hooks.sidebar;

if (drawSidebarWithHistory) {
  hooks.sidebar = (bar, side) => {
    drawSidebarWithHistory(bar, side);

    const count = chats.size;
    if (count === 0) return;

    const deleteAllButton = button("대화 전체 삭제", async () => {
      const confirmed = window.confirm(
        `저장된 대화 ${chats.size}개를 모두 삭제할까요?\n` +
        "대화에 첨부한 파일도 함께 삭제되며, 되돌릴 수 없어요."
      );
      if (!confirmed) return;

      deleteAllButton.disabled = true;

      try {
        // 새로고침해도 삭제한 대화가 다시 나타나지 않도록 저장 기록도 비운다.
        if (db) {
          await new Promise((resolve, reject) => {
            const tx = db.transaction("chats", "readwrite");
            tx.oncomplete = resolve;
            tx.onabort = () => reject(tx.error);
            tx.objectStore("chats").clear();
          });
        }

        chats.clear();
        home();
      } catch {
        deleteAllButton.disabled = false;
        window.alert("대화 기록을 삭제하지 못했어요. 다시 시도해 주세요.");
      }
    });

    // 답변을 받거나 파일을 읽는 중에는 작업이 끝난 뒤 삭제할 수 있다.
    deleteAllButton.disabled = Boolean(pending) || busyFile;
    deleteAllButton.style.cssText = `
      width: 100%;
      margin-top: 18px;
      color: #a33737;
      border: 1px solid #e5caca;
      background: transparent;
    `;

    side.append(deleteAllButton);
  };
}
