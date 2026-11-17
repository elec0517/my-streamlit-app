(async()=>{
 await restore();hooks.seed?.();render();
 const h=()=>bridge("setFrameHeight",{height:Math.max(430,(window.screen?.availHeight||780))});
 window.addEventListener("message",e=>{if(e.source===parent&&e.data?.type==="streamlit:render")receive(e.data.args?.result)});
 bridge("componentReady",{apiVersion:1});h();window.addEventListener("orientationchange",h);
 $("#composer").onsubmit=e=>{e.preventDefault();submit($("textarea").value)};
 $("textarea").onkeydown=e=>{if(e.key==="Enter"&&!e.shiftKey&&!e.isComposing){e.preventDefault();submit(e.target.value)}};
})();
