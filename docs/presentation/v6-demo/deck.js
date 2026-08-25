(() => {
  const beats = [
    { id: "space", act: "problem", mode: "cosmos", name: "Engineering Change Impact Review Copilot" },
    { id: "spacecraft", act: "problem", mode: "spacecraft", name: "우주선" },
    { id: "spacecraft-systems", act: "problem", mode: "systems", name: "우주선을 이루는 시스템" },
    { id: "flight-software", act: "problem", mode: "avionics", name: "비행 소프트웨어 · 선택" },
    { id: "system-artifacts", act: "problem", mode: "hierarchy", name: "비행 소프트웨어 역할" },
    { id: "system-question", act: "problem", mode: "hierarchy", name: "세부 기능" },
    { id: "cfs-structure", act: "architecture", mode: "bus-loop", name: "cFS 정상 발행·전달·구독", source: "Source: NASA GSFC core Flight System architecture" },
    { id: "change", act: "architecture", mode: "change", name: "발행 방식 변경과 수신 이상" },
    { id: "human-process", act: "architecture", mode: "human-process", name: "사람의 변경 영향 검토" },
    { id: "llm-question", act: "architecture", mode: "question", name: "LLM을 활용한다면" },
    { id: "pipeline", act: "solution", mode: "pipeline", name: "전체 해결 구조" },
    { id: "scenario-input", act: "solution", mode: "scenario-input", focus: "input", token: [14, 17], name: "XART-03 Incoming Artifact", source: "Source: frozen v6-r1 case XART-03" },
    { id: "scenario-query", act: "solution", mode: "scenario-query", focus: "query", token: [14, 25.2], name: "결정적 Query Processor" },
    { id: "scenario-broad", act: "solution", mode: "scenario-broad", focus: "broad", token: [14, 33.4], name: "Broad Hybrid Top-40" },
    { id: "scenario-expanded", act: "solution", mode: "scenario-expanded", focus: "expanded", token: [14, 41.6], name: "Identifier 1-hop Expanded 200" },
    { id: "scenario-final", act: "solution", mode: "scenario-final", focus: "final", token: [14, 49.8], name: "Final Review Docket Top-10" },
    { id: "scenario-reviewer", act: "solution", mode: "scenario-reviewer", focus: "reviewer", token: [14, 58], name: "Engineering Reviewer" },
    { id: "scenario-validator", act: "solution", mode: "scenario-validator", focus: "validator", token: [14, 66.2], name: "Exact-evidence Validator" },
    { id: "scenario-verifier", act: "solution", mode: "scenario-verifier", focus: "verifier", token: [14, 74.4], name: "Independent Evidence Verifier" },
    { id: "scenario-human", act: "solution", mode: "scenario-human", focus: "human", token: [14, 82.6], name: "Human Engineer 응답" },
    { id: "test-lens", act: "test", mode: "test-lens", name: "단계별 평가 기준" },
    { id: "closing", act: "test", mode: "closing", name: "감사합니다" }
  ];

  const stage = document.querySelector("#stage");
  const previous = document.querySelector("#prev");
  const next = document.querySelector("#next");
  const progress = document.querySelector("#progress");
  const announcer = document.querySelector("#announcer");
  const sourceLine = document.querySelector("#source-line");
  const systemExpand = document.querySelector("#system-expand");
  const nodes = Array.from(document.querySelectorAll(".cue-node"));
  const scenes = Array.from(document.querySelectorAll(".scene"));
  const scenarioPanels = Array.from(document.querySelectorAll(".scenario-panel"));
  const storageKey = "ecr-v6-flightpath-cue";
  let current = 0;
  let hierarchyTimers = [];

  function clearHierarchyTimers() {
    hierarchyTimers.forEach((timer) => window.clearTimeout(timer));
    hierarchyTimers = [];
    stage.classList.remove("is-auto-expanding");
    systemExpand.disabled = false;
  }

  function cueFromHash() {
    const requested = decodeURIComponent(window.location.hash.slice(1));
    const index = beats.findIndex((beat) => beat.id === requested);
    return index >= 0 ? index : 0;
  }

  function isVisible(node, index) {
    const enter = Number.parseInt(node.dataset.enter || "0", 10);
    const exit = Number.parseInt(node.dataset.exit || String(beats.length - 1), 10);
    return index >= enter && index <= exit;
  }

  function render({ announce = true, curtain = false } = {}) {
    const beat = beats[current];
    stage.dataset.mode = beat.mode;
    stage.dataset.act = beat.act;
    stage.dataset.focus = beat.focus || "none";
    stage.dataset.hierarchyStep = current < 4 ? "root" : current < 5 ? "roles" : "functions";
    systemExpand.setAttribute("aria-expanded", current >= 4 ? "true" : "false");
    if (!stage.classList.contains("is-auto-expanding")) systemExpand.disabled = current !== 3;
    if (beat.token) {
      stage.style.setProperty("--token-x", `${beat.token[0]}%`);
      stage.style.setProperty("--token-y", `${beat.token[1]}%`);
    }
    nodes.forEach((node) => node.classList.toggle("is-visible", isVisible(node, current)));
    scenarioPanels.forEach((panel) => panel.classList.remove("is-wheel-prev", "is-wheel-next"));
    const activeScenario = scenarioPanels.findIndex((panel) => isVisible(panel, current));
    if (activeScenario >= 0) {
      if (activeScenario > 0) scenarioPanels[activeScenario - 1].classList.add("is-wheel-prev");
      if (activeScenario < scenarioPanels.length - 1) scenarioPanels[activeScenario + 1].classList.add("is-wheel-next");
    }
    scenes.forEach((scene) => scene.setAttribute("aria-hidden", isVisible(scene, current) ? "false" : "true"));
    previous.disabled = current === 0;
    next.disabled = current === beats.length - 1;
    progress.style.width = `${((current + 1) / beats.length) * 100}%`;
    sourceLine.textContent = beat.source || (beat.act === "test" && beat.mode !== "closing" ? "Source: immutable v6-r1 regression result" : "");
    sourceLine.hidden = !sourceLine.textContent;
    const expectedHash = `#${beat.id}`;
    if (window.location.hash !== expectedHash) history.replaceState(null, "", expectedHash);
    try { sessionStorage.setItem(storageKey, beat.id); } catch { /* Presentation remains usable without storage. */ }
    if (curtain) {
      stage.classList.remove("is-clearing");
      void stage.offsetWidth;
      stage.classList.add("is-clearing");
    }
    if (announce) announcer.textContent = `${beat.name}. ${current + 1}번째 진행 상태.`;
  }

  function go(index, { auto = false } = {}) {
    if (!auto) clearHierarchyTimers();
    const target = Math.max(0, Math.min(index, beats.length - 1));
    if (target === current) return;
    stage.dataset.direction = target > current ? "forward" : "backward";
    const curtain = beats[target].act !== beats[current].act;
    current = target;
    render({ curtain });
  }

  previous.addEventListener("click", () => go(current - 1));
  next.addEventListener("click", () => go(current + 1));
  systemExpand.addEventListener("click", () => {
    if (current !== 3) return;
    clearHierarchyTimers();
    stage.classList.add("is-auto-expanding");
    systemExpand.disabled = true;
    go(4, { auto: true });
    hierarchyTimers.push(window.setTimeout(() => {
      go(5, { auto: true });
      hierarchyTimers = [];
      stage.classList.remove("is-auto-expanding");
      systemExpand.disabled = true;
      systemExpand.focus({ preventScroll: true });
    }, 2200));
  });
  window.addEventListener("keydown", (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key === " " && event.target.closest("button, a, input, select, textarea")) return;
    if (["ArrowRight", "PageDown", " "].includes(event.key)) { event.preventDefault(); go(current + 1); }
    else if (["ArrowLeft", "PageUp", "Backspace"].includes(event.key)) { event.preventDefault(); go(current - 1); }
    else if (event.key === "Home") { event.preventDefault(); go(0); }
    else if (event.key === "End") { event.preventDefault(); go(beats.length - 1); }
  });
  window.addEventListener("hashchange", () => {
    const index = cueFromHash();
    if (index !== current) {
      clearHierarchyTimers();
      stage.dataset.direction = index > current ? "forward" : "backward";
      current = index;
      render();
    }
  });

  current = cueFromHash();
  if (!window.location.hash) {
    try {
      const saved = sessionStorage.getItem(storageKey);
      const savedIndex = beats.findIndex((beat) => beat.id === saved);
      if (savedIndex >= 0) current = savedIndex;
    } catch { /* ignore */ }
  }
  render({ announce: false });
})();
