// ⑤ 모델 호출 없이 작동하는 포춘쿠키
const fortunes=["힘내! 오늘도 한 줄부터 🥠","빈칸이 있어도 내 코드로 먼저 써 봐요.","모르는 단어 하나에 내 예시를 붙여 봐요.","오늘의 오류 하나가 내일의 힌트가 돼요."];
let fortune="",fortuneTimer;
hooks.cookie=bar=>{
 if(!$("#cookieStyle")){const s=el("style");s.id="cookieStyle";s.textContent=".cookie{margin-left:auto;border:0;background:#fff3d6;border-radius:50%;animation:bob 2.6s ease-in-out infinite;font-size:23px}.fortune{font-size:.86rem;color:#754721}@keyframes bob{50%{transform:translateY(-4px) rotate(7deg)}}@media(prefers-reduced-motion:reduce){.cookie{animation:none}}";document.head.append(s)}
 const note=el("span",fortune,"fortune");note.setAttribute("aria-live","polite");
 const b=button("🥠",()=>{const choices=fortunes.filter(x=>x!==fortune);fortune=choices[Math.floor(Math.random()*choices.length)];note.textContent=fortune;
 clearTimeout(fortuneTimer);fortuneTimer=setTimeout(()=>{fortune="";const n=$(".fortune");if(n)n.textContent=""},6500)},"오늘의 포춘쿠키 열기");b.className="cookie";bar.append(b,note);
};
