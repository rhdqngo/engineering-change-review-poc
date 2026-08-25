const state = {
  cases: [], topK: 0, result: null, resultMetadata: null,
  requestSequence: 0, resultController: null,
};
const $ = (selector) => document.querySelector(selector);
const humanStatus = (value) => value.replaceAll("_", " ");

async function jsonResponse(response, context) {
  const body = await response.text();
  let payload;
  try { payload = JSON.parse(body); }
  catch (_error) {
    if (!response.ok) throw new Error(`${context}: HTTP ${response.status} ${response.statusText}`);
    throw new Error(`${context}: response was not valid JSON`);
  }
  if (!response.ok) throw new Error(payload.detail || `${context}: HTTP ${response.status}`);
  return payload;
}

function compactRunId(runId) {
  return runId.replace(/^cloud-v\d+(?:-[a-z0-9]+)*-/, "");
}

function candidateResult(sourceId) {
  return state.result.candidate_results.find((item) => item.source_id === sourceId) || null;
}

function renderRetrievalScope(result = null) {
  const retrieval = result?.retrieval || {};
  const broadCount = Number.isInteger(retrieval.broad_count) && Number.isInteger(retrieval.broad_k)
    ? `${retrieval.broad_count} / ${retrieval.broad_k}` : "—";
  const expandedCount = Number.isInteger(retrieval.expanded_count)
    ? `${retrieval.expanded_count}${Number.isInteger(retrieval.relation_expansion_count) ? ` · ${retrieval.relation_expansion_count} added` : ""}` : "—";
  const finalCount = Number.isInteger(retrieval.final_k) && Array.isArray(result?.candidates)
    ? `${result.candidates.length} / ${retrieval.final_k}` : "—";
  $("#scope-broad-count").textContent = broadCount;
  $("#scope-expanded-count").textContent = expandedCount;
  $("#scope-final-count").textContent = finalCount;
  $("#scope-broad-fingerprint").textContent = retrieval.broad_candidate_fingerprint || "—";
  $("#scope-expanded-fingerprint").textContent = retrieval.expanded_pool_fingerprint || "—";
  $("#scope-final-fingerprint").textContent = retrieval.final_docket_fingerprint || result?.candidate_fingerprint || "—";
}

function showReview(sourceId, claimIndex = 0) {
  const candidate = state.result.candidates.find((item) => item.source_id === sourceId) || null;
  const result = candidateResult(sourceId);
  const claim = result?.verified_claims[claimIndex] || null;
  document.querySelectorAll("tbody tr").forEach((row) => {
    const selected = row.dataset.sourceId === sourceId;
    row.dataset.active = String(selected);
    row.querySelector("button").setAttribute("aria-pressed", String(selected));
  });
  $("#evidence-title").textContent = sourceId;
  $("#reason").textContent = claim
    ? `${humanStatus(claim.impact_type)} · ${claim.impact_claim}`
    : result?.status === "BLOCKED"
      ? "Atomic claim content is withheld by the fail-closed boundary."
      : "No supported atomic impact claim is exposed for this candidate.";
  $("#evidence").textContent = claim?.evidence_exact_text || "No verified evidence exposed.";
  $("#check-source").textContent = candidate ? "PASS" : "FAIL";
  $("#check-span").textContent = claim ? `PASS · L${claim.evidence_start_line}–L${claim.evidence_end_line}` : "—";
  $("#check-verifier").textContent = claim ? "SUPPORTED" : "—";
  $("#blocked-detail").textContent = result?.blocked_count
    ? `${result.blocked_count} withheld · ${result.blocked_stages.join(", ")}`
    : "No blocked output for this candidate.";
}

