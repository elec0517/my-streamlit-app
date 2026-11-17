// ① 대화 레이아웃. 공통 쉘 위에 홈 또는 현재 대화 제목을 표시한다.
hooks.layout=(body,c)=>{
 if(!c){body.append(el("small","AIVLE SCHOOL   /   DX TRACK"),el("h1","오늘은 무엇을 함께 공부할까요?"),el("p","백서에서 학습 방법을 찾거나, 실습하다 막힌 부분을 물어보세요."))}
 else body.append(el("h2",c.title));
};
