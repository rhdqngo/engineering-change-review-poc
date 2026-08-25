from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "docs" / "presentation" / "v6-demo"


def test_v6_demo_is_one_offline_camera_stage() -> None:
    markup = (DECK / "index.html").read_text(encoding="utf-8")
    script = (DECK / "deck.js").read_text(encoding="utf-8")

    assert 'class="stage"' in markup
    assert 'class="slide ' not in markup
    assert markup.count('class="scene ') == 4
    assert script.count('{ id: "') == 22
    for removed_cue in [
        'id: "role-boundary"',
        'id: "scenario-response"',
        'id: "test-criteria"',
        'id: "final"',
        'id: "test-cases"',
        'id: "test-results"',
        'id: "test-loss"',
        'id: "test-conclusion"',
        'id: "hypothesis"',
        'id: "ai-compress"',
    ]:
        assert removed_cue not in script
    assert 'src="http' not in markup
    assert 'href="http' not in markup
    assert (DECK / "assets" / "spacecraft-light.png").is_file()
    assert (DECK / "assets" / "spacecraft-transparent.png").is_file()
    assert 'spacecraft-stage.png' not in markup


def test_v6_demo_uses_light_continuous_spacecraft_hierarchy() -> None:
    markup = (DECK / "index.html").read_text(encoding="utf-8")
    styles = (DECK / "styles.css").read_text(encoding="utf-8")

    assert '<meta name="color-scheme" content="light">' in markup
    assert 'src="assets/spacecraft-transparent.png"' in markup
    assert 'data-enter="0" data-exit="0"' in markup
    for removed in [
        "1 시스템",
        "4 역할",
        "16 기능",
        "클릭(Click)",
        "APP 01",
        "역할 1(Role)",
        "← → · Space",
    ]:
        assert removed not in markup
    assert 'class="role-legend cue-node"' not in markup
    assert markup.count('class="function-row"') == 4
    assert markup.count("<span>") >= 16
    assert "callout-links" in markup
    assert "tree-links" in markup
    assert 'color-scheme:light' in styles


def test_v6_demo_preserves_project_contract_without_removed_result_cuts() -> None:
    markup = (DECK / "index.html").read_text(encoding="utf-8")

    for expected in [
        "core Flight System",
        "<b>40</b><small>후보</small>",
        '<strong class="expansion-count">200',
        "<b>10</b><span>검토 목록</span>",
        "XART-03",
        "2 verified claims",
        "최종 판단은 Human Engineer",
        "무영향을 보증하지 않음",
        '<div class="closing cue-node" data-enter="21" data-exit="21"><h2>감사합니다</h2></div>',
    ]:
        assert expected in markup
    for removed_result in [
        "DIRECT",
        "SEMANTIC",
        "CROSS-ARTIFACT",
        "BROAD TARGET HIT",
        "CONTROL FALSE ALARM",
        "LOSS DECOMPOSITION",
        "후보 축소",
        "82.5%",
    ]:
        assert removed_result not in markup
    assert "변경 영향 시간 단축" not in markup


def test_v6_demo_has_reversible_keyboard_and_reduced_motion_contract() -> None:
    script = (DECK / "deck.js").read_text(encoding="utf-8")
    styles = (DECK / "styles.css").read_text(encoding="utf-8")
    markup = (DECK / "index.html").read_text(encoding="utf-8")

    for key in ["ArrowRight", "ArrowLeft", "PageDown", "PageUp", "Home", "End"]:
        assert key in script
    assert "history.replaceState" in script
    assert "sessionStorage" in script
    assert 'event.target.closest("button, a, input, select, textarea")' in script
    assert "prefers-reduced-motion" in styles
    assert 'id="announcer" aria-live="polite"' in markup
    assert 'aria-label="이전 장면"' in markup
    assert 'aria-label="다음 장면"' in markup


