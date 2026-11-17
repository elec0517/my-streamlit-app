// ④ 대화 목록과 선택 삭제. 삭제는 해당 대화의 첨부 자료까지 지운다.
hooks.sidebar=(bar,side)=>{
 bar.append(button("☰",()=>{sidebar=!sidebar;render()},"사이드바 열기·닫기"));
 side.append(button("접기",()=>{sidebar=false;render()}),button("＋ 새 대화",()=>{const c=makeChat();store(c);openChat(c.id)}));
 const cur=el("details");cur.append(el("summary","DX 학습 커리큘럼"),el("p","Python → 데이터 분석·시각화 → 머신러닝·딥러닝 → 생성형 AI·RAG → 서비스 구현"));side.append(cur,el("h2","대화 기록"));
 for(const c of [...chats.values()].sort((a,b)=>b.time-a.time)){
  const row=el("div",null,"row"),b=button(c.title,()=>openChat(c.id));
  if(c.id===active)b.className="selected";
  row.append(b,button("×",()=>{if(!confirm("‘"+c.title+"’ 대화를 삭제할까요?"))return;
   chats.delete(c.id);store(c,true);if(active===c.id)home();else render()},"대화 삭제 · "+c.title));side.append(row)
 }
};
