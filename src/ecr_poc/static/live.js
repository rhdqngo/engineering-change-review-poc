const $ = (selector) => document.querySelector(selector);
const form = $("#review-form");
const textInput = $("#artifact-text");
const count = $("#text-count");
const submit = $("#submit-review");
const startNew = $("#new-review");
const errorSummary = $("#form-error");
const resultSection = $("#review-result");
const resultSummary = $("#result-summary");
let activeResult = null;

const statusCopy = {
  REVIEW_REQUIRED: ["Review required", "At least one atomic impact claim passed source, exact-span, and independent verification."],
  NO_SUPPORTED_REVIEW: ["No supported review", "The Final Docket completed without a supported impact claim. This does not guarantee that the full baseline is unaffected."],
  INCONCLUSIVE: ["Inconclusive", "No supported claim is available and at least one candidate was blocked, missing, or insufficient."],
};

function resultMap() {
  return new Map(activeResult.candidate_results.map((item) => [item.source_id, item]));
}

function humanStatus(value) {
  return value.replaceAll("_", " ");
}

function cell(value) {
  return Object.assign(document.createElement("td"), { textContent: value });
}

function renderClaimButtons(candidateResult, selectClaim) {
  const list = $("#claim-list");
  list.replaceChildren();
  candidateResult.verified_claims.forEach((claim, index) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "claim-button";
    button.textContent = `${claim.claim_id} · ${humanStatus(claim.impact_type)}`;
    button.addEventListener("click", () => selectClaim(index));
    item.append(button);
    list.append(item);
  });
  list.hidden = candidateResult.verified_claims.length < 2;
}

function selectCandidate(sourceId, claimIndex = 0) {
  const candidate = activeResult.final_docket.find((item) => item.source_id === sourceId);
  const candidateResult = resultMap().get(sourceId);
  document.querySelectorAll(".candidate-button").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.sourceId === sourceId));
  });
  $("#evidence-heading").textContent = candidate.title;
  $("#evidence-source").textContent = candidate.source_id;
  $("#evidence-status").textContent = humanStatus(candidateResult?.status || "NO_DECISION");
  $("#evidence-blocked").textContent = candidateResult?.blocked_count
    ? `${candidateResult.blocked_count} · ${candidateResult.blocked_stages.join(", ")}`
    : "None";
  renderClaimButtons(candidateResult, (index) => selectCandidate(sourceId, index));
  const claim = candidateResult?.verified_claims[claimIndex] || null;
  $("#evidence-verifier").textContent = claim ? `SUPPORTED · ${claim.verifier_reason}` : "No supported claim";
  $("#evidence-reason").textContent = claim
    ? `${humanStatus(claim.impact_type)} · ${claim.impact_claim}`
    : candidateResult?.status === "BLOCKED"
      ? "Claim content was withheld by the fail-closed boundary."
      : "No verified atomic impact claim is exposed for this candidate.";
  $("#evidence-lines").textContent = claim
    ? `Lines ${claim.evidence_start_line}–${claim.evidence_end_line}`
    : "—";
  $("#evidence-span").textContent = claim?.evidence_exact_text || "No verified evidence exposed.";
}

