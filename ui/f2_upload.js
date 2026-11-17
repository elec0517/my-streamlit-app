// ② 입력창 왼쪽 + 및 드롭. 첨부 파일은 현재 대화에만 유지한다.
hooks.upload=()=>{
 const row=$("#composeRow"),box=$("#composer"),list=$("#files");
 if(!$("#attach")){
  const input=el("input");input.type="file";input.accept=".pdf,application/pdf";input.multiple=true;input.hidden=true;
  const b=button("＋",()=>input.click(),"PDF 첨부");b.id="attach";row.prepend(b,input);
  async function attach(files){
   if(busyFile||pending)return;
   const target=active;busyFile=true;notice="PDF를 읽는 중이에요.";render();
   try{
    const incoming=Array.from(files);
    if(incoming.some(f=>!f.name.toLowerCase().endsWith(".pdf")||f.size>5*1024*1024))throw Error("파일당 5MB 이하 PDF를 선택해 주세요.");
    const loaded=[];
    for(const f of incoming){
     const data=await new Promise((ok,no)=>{const r=new FileReader();r.onload=()=>ok(r.result.split(",")[1]);r.onerror=no;r.readAsDataURL(f)});
     loaded.push({name:f.name,data});
    }
    if(active!==target)return;
    const seen=new Set([...(current()?.docs||[]),...staged].map(d=>d.data));
    const extra=loaded.filter(d=>{if(seen.has(d.data))return false;seen.add(d.data);return true});
    if(seen.size>3)throw Error("한 대화에 PDF를 3개까지 첨부할 수 있어요.");
    staged.push(...extra);notice="";
   }catch(e){notice=e.message||"파일을 다시 선택해 주세요."}finally{busyFile=false;input.value="";render()}
  }
  input.onchange=()=>attach(input.files);
  box.ondragover=e=>{e.preventDefault();box.classList.add("drag")};
  box.ondragleave=()=>box.classList.remove("drag");
  box.ondrop=e=>{e.preventDefault();box.classList.remove("drag");attach(e.dataTransfer.files)};
 }
 list.replaceChildren();
 for(const doc of current()?.docs||[])list.append(el("small","📄 "+doc.name+"　"));
 for(const doc of staged)list.append(button("📎 "+doc.name+" ×",()=>{staged=staged.filter(d=>d!==doc);render()},"첨부 취소 "+doc.name));
};
