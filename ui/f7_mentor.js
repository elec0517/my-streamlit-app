// ⑦ 처음 한 번 기본 대화를 만든다. 이후 직접 삭제하면 자동 복구하지 않는다.
hooks.seed=()=>{
 let seeded=false;try{seeded=localStorage.getItem("aivle-mentor-v1")==="1"}catch{}
 if(!seeded&&!Array.from(chats.values()).some(c=>c.mode==="mentor"))store(makeChat("mentor"));
 try{localStorage.setItem("aivle-mentor-v1","1")}catch{}
};
hooks.mentor=(body,c)=>{
 if(!c){body.append(button("✦ 선배에게 물어보기",()=>{
  const mentor=[...chats.values()].find(x=>x.mode==="mentor")||makeChat("mentor");store(mentor);openChat(mentor.id)}));return}
 if(c.mode!=="mentor"||c.messages.length)return;
 body.append(el("p","선배 에이블러의 경험에서 나에게 맞는 공부 방법을 찾아보세요."));
 for(const q of ["선배는 복습스터디에서 매일 한 시간을 어떻게 썼나요?","코딩 기초를 다진 다음 활용 능력을 키우려면 무엇을 연습할까요?"])
  body.append(button(q,()=>submit(q)));
};
