const state = {
  cases: [],
  topK: 0,
  result: null,
  resultMetadata: null,
  requestSequence: 0,
  resultController: null,
};
const $ = (selector) => document.querySelector(selector);

function humanStatus(value) {
  return value.replaceAll("_", " ");
}

function compactRunId(runId) {
  return runId.replace(/^cloud-v\d+-/, "");
}

function resultFor(sourceId) {
  return state.result.final_reviews.find((item) => item.source_id === sourceId) || null;
}

function selectCandidate(sourceId) {
  const candidate = state.result.candidates.find((item) => item.source_id === sourceId);
  const review = resultFor(sourceId);
  document.querySelectorAll("tbody tr").forEach((row) => {
    const selected = row.dataset.sourceId === sourceId;
    row.dataset.active = String(selected);
    row.querySelector("button").setAttribute("aria-pressed", String(selected));
  });
  $("#evidence-title").textContent = candidate.source_id;
  $("#reason").textContent = review?.short_reason || "No review decision returned for this candidate.";
  $("#evidence").textContent = review?.status === "VERIFIED_REVIEW"
    ? review.evidence
    : "No evidence exposed.";
  $("#check-source").textContent = "PASS";
  $("#check-span").textContent = review?.evidence && review.status === "VERIFIED_REVIEW" ? "PASS" : "—";
  $("#check-verifier").textContent = review?.status === "VERIFIED_REVIEW" ? "SUPPORTED" : "—";
  $("#blocked-detail").textContent = review?.status === "REJECTED_UNSUPPORTED"
    ? `Withheld at ${review.blocked_stage}: ${review.verifier_reason || "not eligible for verifier"}`
    : "No blocked output for this candidate.";
}

function renderResult(sourceLabel) {
  const result = state.result;
  const isFixture = result.provider === "fixture-not-llm";
  const publishedRunId = state.resultMetadata?.published_run_id || result.run_id;
  const displayRun = publishedRunId ? compactRunId(publishedRunId) : "unknown run";
  const sourceCommit = state.resultMetadata?.source_commit || result.provenance?.source_commit;
  const shortCommit = sourceCommit ? sourceCommit.slice(0, 8) : null;
  const freezeVersion = state.resultMetadata?.freeze_version || result.experiment_id || "legacy freeze";
  $("#environment").textContent = sourceLabel === "saved-evaluation" && !isFixture
    ? `SAVED EVALUATION · ${result.provider} · ${result.model}`
    : sourceLabel === "published-evaluation" && !isFixture
      ? `PUBLISHED CLOUD EVALUATION · ${result.provider} · ${result.model} · ${displayRun}${shortCommit ? ` · ${shortCommit}` : ""}`
    : "DETERMINISTIC FIXTURE · NOT LLM EXPERIMENT EVIDENCE";
  $("#environment").title = !isFixture && publishedRunId ? `Published run ${publishedRunId}` : "";
  $("#provenance-note").textContent = isFixture
    ? "Fixture mode is deterministic UI/test data, never experiment evidence."
    : `Published experiment · ${freezeVersion} · run ${publishedRunId || "unknown run"}${shortCommit ? ` · commit ${shortCommit}` : ""}`;
  $("#fingerprint").textContent = `candidate seal ${result.candidate_fingerprint.slice(0, 12)}…`;
  $("#top-k").textContent = result.candidates.length;
  const verified = result.final_reviews.filter((item) => item.status === "VERIFIED_REVIEW").length;
  const blocked = result.final_reviews.filter((item) => item.status === "REJECTED_UNSUPPORTED").length;
  $("#verified-count").textContent = verified;
  $("#blocked-count").textContent = blocked;
  const rows = $("#candidate-rows");
  rows.replaceChildren();
  result.candidates.forEach((candidate) => {
    const review = resultFor(candidate.source_id);
    const tr = document.createElement("tr");
    tr.dataset.sourceId = candidate.source_id;
    const status = review?.status || "NO OUTPUT";
    tr.innerHTML = `
      <td>${String(candidate.rank).padStart(2, "0")}</td>
      <td><button class="source-button" type="button"><span class="source-id"></span><span class="source-title"></span></button></td>
      <td>${candidate.hybrid_score.toFixed(3)}</td>
      <td><span class="status">INCLUDED</span></td>
      <td><span class="status ${status === "VERIFIED_REVIEW" ? "verified" : status === "REJECTED_UNSUPPORTED" ? "rejected" : ""}">${humanStatus(status)}</span></td>`;
    tr.querySelector(".source-id").textContent = candidate.source_id;
    tr.querySelector(".source-title").textContent = candidate.title;
    const sourceButton = tr.querySelector("button");
    sourceButton.setAttribute("aria-controls", "evidence-desk");
    sourceButton.setAttribute("aria-pressed", "false");
    sourceButton.addEventListener("click", () => selectCandidate(candidate.source_id));
    rows.append(tr);
  });
  const preferred = result.final_reviews.find((item) => item.status === "VERIFIED_REVIEW")
    || result.final_reviews.find((item) => item.status === "REJECTED_UNSUPPORTED");
  selectCandidate(preferred?.source_id || result.candidates[0].source_id);
}

async function runCase() {
  const runButton = $("#run-button");
  const restoreReloadFocus = document.activeElement === runButton;
  const requestSequence = ++state.requestSequence;
  state.resultController?.abort();
  const controller = new AbortController();
  state.resultController = controller;
  $("#error").hidden = true;
  runButton.disabled = true;
  try {
    const source = $("#source-select").value;
    const response = await fetch(
      `/api/cases/${encodeURIComponent($("#case-select").value)}/result?source=${source}`,
      { cache: "no-store", signal: controller.signal },
    );
    if (!response.ok) throw new Error((await response.json()).detail || response.statusText);
    const payload = await response.json();
    if (requestSequence !== state.requestSequence) return;
    state.result = payload.result;
    state.resultMetadata = payload.result_metadata || null;
    renderResult(payload.result_source);
  } catch (error) {
    if (error.name === "AbortError" || requestSequence !== state.requestSequence) return;
    $("#error").textContent = `Result load failed: ${error.message}`;
    $("#error").hidden = false;
  } finally {
    if (requestSequence === state.requestSequence) {
      state.resultController = null;
      runButton.disabled = false;
      if (restoreReloadFocus) runButton.focus();
    }
  }
}

function renderCase() {
  const item = state.cases.find((candidate) => candidate.id === $("#case-select").value);
  $("#case-meta").textContent = `${item.id} · ${item.type} · frozen expected target ${item.expected_review_targets.join(", ") || "none"}`;
  $("#change-title").textContent = item.change_text;
  $("#scenario").textContent = item.scenario;
  runCase();
}

async function init() {
  const response = await fetch("/api/cases", { cache: "no-store" });
  const payload = await response.json();
  state.cases = payload.cases;
  state.topK = payload.top_k;
  const select = $("#case-select");
  state.cases.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = `${item.id} · ${item.type}`;
    select.append(option);
  });
  select.addEventListener("change", renderCase);
  $("#source-select").addEventListener("change", runCase);
  $("#run-button").addEventListener("click", runCase);
  renderCase();
}

init().catch((error) => {
  $("#error").textContent = `Demo initialization failed: ${error.message}`;
  $("#error").hidden = false;
});
