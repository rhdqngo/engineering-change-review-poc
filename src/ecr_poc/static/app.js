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

async function jsonResponse(response, context) {
  const body = await response.text();
  let payload;
  try {
    payload = JSON.parse(body);
  } catch (_error) {
    if (!response.ok) throw new Error(`${context}: HTTP ${response.status} ${response.statusText}`);
    throw new Error(`${context}: response was not valid JSON`);
  }
  if (!response.ok) throw new Error(payload.detail || `${context}: HTTP ${response.status}`);
  return payload;
}

function compactRunId(runId) {
  return runId.replace(/^cloud-v\d+-/, "");
}

function resultFor(sourceId) {
  const records = state.result.final_reviews.filter((item) => item.source_id === sourceId);
  return records.find((item) => item.status === "VERIFIED_REVIEW") || records[0] || null;
}

function showReview(sourceId, review, recordIndex = null) {
  const candidate = state.result.candidates.find((item) => item.source_id === sourceId) || null;
  document.querySelectorAll("tbody tr").forEach((row) => {
    const selected = recordIndex === null && row.dataset.sourceId === sourceId;
    row.dataset.active = String(selected);
    row.querySelector("button").setAttribute("aria-pressed", String(selected));
  });
  $("#evidence-title").textContent = recordIndex === null
    ? sourceId
    : `${sourceId} · withheld record ${recordIndex + 1}`;
  $("#reason").textContent = review?.short_reason || "No review decision returned for this candidate.";
  $("#evidence").textContent = review?.status === "VERIFIED_REVIEW"
    ? review.evidence
    : "No evidence exposed.";
  $("#check-source").textContent = candidate ? "PASS" : "FAIL";
  $("#check-span").textContent = review?.evidence && review.status === "VERIFIED_REVIEW" ? "PASS" : "—";
  $("#check-verifier").textContent = review?.status === "VERIFIED_REVIEW" ? "SUPPORTED" : "—";
  $("#blocked-detail").textContent = review?.status === "REJECTED_UNSUPPORTED"
    ? `Withheld at ${review.blocked_stage}: ${review.verifier_reason || "not eligible for verifier"}`
    : "No blocked output for this candidate.";
}

function selectCandidate(sourceId) {
  showReview(sourceId, resultFor(sourceId));
}

function clearResultSurface(message) {
  state.result = null;
  state.resultMetadata = null;
  $("#environment").textContent = message;
  $("#provenance-note").textContent = "No result provenance is exposed while this request is incomplete.";
  $("#provenance-note").removeAttribute("title");
  $("#fingerprint").textContent = "candidate seal —";
  $("#fingerprint").removeAttribute("title");
  $("#top-k").textContent = state.topK || "—";
  $("#verified-count").textContent = "—";
  $("#blocked-count").textContent = "—";
  $("#candidate-rows").replaceChildren();
  $("#evidence-title").textContent = "Result withheld";
  $("#reason").textContent = "Waiting for a result owned by the selected case and source.";
  $("#evidence").textContent = "No evidence exposed.";
  $("#check-source").textContent = "—";
  $("#check-span").textContent = "—";
  $("#check-verifier").textContent = "—";
  $("#blocked-detail").textContent = "No result record is exposed during loading or recovery.";
  $("#blocked-records").replaceChildren(Object.assign(document.createElement("li"), { textContent: "No result records exposed." }));
}