function clearResultSurface(message) {
  state.result = null;
  state.resultMetadata = null;
  $("#environment").textContent = message;
  $("#provenance-note").textContent = "No result provenance is exposed while this request is incomplete.";
  renderRetrievalScope();
  $("#fingerprint").textContent = "Final Docket seal —";
  $("#top-k").textContent = state.topK || "—";
  $("#verified-count").textContent = "—";
  $("#blocked-count").textContent = "—";
  $("#candidate-rows").replaceChildren();
  $("#evidence-title").textContent = "Result withheld";
  $("#reason").textContent = "Waiting for the selected frozen case result.";
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
  const freezeVersion = state.resultMetadata?.freeze_version || result.experiment_id || "v6 regression";
  const experimentManifest = state.resultMetadata?.experiment_manifest || result.provenance?.experiment_manifest;
  const embeddingFingerprint = state.resultMetadata?.embedding_index_fingerprint
    || result.provenance?.embedding_index_fingerprint || result.embedding_index_fingerprint;
  const identifierFingerprint = result.provenance?.identifier_index_fingerprint || result.identifier_index_fingerprint;
  const isPublished = sourceLabel === "published-evaluation";
  $("#environment").textContent = isPublished && !isFixture
    ? `PUBLISHED REGRESSION BENCHMARK · ${result.provider} · ${result.model} · ${displayRun}`
    : isPublished
      ? `PUBLISHED FIXTURE SNAPSHOT · NOT LLM EVIDENCE · ${displayRun}`
      : "DETERMINISTIC FIXTURE · NOT LLM EVIDENCE";
  $("#environment").title = publishedRunId ? `Run ${publishedRunId}` : "";
  $("#provenance-note").textContent = [
    `Frozen regression benchmark · ${freezeVersion}`,
    `run ${publishedRunId || "unknown"}`,
    sourceCommit ? `commit ${sourceCommit.slice(0, 8)}` : null,
    experimentManifest ? `manifest ${experimentManifest}` : null,
    embeddingFingerprint ? `embedding ${embeddingFingerprint.slice(0, 12)}…` : null,
    identifierFingerprint ? `identifier ${identifierFingerprint.slice(0, 12)}…` : null,
    isFixture ? "fixture, not LLM experiment evidence" : null,
  ].filter(Boolean).join(" · ");
  renderRetrievalScope(result);
  $("#fingerprint").textContent = `Final Docket seal ${result.candidate_fingerprint.slice(0, 12)}…`;
  $("#fingerprint").title = `Final ${result.candidate_fingerprint}`;
  $("#top-k").textContent = result.candidates.length;
  $("#verified-count").textContent = result.candidate_results.filter((item) => item.status === "VERIFIED_REVIEW").length;
  $("#blocked-count").textContent = result.candidate_results.reduce((total, item) => total + item.blocked_count, 0);
  const rows = $("#candidate-rows");
  rows.replaceChildren();
  result.candidates.forEach((candidate) => {
    const review = candidateResult(candidate.source_id);
    const tr = document.createElement("tr");
    tr.dataset.sourceId = candidate.source_id;
    tr.innerHTML = `<td>${String(candidate.rank).padStart(2, "0")}</td>
      <td><button class="source-button" type="button"><span class="source-id"></span><span class="source-title"></span></button></td>
      <td>${candidate.hybrid_score.toFixed(3)}</td>
      <td>${candidate.relation_score.toFixed(3)}</td>
      <td><span class="status"></span></td>`;
    tr.querySelector(".source-id").textContent = candidate.source_id;
    tr.querySelector(".source-title").textContent = candidate.title;
    const status = tr.querySelector(".status");
    status.textContent = humanStatus(review?.status || "NO_OUTPUT");
    if (review?.status === "VERIFIED_REVIEW") status.classList.add("verified");
    if (review?.status === "BLOCKED") status.classList.add("rejected");
    const button = tr.querySelector("button");
    button.setAttribute("aria-controls", "evidence-desk");
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => showReview(candidate.source_id));
    rows.append(tr);
  });
  const blocked = result.candidate_results.filter((item) => item.blocked_count);
  $("#blocked-records").replaceChildren(...(blocked.length ? blocked.map((item) => {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "blocked-record-button";
    button.textContent = `${item.source_id} · ${item.blocked_count} withheld`;
    button.addEventListener("click", () => showReview(item.source_id));
    li.append(button);
    return li;
  }) : [Object.assign(document.createElement("li"), { textContent: "No withheld records." })]));
  const preferred = result.candidate_results.find((item) => item.status === "VERIFIED_REVIEW")
    || result.candidate_results.find((item) => item.status === "BLOCKED")
    || result.candidate_results[0];
  showReview(preferred.source_id);
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
    const response = await fetch(`/api/cases/${encodeURIComponent($("#case-select").value)}/result?source=${source}`, { cache: "no-store", signal: controller.signal });
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
    $("#error").focus();
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
  $("#case-meta").textContent = `${item.id} · ${item.type} · ${item.expected_claims.length} frozen claim slot${item.expected_claims.length === 1 ? "" : "s"}`;
  $("#change-title").textContent = item.incoming_artifact.title || item.scenario;
  $("#scenario").textContent = item.scenario;
  $("#incoming-artifact-type").textContent = item.incoming_artifact.artifact_type;
  $("#incoming-artifact-title").textContent = item.incoming_artifact.title || item.incoming_artifact.subsystem || "—";
  $("#incoming-artifact-text").textContent = item.incoming_artifact.text;
  runCase();
}

async function init() {
  const runButton = $("#run-button");
  runButton.disabled = true;
  runButton.textContent = "Loading catalog";
  $("#error").hidden = true;
  try {
    const payload = await jsonResponse(await fetch("/api/cases", { cache: "no-store" }), "Case catalog service");
    if (!Array.isArray(payload.cases) || !payload.cases.length) throw new Error("Case catalog is empty");
    state.cases = payload.cases;
    state.topK = payload.top_k;
    $("#case-select").replaceChildren(...state.cases.map((item) => Object.assign(document.createElement("option"), { value: item.id, textContent: `${item.id} · ${item.type}` })));
    $("#case-select").onchange = renderCase;
    $("#source-select").onchange = runCase;
    $(".table-wrap").onkeydown = (event) => {
      const scroll = $(".table-wrap");
      if (["ArrowLeft", "ArrowRight"].includes(event.key)) {
        event.preventDefault();
        scroll.scrollBy({ left: event.key === "ArrowRight" ? 160 : -160 });
      } else if (["Home", "End"].includes(event.key)) {
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