def test_v6_demo_has_concrete_opening_and_timed_system_expansion() -> None:
    markup = (DECK / "index.html").read_text(encoding="utf-8")
    script = (DECK / "deck.js").read_text(encoding="utf-8")
    styles = (DECK / "styles.css").read_text(encoding="utf-8")

    assert "Engineering Change<br><em>Impact Review Copilot</em>" in markup
    assert "cFS 변경 영향 후보를 정확한 근거와 함께 좁혀주는" in markup
    assert 'id="system-expand"' in markup
    for label in [
        "고이득 안테나",
        "별 추적기",
        "태양전지판",
        "비행 컴퓨터",
        "유도·항법·제어",
        "명령·데이터 처리",
        "전력·열 제어",
        "고장 감지·복구",
        "복잡한 시스템",
    ]:
        assert label in markup
    assert "systemExpand.addEventListener" in script
    assert "go(4, { auto: true })" in script
    assert "go(5, { auto: true })" in script
    assert "2200" in script
    assert "hierarchyStep" in script
    assert "translateX(-115vw)" in styles
    assert 'class="impact-loop cue-node"' not in markup
    assert 'class="artifact-flow cue-node"' in markup
    assert 'data-enter="8" data-exit="9" aria-label="사람이 변경을 접수하고' in markup
    assert 'class="scene scene-cfs cue-node" data-enter="6" data-exit="9"' in markup
    assert markup.count('class="flow-card') == 5
    assert 'class="bus-cycle cue-node"' not in markup
    assert 'id: "cfs-loop"' not in script
    assert 'id: "cfs-benefit"' not in script
    assert 'id: "cfs-structure", act: "architecture", mode: "bus-loop"' in script
    assert 'class="cfs-benefit cue-node" data-enter="6" data-exit="6"' in markup
    assert 'class="bus-column bus-publisher"' in markup
    assert 'class="bus-route"' in markup
    assert 'class="bus-column bus-subscribers"' in markup
    assert markup.count("이상 발생") == 3
    assert "발행 방식 변경" in markup
    assert "영향 전파" in markup
    assert "사람의 변경 검토" in markup
    assert "연관 항목 찾기" in markup
    assert 'class="ai-review-card"' in markup
    assert "AI 변경 영향 검토" in markup
    assert "LLM을 활용한다면...?" in markup
    assert 'id="beat-name"' not in markup
    for chapter in ["CHAPTER 1", "CHAPTER 2", "CHAPTER 3", "CHAPTER 4"]:
        assert chapter in markup
    for removed_english_suffix in [
        "통신(Communication)",
        "분해(Decomposition)",
        "기능<em>(Function)</em>",
        "영향 전파(Impact Propagation)",
        "사람의 변경 검토(Human Review)",
        "검색(Retrieve)",
        "결과(Result)",
    ]:
        assert removed_english_suffix not in markup
    assert "프로젝트(Project)" not in markup
    assert "card-reveal-right" in styles
    assert "fault-value-run" in styles
    assert "receiver-fault-three" in styles
    assert 'data-mode="ai-compress"' not in styles
    assert 'id: "human-process"' in script
    assert 'id: "llm-question"' in script
    assert script.index('id: "human-process"') < script.index('id: "llm-question"') < script.index('id: "pipeline"')
    assert "human-question-in" in styles
    assert "transition-delay:.82s,.82s,0s,0s" in styles
    assert "animation:human-question-in .72s cubic-bezier(.2,.8,.2,1) .82s" in styles
    assert "animation-delay:.42s" in styles
    assert "1.16s forwards" in styles
    assert "animation-delay:calc(.84s" in styles
    assert "stroke-dashoffset:0!important" in styles


def test_v6_demo_uses_plain_test_criteria_rows() -> None:
    markup = (DECK / "index.html").read_text(encoding="utf-8")
    styles = (DECK / "styles.css").read_text(encoding="utf-8")

    assert '<h2 id="test-title">테스트 기준</h2>' in markup
    assert 'class="case-spectrum cue-node"' not in markup
    assert 'class="metric-lens cue-node" data-enter="20" data-exit="20"' in markup
    criteria = markup.split('<div class="metric-lens', 1)[1].split(
        '<div class="closing', 1
    )[0]
    for label, explanation in [
        ("1차 검색", "처음 모은 40개 후보"),
        ("연관 확장", "확장된 200개 후보"),
        ("후보 압축", "최종 10개 안에 남는지"),
        ("근거 검증", "정확한 원문 근거"),
        ("오경보", "잘못된 경고가 생기지 않는지"),
    ]:
        assert label in criteria
        assert explanation in criteria
    assert criteria.count("<p>") == 5
    assert "grid-template-columns:25% 1fr" in styles
    assert ".metric-lens:before" in styles
    assert '.closing{position:absolute;inset:0;display:grid;place-items:center' in styles