function renderResult(sourceLabel) {
  const result = state.result;
  const isFixture = result.provider === "fixture-not-llm";
  const publishedRunId = state.resultMetadata?.published_run_id || result.run_id;
  const displayRun = publishedRunId ? compactRunId(publishedRunId) : "unknown run";
  const sourceCommit = state.resultMetadata?.source_commit || result.provenance?.source_commit;
  const shortCommit = sourceCommit ? sourceCommit.slice(0, 8) : null;
  const freezeVersion = state.resultMetadata?.freeze_version || result.experiment_id || "legacy freeze";
  const experimentManifest = state.resultMetadata?.experiment_manifest
    || result.provenance?.experiment_manifest;
  const indexFingerprint = state.resultMetadata?.embedding_index_fingerprint
    || result.provenance?.embedding_index_fingerprint
    || result.embedding_index_fingerprint;
  const isPublished = ["saved-evaluation", "published-evaluation"].includes(sourceLabel);
  $("#environment").textContent = isPublished && isFixture
    ? `PUBLISHED FIXTURE SNAPSHOT · NOT LLM EXPERIMENT EVIDENCE · ${displayRun}`
    : sourceLabel === "saved-evaluation" && !isFixture
    ? `SAVED EVALUATION · ${result.provider} · ${result.model}`
    : sourceLabel === "published-evaluation" && !isFixture
      ? `PUBLISHED CLOUD EVALUATION · ${result.provider} · ${result.model} · ${displayRun}${shortCommit ? ` · ${shortCommit}` : ""}`
    : "DETERMINISTIC FIXTURE · NOT LLM EXPERIMENT EVIDENCE";
  $("#environment").title = !isFixture && publishedRunId ? `Published run ${publishedRunId}` : "";
  const provenanceText = isPublished && isFixture
    ? `Published fixture snapshot · ${freezeVersion} · run ${publishedRunId || "unknown run"}${experimentManifest ? ` · manifest ${experimentManifest}` : ""}${indexFingerprint ? ` · index ${indexFingerprint.slice(0, 12)}…` : ""} · not LLM evidence`
    : isFixture
    ? "Fixture mode is deterministic UI/test data, never experiment evidence."
    : `Published experiment · ${freezeVersion} · run ${publishedRunId || "unknown run"}${shortCommit ? ` · commit ${shortCommit}` : ""}${experimentManifest ? ` · manifest ${experimentManifest}` : ""}${indexFingerprint ? ` · index ${indexFingerprint.slice(0, 12)}…` : ""}`;
  $("#provenance-note").textContent = provenanceText;
  $("#provenance-note").title = [
    publishedRunId ? `run ${publishedRunId}` : null,
    sourceCommit ? `commit ${sourceCommit}` : null,
    experimentManifest ? `manifest ${experimentManifest}` : null,
    indexFingerprint ? `embedding index ${indexFingerprint}` : null,
  ].filter(Boolean).join(" · ");
  $("#fingerprint").textContent = `candidate seal ${result.candidate_fingerprint.slice(0, 12)}…`;
  $("#fingerprint").title = `Full candidate fingerprint: ${result.candidate_fingerprint}`;
  $("#fingerprint").setAttribute("aria-label", `Full candidate fingerprint ${result.candidate_fingerprint}`);
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
    sourceButton.addEventListener("keydown", (event) => {
      if (["Enter", " "].includes(event.key)) {
        event.preventDefault();
        selectCandidate(candidate.source_id);
      }
    });
    rows.append(tr);
  });
  const blockedRecords = result.final_reviews
    .map((review, index) => ({ review, index }))
    .filter(({ review }) => review.status === "REJECTED_UNSUPPORTED");
  const blockedList = $("#blocked-records");
  blockedList.replaceChildren();
  if (!blockedRecords.length) {
    blockedList.append(Object.assign(document.createElement("li"), { textContent: "No withheld records." }));
  } else {
    blockedRecords.forEach(({ review, index }) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "blocked-record-button";
      button.textContent = `${review.source_id} · ${review.blocked_stage || "unknown stage"}`;
      button.setAttribute("aria-label", `Inspect withheld record ${index + 1} for ${review.source_id}, stage ${review.blocked_stage || "unknown"}`);
      button.addEventListener("click", () => showReview(review.source_id, review, index));
      item.append(button);
      blockedList.append(item);
    });
  }
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
  const source = $("#source-select").value;
  clearResultSurface(source === "published" ? "PUBLISHED RESULT · LOADING" : "FIXTURE RESULT · LOADING");
  try {
    const response = await fetch(
      `/api/cases/${encodeURIComponent($("#case-select").value)}/result?source=${source}`,
      { cache: "no-store", signal: controller.signal },
    );
    const payload = await jsonResponse(response, "Result service");
    if (requestSequence !== state.requestSequence) return;
    state.result = payload.result;
    state.resultMetadata = payload.result_metadata || null;
    renderResult(payload.result_source);
  } catch (error) {
    if (error.name === "AbortError" || requestSequence !== state.requestSequence) return;
    $("#error").textContent = `Result load failed: ${error.message}`;
    $("#error").hidden = false;
    $("#environment").textContent = "RESULT UNAVAILABLE · EVIDENCE WITHHELD";
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
  $("#changed-source").textContent = item.changed_source_id;
  $("#original-content").textContent = item.original_content;
  $("#changed-content").textContent = item.changed_content;
  runCase();
}

async function init() {
  const runButton = $("#run-button");
  runButton.disabled = true;
  runButton.textContent = "Loading catalog";
  $("#error").hidden = true;
  try {
    const response = await fetch("/api/cases", { cache: "no-store" });
    const payload = await jsonResponse(response, "Case catalog service");
    if (!Array.isArray(payload.cases) || !payload.cases.length) throw new Error("Case catalog is empty");
    state.cases = payload.cases;
    state.topK = payload.top_k;
    const select = $("#case-select");
    select.replaceChildren();
    state.cases.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = `${item.id} · ${item.type}`;
      select.append(option);
    });
    select.onchange = renderCase;
    $("#source-select").onchange = runCase;
    $(".table-wrap").onkeydown = (event) => {
      const scroll = $(".table-wrap");
      if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
        event.preventDefault();
        scroll.scrollBy({ left: event.key === "ArrowRight" ? 160 : -160 });
      } else if (event.key === "Home" || event.key === "End") {
        event.preventDefault();
        scroll.scrollLeft = event.key === "Home" ? 0 : scroll.scrollWidth;
      }
    };
    runButton.onclick = runCase;
    runButton.textContent = "Reload result";
    runButton.disabled = false;
    renderCase();
  } catch (error) {
    clearResultSurface("CASE CATALOG UNAVAILABLE · EVIDENCE WITHHELD");
    $("#error").textContent = `Case catalog load failed: ${error.message}. Retry when the service is ready.`;
    $("#error").hidden = false;
    runButton.textContent = "Retry catalog";
    runButton.onclick = init;
    runButton.disabled = false;
  }
}

init();
