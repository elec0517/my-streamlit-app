// ⑧ 공식 문서 바로가기. 주소를 추가하면 /help에도 자동 반영된다.
const links={"/seaborn":"https://seaborn.pydata.org/","/pandas":"https://pandas.pydata.org/","/streamlit":"https://docs.streamlit.io/","/python":"https://docs.python.org/ko/3/","/scikit":"https://scikit-learn.org/","/scikitlearn":"https://scikit-learn.org/","/python":"https://docs.python.org/ko/3/","/tensorflow":"https://www.tensorflow.org/","/numpy":"https://numpy.org/",};
hooks.slash=q=>{
 if(!q.startsWith("/"))return null;
 const cmd=q.toLowerCase().trim();
 if(links[cmd])return {text:cmd.slice(1)+" 공식 문서",url:links[cmd]};
 return {text:(cmd==="/help"?"바로가기 명령어":"등록되지 않은 명령어예요. 사용 가능한 명령어")+"\n"+Object.keys(links).join("   ")};
};
$("textarea").placeholder="백서에 질문하거나 /help를 입력하세요";
