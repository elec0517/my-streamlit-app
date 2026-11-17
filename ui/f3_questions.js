// ③ 백서 5장·9장 FAQ. 버튼을 누르면 입력과 동일한 경로로 질문한다.
hooks.questions=(body,c)=>{
 if(c?.messages.length||c?.mode==="mentor")return;
 const group=el("div",null,"choices");
 for(const text of ["코딩 경험이 적으면 어떻게 따라가나요?","팀원의 코드를 합치기 전에 무엇을 정하면 좋을까요?"])
  group.append(button(text,()=>submit(text)));
 body.append(group);
};