function renderResult(result) {
  activeResult = result;
  const [heading, copy] = statusCopy[result.overall_status] || ["Unknown result", "The response did not match the current v6 contract."];
  $("#result-heading").textContent = result.partial ? `${heading} · partial` : heading;
  $("#result-copy").textContent = copy;
  resultSummary.dataset.status = result.overall_status;
  resultSummary.dataset.partial = String(result.partial);
  $("#scope-baseline").textContent = result.retrieval.baseline_count.toLocaleString();
  $("#scope-broad").textContent = `${result.retrieval.broad_count} / ${result.retrieval.broad_k}`;
  $("#scope-expanded").textContent = `${result.retrieval.expanded_count} (${result.retrieval.relation_expansion_count} added)`;
  $("#scope-final").textContent = `${result.final_docket.length} / ${result.retrieval.final_k}`;
  const decisions = resultMap();
  $("#candidate-rows").replaceChildren(...result.final_docket.map((candidate) => {
    const row = document.createElement("tr");
    const title = document.createElement("td");
    const button = document.createElement("button");
    const candidateResult = decisions.get(candidate.source_id);
    button.type = "button";
    button.className = "candidate-button source-button";
    button.dataset.sourceId = candidate.source_id;
    button.setAttribute("aria-pressed", "false");
    button.setAttribute("aria-controls", "evidence-desk");
    button.textContent = candidate.title;
    button.addEventListener("click", () => selectCandidate(candidate.source_id));
    title.append(button);
    row.append(
      cell(candidate.rank),
      title,
      cell(candidate.type),
      cell(humanStatus(candidateResult?.status || "NO_DECISION")),
      cell(candidate.final_score.toFixed(4)),
    );
    return row;
  }));
  const provenance = [
    ["Request", result.request_id],
    ["Baseline", result.baseline_id],
    ["Model", result.model],
    ["Embedding", result.embedding_model],
    ["Query processor", result.query_processing.processor_version],
    ["Query fingerprint", result.query_processing.query_fingerprint],
    ["Embedding index", result.embedding_index_fingerprint],
    ["Identifier index", result.identifier_index_fingerprint],
    ["Broad fingerprint", result.retrieval.broad_candidate_fingerprint],
    ["Expanded fingerprint", result.retrieval.expanded_pool_fingerprint],
    ["Final Docket fingerprint", result.retrieval.final_docket_fingerprint],
    ["Retention", result.retention],
  ];
  $("#provenance-list").replaceChildren(...provenance.map(([term, value]) => {
    const wrapper = document.createElement("div");
    wrapper.append(
      Object.assign(document.createElement("dt"), { textContent: term }),
      Object.assign(document.createElement("dd"), { textContent: value }),
    );
    return wrapper;
  }));
  resultSection.hidden = false;
  startNew.hidden = false;
  const preferred = result.candidate_results.find((item) => item.status === "VERIFIED_REVIEW")
    || result.candidate_results.find((item) => item.status === "BLOCKED")
    || result.candidate_results[0];
  selectCandidate(preferred.source_id);
  resultSummary.focus();
}

function identifierValues() {
  return $("#artifact-identifiers").value.split(",").map((item) => item.trim()).filter(Boolean);
}

textInput.addEventListener("input", () => {
  count.textContent = `${textInput.value.length.toLocaleString()} / 20,000`;
});

$(".table-wrap").addEventListener("keydown", (event) => {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const scroll = event.currentTarget;
  if (event.key === "Home") scroll.scrollLeft = 0;
  else if (event.key === "End") scroll.scrollLeft = scroll.scrollWidth;
  else scroll.scrollBy({ left: event.key === "ArrowRight" ? 160 : -160 });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorSummary.hidden = true;
  const identifiers = identifierValues();
  if (!textInput.value.trim()) {
    errorSummary.textContent = "Enter the incoming artifact text.";
    errorSummary.hidden = false;
    errorSummary.focus();
    return;
  }
  if (identifiers.length > 20 || identifiers.some((value) => value.length > 120)) {
    errorSummary.textContent = "Use at most 20 identifiers, each no longer than 120 characters.";
    errorSummary.hidden = false;
    errorSummary.focus();
    return;
  }
  submit.disabled = true;
  submit.textContent = "Review running…";
  try {
    const response = await fetch("/api/reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ incoming_artifact: {
        artifact_type: $("#artifact-type").value,
        text: textInput.value,
        title: $("#artifact-title").value || null,
        subsystem: $("#artifact-subsystem").value || null,
        identifiers,
      } }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || `Review failed (${response.status})`);
    renderResult(payload);
  } catch (error) {
    errorSummary.textContent = error.message;
    errorSummary.hidden = false;
    errorSummary.focus();
  } finally {
    submit.disabled = false;
    submit.textContent = "Run engineering review · uses Vertex AI";
  }
});

startNew.addEventListener("click", () => {
  form.reset();
  count.textContent = "0 / 20,000";
  resultSection.hidden = true;
  startNew.hidden = true;
  errorSummary.hidden = true;
  activeResult = null;
  textInput.focus();
});
