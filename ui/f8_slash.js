// ⑧ 슬래시 메뉴: / 입력 → 홈페이지 › → 사이트 선택
(() => {
  // 사이트를 추가하려면 이 목록에 한 줄만 추가하세요.
  const sites = [
    { name: "Seaborn",      cmd: "/seaborn",    url: "https://seaborn.pydata.org/" },
    { name: "pandas",       cmd: "/pandas",     url: "https://pandas.pydata.org/" },
    { name: "Streamlit",    cmd: "/streamlit",  url: "https://docs.streamlit.io/" },
    { name: "Python",       cmd: "/python",     url: "https://docs.python.org/ko/3/" },
    { name: "scikit-learn", cmd: "/scikit",     url: "https://scikit-learn.org/",
      aliases: ["/scikitlearn", "/scikit-learn"] },
    { name: "TensorFlow",   cmd: "/tensorflow", url: "https://www.tensorflow.org/" },
    { name: "NumPy",        cmd: "/numpy",      url: "https://numpy.org/" }
  ];

  const input = document.querySelector("#composer textarea");
  const composer = document.querySelector("#composer");

  // 입력창 바로 위에 두 메뉴를 나란히 배치
  const style = document.createElement("style");
  style.textContent = `
    #composer { position: relative; }

    #slash-menu {
      position: absolute;
      left: 0;
      bottom: calc(100% + 8px);
      z-index: 10;
      display: flex;
      align-items: flex-end;
      max-width: 100%;
    }

    #slash-menu[hidden], #slash-sites[hidden] { display: none; }

    #slash-home, #slash-sites {
      background: white;
      border: 1px solid #cbdad0;
      border-radius: 12px;
      box-shadow: 0 4px 16px #17382918;
    }

    #slash-home {
      padding: 9px 14px;
      white-space: nowrap;
      color: #254d40;
    }

    #slash-home:hover, #slash-home[aria-expanded="true"] {
      background: #e8f1e9;
    }

    #slash-sites {
      padding: 5px;
      min-width: 125px;
      max-height: min(42vh, 310px);
      overflow-y: auto;
    }

    #slash-sites a {
      display: block;
      padding: 6px 12px;
      color: #243c37;
      text-decoration: none;
      border-radius: 7px;
    }

    #slash-sites a:hover, #slash-sites a:focus-visible {
      background: #e8f1e9;
    }
  `;
  document.head.append(style);

  const menu = document.createElement("div");
  menu.id = "slash-menu";
  menu.hidden = true;

  const homeButton = button("홈페이지 ›", openSites, "학습 사이트 목록 열기");
  homeButton.id = "slash-home";
  homeButton.setAttribute("aria-controls", "slash-sites");
  homeButton.setAttribute("aria-expanded", "false");

  const siteList = document.createElement("nav");
  siteList.id = "slash-sites";
  siteList.hidden = true;
  siteList.setAttribute("aria-label", "학습 사이트");

  function openSites() {
    siteList.hidden = false;
    homeButton.setAttribute("aria-expanded", "true");
  }

  function closeSites() {
    siteList.hidden = true;
    homeButton.setAttribute("aria-expanded", "false");
  }

  function closeMenu() {
    closeSites();
    menu.hidden = true;
  }

  for (const site of sites) {
    const link = document.createElement("a");
    link.textContent = site.name;
    link.href = site.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";

    link.addEventListener("click", () => {
      input.value = "";
      closeMenu();
    });

    siteList.append(link);
  }

  menu.append(homeButton, siteList);
  composer.append(menu);

  // '/' 하나를 입력하면 홈페이지 버튼 표시
  input.addEventListener("input", () => {
    if (input.value.trim() === "/") {
      menu.hidden = false;
    } else {
      closeMenu();
    }
  });

  // 마우스는 올려서, 터치·키보드는 버튼을 눌러서 펼치기
  homeButton.addEventListener("mouseenter", openSites);
  menu.addEventListener("mouseleave", closeSites);

  document.addEventListener("pointerdown", event => {
    if (!menu.contains(event.target) && event.target !== input) closeMenu();
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !menu.hidden) {
      closeMenu();
      input.focus();
    }
  });

  // '/'에서 Enter 또는 ↓를 누르면 채팅 전송 대신 사이트 목록 열기
  input.addEventListener("keydown", event => {
    if (event.isComposing || input.value.trim() !== "/") return;
    if (event.key === "Enter" || event.key === "ArrowDown") {
      event.preventDefault();
      event.stopImmediatePropagation();
      menu.hidden = false;
      openSites();
      siteList.querySelector("a")?.focus();
    }
  }, true);

  // 기존 /seaborn, /help 등 직접 입력 방식
  hooks.slash = question => {
    const cmd = question.trim().toLowerCase();
    if (!cmd.startsWith("/")) return null;

    closeMenu();
    const site = sites.find(s => s.cmd === cmd || s.aliases?.includes(cmd));
    if (site) return { text: `${site.name} 공식 홈페이지`, url: site.url };

    const title = cmd === "/help" || cmd === "/"
      ? "사용할 수 있는 홈페이지 명령어"
      : "등록되지 않은 명령어예요. 아래에서 골라 주세요.";

    return { text: `${title}\n${sites.map(s => s.cmd).join("   ")}` };
  };

  input.placeholder = "백서에 질문하거나 /를 입력하세요";
})();
