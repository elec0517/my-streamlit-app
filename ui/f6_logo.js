
// ⑥ AIVLE 로고를 누르면 홈으로 이동
hooks.logo = bar => {
  const logoButton = button("", home, "AIVLE 홈으로");

  const logo = new Image();
  logo.src = "./logo.png";
  logo.alt = "AIVLE";
  logo.style.cssText = "display:block; width:132px; max-width:32vw; height:auto;";

  logoButton.style.cssText = "padding:2px 6px; border:0; background:transparent;";
  logoButton.append(logo);
  bar.append(logoButton);
};