def test_v6_demo_solution_flow_is_two_row_korean_sequence() -> None:
    markup = (DECK / "index.html").read_text(encoding="utf-8")
    styles = (DECK / "styles.css").read_text(encoding="utf-8")
    pipeline = markup.split('<div class="pipeline-map', 1)[1].split(
        '<div class="artifact-token', 1
    )[0]

    for label in [
        "변경 입력",
        "자연어 처리",
        "1차 검색",
        "연관 확장",
        "후보 압축",
        "영향 분석",
        "근거 확인",
        "독립 검증",
        "최종 판단",
    ]:
        assert label in pipeline
    for removed in ["Incoming", "Query", "DETERMINISTIC", "Reviewer", "Validator"]:
        assert removed not in pipeline
    assert pipeline.count("--y:43%") == 5
    assert pipeline.count("--y:69%") == 4
    assert 'class="pipeline-route-full"' in pipeline
    assert '<div class="flight-path" aria-hidden="true"></div>' in markup
    for gcp_service in [
        "Cloud Run API",
        "Vertex AI 임베딩",
        "Cloud Storage 기준 자료",
        "Google ADK · Gemini",
    ]:
        assert gcp_service in pipeline
    assert pipeline.count('class="gcp-tag"') == 5
    assert '.stage[data-mode="pipeline"] .gcp-tag' in styles
    assert '.gcp-tag{display:none}' in styles
    assert "pipeline-card-in" in styles
    assert "calc(.18s + var(--i)*.34s)" in styles
    assert ".pipeline-route-full .route-trace{stroke:var(--amber);stroke-width:4;stroke-linecap:butt" in styles


def test_v6_demo_scenario_uses_three_zone_circular_wheel() -> None:
    markup = (DECK / "index.html").read_text(encoding="utf-8")
    script = (DECK / "deck.js").read_text(encoding="utf-8")
    styles = (DECK / "styles.css").read_text(encoding="utf-8")

    assert markup.count('class="scenario-explain"') == 9
    assert markup.count('class="scenario-example"') == 9
    assert markup.count('class="scenario-meaning"') == 9
    for label in ["단계 설명", "실제 사용", "에이전트 처리", "처리 의미"]:
        assert label in markup
    assert "SAMPLE_APP의 Int2 상한 조건을 바꾸려는데" in markup
    assert "영향 후보 2건" in markup
    assert 'class="scenario-panel input-panel cue-node"' in markup
    for sentence in [
        "사용자는 바꾸려는 내용과 확인할 영향을 한 문장으로 묻는다.",
        "시스템은 질문에서 바꿀 대상, 핵심 식별자, 변경 내용을 구조화한다.",
        "같은 단어가 있는 자료와 뜻이 비슷한 자료를 함께 찾아 빠뜨릴 가능성을 줄인다.",
        "겹치거나 관련이 적은 항목을 걸러 사람이 확인할 10개만 남긴다.",
        "다른 에이전트가 같은 근거로 다시 확인해 근거 없는 판단을 걸러낸다.",
        "사용자는 확인할 코드와 시험, 그 근거를 한 번에 받아 최종 결정을 내린다.",
    ]:
        assert sentence in markup
    assert "에이전트는 질문에서" not in markup
    assert "Int2 상한 검사 추가" in markup
    assert "현재 구현 · Int1만 검사" in markup
    assert "if (TblDataPtr-&gt;Int1 &gt; SAMPLE_APP_PLATFORM_TBL_ELEMENT_1_MAX)" in markup
    assert "TblDataPtr-&gt;Int2" not in markup
    assert "변경 지점 확인" in markup
    for visual in [
        "nlp-visual",
        "search-visual",
        "expansion-visual",
        "compression-visual",
        "claim-visual",
        "evidence-visual",
        "verifier-visual",
        "response-visual",
    ]:
        assert visual in markup
    assert "process-piece-in" in styles
    assert "visual-path-draw" in styles
    assert ".zone-label{display:none}" in styles
    assert "nlp-token-in" in styles
    assert "expansion-node-in" in styles
    assert 'data-direction="forward"' in markup
    assert 'stage.dataset.direction = target > current ? "forward" : "backward"' in script
    assert 'classList.add("is-wheel-prev")' in script
    assert 'classList.add("is-wheel-next")' in script
    assert "if (activeScenario > 0)" in script
    assert "if (activeScenario < scenarioPanels.length - 1)" in script
    assert ".is-wheel-next{z-index:1;top:100%" in styles
    assert ".is-wheel-prev{z-index:1;top:0" in styles
    assert "content:attr(data-prev)" not in styles
    assert "content:attr(data-next)" not in styles
