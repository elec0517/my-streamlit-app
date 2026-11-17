"use strict";
const $=s=>document.querySelector(s), hooks={}, chats=new Map();
let active=null, pending=null, db, staged=[], busyFile=false, sidebar=innerWidth>690, notice="";
const uid=()=>crypto.randomUUID();
function el(tag,text,cls){const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n}
function button(text,fn,title){const b=el("button",text);b.type="button";b.onclick=fn;if(title){b.title=title;b.setAttribute("aria-label",title)}return b}
function current(){return chats.get(active)}
function makeChat(mode="normal"){const c={id:uid(),mode,title:mode==="mentor"?"선배에게 물어보기":"새 대화",messages:[],docs:[],time:Date.now()};chats.set(c.id,c);return c}
function openChat(id){active=id;staged=[];notice="";$("textarea").value="";if(innerWidth<690)sidebar=false;render()}
function home(){openChat(null)}
function store(c,remove=false){
 if(!db)return;
 const tx=db.transaction("chats","readwrite"), s=tx.objectStore("chats");
 if(remove)s.delete(c.id);else s.put(c);
 tx.onerror=()=>{$("#status").textContent="브라우저 저장 공간이 부족해 이번 변경을 저장하지 못했어요."};
}
async function restore(){
 try{db=await new Promise((ok,no)=>{const r=indexedDB.open("aivle-study-v1",1);r.onupgradeneeded=()=>r.result.createObjectStore("chats",{keyPath:"id"});r.onsuccess=()=>ok(r.result);r.onerror=()=>no(r.error)});
 const rows=await new Promise((ok,no)=>{const r=db.transaction("chats").objectStore("chats").getAll();r.onsuccess=()=>ok(r.result);r.onerror=()=>no(r.error)});
 rows.forEach(c=>chats.set(c.id,c));}catch{notice="이 브라우저에서는 현재 세션 동안만 대화가 유지돼요."}
}
function bridge(type,payload={}){parent.postMessage({isStreamlitMessage:true,type:"streamlit:"+type,...payload},"*")}
function message(body,m){const box=el("article",m.text,"msg "+(m.role==="user"?"user":"bot"));body.append(box);
 if(m.url){const a=el("a","공식 홈페이지 열기 ↗");a.href=m.url;a.target="_blank";a.rel="noopener noreferrer";box.append(el("br"),a)}
 if(m.refs?.length){const d=el("details");d.append(el("summary","검색한 자료"),el("small",m.refs.join("\n")));box.append(d)}}
function render(){
 const bar=$("header"),side=$("aside"),body=$("#body");bar.replaceChildren();side.replaceChildren();body.replaceChildren();
 side.hidden=!sidebar||!hooks.sidebar;hooks.sidebar?.(bar,side);hooks.logo?.(bar);
 const c=current();hooks.layout?.(body,c);hooks.questions?.(body,c);hooks.mentor?.(body,c);
 for(const m of c?.messages||[])message(body,m);
 if(pending?.chat===active && pending){const n=el("p","답변을 입력 중입니다…","loading");n.setAttribute("role","status");body.append(n)}
 hooks.cookie?.(bar);hooks.upload?.();$("#status").textContent=notice;
 $(".send").disabled=!!pending||busyFile;
 if(c?.messages.length)body.scrollTop=body.scrollHeight;
}
function submit(text){
 text=text.trim();if(pending||busyFile||(!text&&!staged.length))return;
 const c=current()||makeChat();active=c.id;
 for(const doc of staged)if(!c.docs.some(d=>d.data===doc.data))c.docs.push(doc);
 staged=[];$("textarea").value="";notice="";
 if(!text){notice="PDF를 첨부했어요. 궁금한 점을 입력해 주세요.";store(c);render();return}
 const history=c.messages.filter(m=>!m.local).slice(-8).map(({role,text})=>({role,text}));
 c.messages.push({role:"user",text});if(c.messages.length===1&&c.mode==="normal")c.title=text.slice(0,30);c.time=Date.now();
 const local=hooks.slash?.(text);
 if(local){c.messages.at(-1).local=true;c.messages.push({role:"assistant",local:true,...local});store(c);render();return}
 pending={id:uid(),chat:c.id};store(c);render();
 bridge("setComponentValue",{dataType:"json",value:{...pending,question:text,history,files:c.docs}});
}
function receive(r){
 if(!pending||r?.id!==pending.id)return;
 const c=chats.get(pending.chat);pending=null;
 if(c){c.messages.push({role:"assistant",text:r.error||r.text,refs:r.refs,local:!!r.error});store(c)}render();
}
