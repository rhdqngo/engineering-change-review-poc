# 목적 중심 NASA cFS Engineering Change Impact Review

## Evidence-grounded v6 최종 요구사항

status: design-frozen-for-implementation

architecture: purpose-driven-v6

design tag: `ecr-poc-v6-design-freeze`

final tag: `ecr-poc-v6-freeze`

이 문서는 현재 런타임, 평가, UI와 배포의 최상위 요구사항이다. v1~v5는 historical offline adapter로만 보존한다. 아직 freeze되지 않은 기존 v6 구현은 별도 v7으로 분기하지 않고 이 문서에 맞는 최종 v6로 교체한다.

## 1. 목적과 해결할 문제

> 새로운 engineering artifact가 들어왔을 때, 변경되지 않은 NASA cFS 기준선에서 사람이 다시 검토해야 할 artifact를 발견하고, 검증 가능한 atomic impact claim과 정확한 원문 근거를 제공하는 fail-closed Engineering Change Impact Review Copilot을 만든다.

프로젝트가 답해야 하는 질문은 다음 하나다.

> 이 변경은 기존 engineering baseline의 어떤 artifact를 왜 다시 검토하게 만드는가?

새 Requirement, Interface, Design, Configuration, Verification 또는 Documentation artifact는 여러 source, header, configuration, EDS/XML, requirement/design 문서와 test에 영향을 줄 수 있다. 사람이 전체 baseline을 매번 탐색하기 어렵고 단순 keyword 검색은 semantic 또는 cross-artifact 관계를 놓친다. 반대로 자유로운 LLM 추론은 존재하지 않는 관계와 근거를 만들 수 있다.

따라서 시스템은 내부 후보 탐색에서는 recall을 넓히되, 사용자에게는 frozen baseline으로 입증되고 독립 검증된 atomic claim만 노출한다.

## 2. 사용자와 권한 경계

주 사용자는 cFS baseline과 engineering artifact를 이해하는 숙련 엔지니어다. 사용자는 Incoming Artifact를 제출하고, 시스템이 만든 review docket과 exact evidence를 확인한 뒤 최종 Engineering Review 판단을 내린다.

시스템은 다음을 하지 않는다.

- change 승인 또는 거부
- requirement, source, test 또는 baseline 자동 수정
- 전체 baseline에 영향이 없다는 보증
- source 밖 dependency 또는 old value 추론
- LLM 기반 autonomous orchestration, debate 또는 voting
- Knowledge Graph, Vector DB, DB, fine-tuning 또는 2-hop dependency traversal

Human Engineer가 언제나 최종 판단 주체다. `NO_SUPPORTED_REVIEW`는 전체 baseline 무영향이 아니라 평가된 candidate scope에서 supported claim을 찾지 못했다는 뜻이다.

## 3. 입력 계약

```text
IncomingArtifact
- artifact_type: requirement | interface_change | design_change |
                 configuration_change | verification_change |
                 documentation_change | other_engineering
- text: required, trimmed, 1–20,000 characters
- title: optional, max 200
- subsystem: optional, max 120
- identifiers: optional, max 20 items, each max 120
```

`text`와 사용자가 명시한 필드는 authoritative input이다. 입력의 명령문, prompt-like text, source code comment는 모두 untrusted engineering data이며 시스템 instruction으로 실행하지 않는다. Incoming Artifact는 corpus, document index 또는 identifier index에 삽입하지 않는다.

## 4. 전체 구조

```text
Incoming Engineering Artifact
        ↓
Deterministic Query Processor
        ↓
Broad Hybrid Retrieval Top-40
        ↓
Deterministic Identifier 1-Hop Expansion
        ↓
Expanded Candidate Pool max 200
        ↓
Deterministic Final Ranking
        ↓
Immutable Final Review Docket Top-10
        ↓
Engineering Reviewer — Atomic Impact Claims
        ↓
Deterministic Evidence Validator
        ↓
Independent Evidence Verifier
        ↓
Fail-Closed Verified Review Docket
        ↓
Human Engineering Review
```

Google ADK `LlmAgent`는 정확히 두 개다.

1. Engineering Reviewer
2. Evidence Verifier

Query Processor, Hybrid Retrieval, Identifier Expansion, Ranking과 Evidence Validator는 결정적 코드이며 Agent가 아니다.

## 5. NASA cFS Engineering Baseline

- NASA cFS v7.0.1 official bundle의 root commit과 recursive submodule URL/SHA를 고정한다.
- `.git`, `.github`, generated/build output, binary와 vendored dependency는 제외한다.
- C/C++ source/header, EDS/XML, configuration, requirement/design documentation과 unit test를 ingest한다.
- 원문을 재작성하지 않고 UTF-8/LF normalization, parsing, chunking, type/path/symbol/line metadata만 추가한다.
- chunk boundary는 document heading, C symbol/function, EDS/XML named element, configuration block을 우선하고 큰 block만 provider-safe line window로 분할한다.
- source ID는 `CFS::<component>::<path>::<symbol-or-lines>`를 유지한다.
- 각 chunk는 source file SHA-256, content SHA-256, absolute line range와 exact content를 가진다.
- 최종 v6 corpus는 35,515개 chunk와 현재 artifact ID, content, ordering, package hashes를 그대로 유지한다.

Artifact package와 raw source archive는 immutable GCS prefix `frozen/ecr-poc-v6`에 generation precondition으로 저장한다. v1~v5 object, tag, result와 published pointer는 변경하지 않는다.

## 6. Frozen document embedding index

- model: `gemini-embedding-001`
- task: `RETRIEVAL_DOCUMENT`
- dimensions: 768
- storage: ordered source IDs와 row-major float32 vector matrix
- runtime: document vector를 다시 생성하지 않고 memory에 한 번 적재
- live request: `RETRIEVAL_QUERY` vector만 생성하며 query vector를 disk 또는 GCS에 저장하지 않음

Index metadata는 artifact package identity, ordered source ID hash, vector SHA-256, dimension, model/task와 fingerprint를 포함한다. vector dimension, ordering, generation 또는 source package drift는 readiness/integrity를 실패시킨다.

## 7. Deterministic Query Processor

Query Processor version은 `incoming-query-v2-deterministic`으로 고정한다. LLM 또는 provider를 호출하지 않는다.

안정적인 query serialization 순서는 다음과 같다.

1. artifact type
2. title
3. subsystem
4. user identifiers
5. raw text
6. raw fields에서 결정적으로 추출한 code-like identifiers

BM25용 token은 stable deduplication을 적용하고 dense query에는 동일한 stable serialization을 사용한다. old value, dependency, relation 또는 baseline fact를 생성하지 않는다. 처리 결과에는 processor version, extracted identifiers와 query fingerprint만 남기며 raw input을 log 또는 public response에 복제하지 않는다.

## 8. Broad Hybrid Retrieval

- BM25: `k1=1.5`, `b=0.75`
- dense: frozen document vector와 live query vector cosine similarity
- normalization: corpus 전체 per-query min-max
- fusion: BM25 0.50 + dense 0.50
- broad candidate count: 40
- tie-break: hybrid score descending, source ID ascending

Broad candidate에는 lexical, dense 또는 두 origin, raw component scores, hybrid score와 broad rank를 기록한다. Broad fingerprint는 rank, source ID와 content hash를 canonical JSON으로 직렬화해 SHA-256으로 계산한다.

## 9. Deterministic Identifier Index와 1-Hop Expansion

Identifier index schema는 `engineering-identifier-index-v1`이다. entry는 exact case-sensitive `identifier`, `kind`, `scope`, document frequency와 ordered source postings를 가진다.

지원 kind:

- C/C++ function 또는 symbol
- struct/type/enum 이름
- macro 또는 configuration constant
- Message ID/MID
- command code identifier
- table identifier
- EDS/XML named element
- 명시적인 test target identifier

언어 keyword와 generic token은 제외한다. Expansion eligibility는 artifact document frequency 2 이상 50 이하인 typed identifier로 제한한다. artifact package에서 index를 두 번 만들었을 때 bytes, entry ordering, posting ordering과 SHA-256이 동일해야 한다.

Expansion seed는 다음의 합집합이다.

- Incoming Artifact의 user identifier와 deterministic extracted identifier
- Broad Top-40 candidate별 specificity 우선 최대 8개 eligible identifier

Incoming seed strength는 `1.0`, broad seed strength는 `1 / log2(broad_rank + 1)`이다. Identifier specificity는 document-frequency 기반 normalized IDF다. Candidate relation score는 해당 candidate에 도달하는 모든 직접 edge score의 최댓값이다.

추가 candidate에서 다시 identifier를 추적하지 않는다. Broad Top-40은 항상 유지하고 relation-only candidate는 relation score, hybrid score, source ID 순으로 최대 160개만 추가한다. Expanded pool 최대 크기는 200이다.

Identifier index는 extractor version, artifact package SHA-256, ordered entry/posting hash, object SHA-256, GCS generation과 fingerprint를 manifest에 고정한다. tamper, duplicate posting, unknown source ID 또는 package drift는 readiness/integrity를 실패시킨다.

## 10. Final Candidate Ranking과 docket seal

```text
final_score = 0.75 × hybrid_score + 0.25 × relation_score
```

Final ordering은 다음 순서다.

1. final score descending
2. hybrid score descending
3. source ID ascending

Expanded pool 전체에 `expanded_pool_fingerprint`, 최종 Top-10에 `final_docket_fingerprint`를 생성한다. Reviewer, deterministic validator와 Verifier가 참조하는 immutable candidate set은 Final Top-10 및 `final_docket_fingerprint`다. Reviewer가 별도 검색하거나 Final Docket 밖 source를 추가할 수 없다.

Candidate retrieval provenance는 다음을 포함한다.

```text
source_id
retrieval_origins[]: lexical | dense | relation_expansion
broad_rank: optional
relation_identifiers[]
bm25_score
embedding_score
hybrid_score
relation_score
final_score
final_rank
```

## 11. Engineering Reviewer

Reviewer는 Incoming Artifact와 immutable Final Top-10을 untrusted data로 받고 candidate마다 정확히 하나의 decision을 반환한다.

```text
REVIEW
NO_REVIEW
INSUFFICIENT_EVIDENCE
```

- `REVIEW`는 1~3개의 atomic impact claim을 요구한다.
- `NO_REVIEW`와 `INSUFFICIENT_EVIDENCE`는 claim을 허용하지 않는다.
- 요청 전체 claim은 최대 20개다.
- Final Top-10 source ID는 정확히 한 번씩 나타나야 한다.

Atomic claim은 하나의 검증 가능한 engineering assertion만 포함한다.

```text
ReviewerClaimDraft
- impact_type
- impact_claim
- evidence_exact_text
- evidence_start_line
- evidence_end_line
```

허용 impact type:

```text
REQUIREMENT_CONFLICT
INTERFACE_IMPACT
DESIGN_ASSUMPTION
CONFIGURATION_IMPACT
IMPLEMENTATION_IMPACT
VERIFICATION_IMPACT
DOCUMENTATION_IMPACT
```

Claim ID는 model이 만들지 않는다. Deterministic Validator가 Final rank와 candidate 내부 ordinal로 `CLM-<rank>-<ordinal>`을 부여한다.

## 12. Deterministic Evidence Validator

코드가 다음을 전담한다.

- decision source ID가 Final Top-10과 frozen baseline에 존재하는가
- 모든 Final candidate decision이 정확히 한 번 존재하는가
- decision/claim cardinality와 전체 claim limit이 유효한가
- impact type과 field limits가 유효한가
- evidence line range가 candidate source range 안에 있는가
- evidence exact text가 지정 line range의 원문에 contiguous span으로 존재하는가
- claim source와 evidence source가 일치하는가

실패 claim은 Verifier에 전달하지 않고 `BLOCKED`로 기록한다. Deterministic Validator는 claim의 의미적 타당성이나 누락된 engineering impact를 판단하지 않는다.

## 13. Evidence Verifier

Verifier는 결정적으로 유효한 claim을 고정 순서의 한 batch로 받는다. 입력은 Incoming Artifact, claim ID/type/text, exact source span과 최소 source metadata뿐이다. Reviewer의 장문 reasoning, confidence, 다른 candidate 또는 raw model output은 전달하지 않는다.

Verifier 질문은 두 개뿐이다.

1. evidence가 impact claim을 실제로 지지하는가
2. claim이 evidence가 허용하는 범위보다 과도하게 강한가

Verdict:

```text
SUPPORTED
REJECTED
MISSING
```

claim별 정확히 하나의 verdict가 필요하다. duplicate 또는 missing verdict는 해당 claim을 fail-closed `BLOCKED`로 처리한다.

## 14. Final 상태와 fail-closed 노출

Candidate final status:

- `VERIFIED_REVIEW`: 하나 이상의 claim이 `SUPPORTED`
- `NO_REVIEW`: Reviewer가 정상적으로 `NO_REVIEW`
- `NO_SUPPORTED_CLAIM`: 모든 valid REVIEW claim이 정상적으로 `REJECTED`
- `INSUFFICIENT_EVIDENCE`: Reviewer가 판단 근거 부족을 명시
- `BLOCKED`: schema, membership, exact evidence, duplicate/missing verdict 또는 provider 오류

Overall status:

- `REVIEW_REQUIRED`: supported claim이 하나 이상
- `INCONCLUSIVE`: supported claim 없이 blocked, missing, insufficient 또는 provider 오류가 존재
- `NO_SUPPORTED_REVIEW`: 모든 Final candidate가 정상 종결됐지만 supported claim이 없음

Verified claim과 일부 blocked result가 함께 있으면 `REVIEW_REQUIRED`, `partial=true`다. `NO_SUPPORTED_CLAIM`은 정상적인 negative verification이고 자체로 `INCONCLUSIVE`를 만들지 않는다.

Live API/UI에는 supported claim의 claim text, exact evidence와 verifier support reason만 노출한다. Rejected/missing/invalid claim의 문구와 evidence는 노출하지 않고 candidate status, blocked count, blocked stage와 verdict만 표시한다.

## 15. Live API

`POST /api/reviews`는 기존 IncomingArtifact request contract를 유지한다.

```text
LiveReviewResponse
- request_id
- baseline_id
- provider / model
- embedding model / embedding index fingerprint
- identifier index fingerprint
- query_processing
  - processor_version
  - extracted_identifiers
  - query_fingerprint
- retrieval
  - baseline_count
  - broad_k / broad_count / broad_candidate_fingerprint
  - relation_expansion_count
  - expanded_count / expanded_pool_fingerprint
  - final_k / final_docket_fingerprint
- final_docket
  - retrieval provenance and candidate final state
  - verified_claims
  - blocked count/stage
- overall_status
- partial
- retention: "not_saved"
```

Raw input은 response에 복제하지 않는다. HTTP boundary:

- invalid input: 422
- duplicate concurrent execution: 429
- document/identifier index unavailable: 503
- query embedding provider error/timeout: 502/504
- Reviewer/Verifier failure: 200 `INCONCLUSIVE`, unsupported evidence 없음

서비스는 request 하나만 동시에 처리하고 Cloud Run timeout 300초, max instance 1, concurrency 1을 유지한다. 제출 버튼 `Run engineering review · uses Vertex AI`의 클릭은 건별 billable 실행 승인이다.

## 16. UI 정보 구조

### `/` — Live Review

순서:

1. Incoming Artifact form
2. overall disposition와 evaluated scope
3. horizontally scrollable Final Top-10 docket
4. selected verified evidence 또는 fail-closed state
5. runtime/index provenance

Desktop와 390×844 narrow 모두 이 정보 순서를 유지한다. 실패 시 input을 보존하고 완료 시 result heading, 실패 시 error summary로 focus를 이동한다. `NO_SUPPORTED_REVIEW`에는 baseline 35,515, Broad 40, Expanded pool count, Final 10, verified target 0을 표시하며 무영향 표현을 사용하지 않는다.

### `/evaluation` — Frozen Regression Benchmark

20개 frozen case, retrieval stage metrics, atomic claim metrics와 provenance를 표시한다. Live Review와 동등한 tab으로 섞지 않는다. Published actual result와 fixture를 명확히 구분한다. 미관찰 성능평가로 표현하지 않는다.

## 17. 안전한 로깅과 retention

Incoming text, prompt, raw model output, rejected claim/evidence, credentials와 live result를 GCS 또는 application log에 저장하지 않는다. 구조화 로그에는 다음만 허용한다.

- request/run/case ID
- artifact type
- role
- source ID와 claim ID
- candidate decision/final status
- verifier verdict
- blocked stage
- latency
- error type
- safe fingerprint와 aggregate count

Live response retention은 `not_saved`다. 공식 evaluation result만 승인된 immutable run/publish 경로로 저장한다.

## 18. Frozen 20-case regression benchmark

Experiment identity는 `ecr-poc-regression-v6`이다. Manifest는 `ecr-poc-v6.json`, GCS는 `frozen/ecr-poc-v6`, `runs/v6`, `published/v6/demo.json`, final tag는 `ecr-poc-v6-freeze`를 사용한다.

Case distribution:

| 유형 | 수 |
| --- | ---: |
| Direct | 5 |
| Semantic | 5 |
| Cross-Artifact | 5 |
| Clean | 2 |
| Benign | 3 |

기존 Incoming Artifact text와 case ID는 유지한다. v6 current case는 legacy mutation/change field를 Agent 또는 retrieval 입력으로 사용하지 않는다.

Impact case는 실행 전에 다음을 고정한다.

```text
ExpectedClaimSlot
- claim_slot_id
- source_id
- impact_type
- acceptable_exact_evidence_spans[]
```

Expected review target는 expected claim source ID에서 파생한다. Clean/Benign은 expected claim이 없다. Claim match는 source ID, impact type과 nested/contiguous acceptable evidence span으로 결정한다.

Impact case의 unmatched verified claim은 자동 false positive로 단정하지 않고 `unregistered additional finding`으로 보고한다. 따라서 human adjudication 없는 자동 Claim Precision은 주장하지 않는다.

Metrics는 전체와 유형별로 계산한다.

- Broad Retrieval Hit@40
- Relation Expansion Gain
- Expanded Pool Target Coverage
- Final Docket Hit@10과 complete-case coverage
- Final target rank와 MRR
- expected claim proposal recall
- verified expected claim recall
- proposed/blocked/rejected/verified claim count
- average expanded pool, Final docket, verified docket size와 candidate reduction
- Clean/Benign False Alarm
- unregistered additional finding

기존 20 case는 개발 과정에서 알려진 regression/diagnostic benchmark이며 미관찰 generalization이나 preregistered unbiased 성능을 주장하지 않는다.

## 19. 검증 계약

### Data와 index

- 동일 checkout의 artifact ingest 두 회가 35,515 artifact ID/content/order/hash에서 byte-identical
- identifier index 두 회가 entry/posting/order/hash에서 byte-identical
- corpus, raw archive, vector, identifier index의 SHA/generation drift 차단
- duplicate ID/posting, unknown source, line range와 vector dimension/order 오류 차단
- Incoming Artifact가 어떤 frozen index에도 들어가지 않음

### Query와 Retrieval

- Query Processor가 LLM/provider를 호출하지 않음
- raw input과 field order에서 stable query/fingerprint 생성
- old value 또는 relation 생성 금지
- Broad Top-40, Expanded max-200, Final Top-10 결정론
- high-frequency identifier 제외, one-hop 제한, dedup/cap/tie-break 검증
- 세 fingerprint drift 감지

### Reviewer, Validator와 Verifier

- Final Top-10 decision 누락/중복과 off-docket source 차단
- invalid impact type과 candidate/total claim limit 차단
- exact span/line/source 실패 claim은 Verifier 호출 금지
- 일부 supported, 전부 rejected, 일부 blocked, duplicate/missing verdict 검증
- rejected/missing/invalid claim evidence 비노출
- provider timeout/error가 fail-closed overall status를 생성

### API, privacy와 UI

- empty/oversize identifier와 concurrent submission
- 422/429/503/502/504 및 200 `INCONCLUSIVE` 경계
- raw input/prompt/raw output/credentials/unsupported evidence의 response·log·GCS 부재
- desktop 1440×900, narrow 390×844, keyboard-only, long input, rapid switching
- review-required, no-supported-review, inconclusive, partial, index/provider error와 recovery
- verified evidence와 blocked state의 candidate switching

### Local gates

- `validate-data`
- `validate-historical` for v1~v5
- 전체 pytest
- Ruff
- mypy
- package build
- PowerShell script parsing

## 20. GCP와 승인 경계

- project: `iceu-687`
- Cloud Run region: `asia-northeast3`
- Vertex embedding location: `global`
- private service: `ecr-poc`
- evaluation Job: `ecr-poc-evaluate`
- service max instance 1, concurrency 1, timeout 300초
- dedicated web/job service accounts와 최소권한 IAM
- service-level `roles/run.invoker`, no public binding

Immutable GCS payload는 artifact package, raw archive, embedding metadata, vector matrix와 identifier index를 포함한다. 모든 upload는 generation precondition을 사용한다.

다음은 각각 실행 직전 명시적 승인을 받는다.

1. 남은 Vertex document embedding generation
2. immutable GCS payload upload
3. provisioning/deploy와 live ongoing Vertex activation
4. 공식 20-case regression Job
5. publish
6. Git push

실패 run과 checkpoint는 삭제 또는 덮어쓰지 않는다.

## 21. 완료 조건

기능 완료 조건:

- design tag/commit/document SHA와 manifest provenance 일치
- 불변 35,515 artifact corpus, embedding index와 identifier index
- deterministic Broad/Expanded/Final retrieval과 세 fingerprint
- 정확히 두 ADK Agent와 atomic claim 계약
- deterministic exact evidence validation과 independent claim verification
- fail-closed API/UI 및 safe logging
- 20/20 terminal regression case와 metric 재계산
- Live/Evaluation desktop/narrow/keyboard 실제 브라우저 검증
- private Cloud Run/GCS/IAM/Logging과 문서·코드·테스트 일치

완료 조건이 아닌 것:

- 특정 retrieval coverage, claim recall 또는 false-alarm 수치
- 자동 approval 품질
- 전체 baseline 무영향 보증

품질 수치는 frozen v6 이후 query, ranking, prompt 또는 verifier 중 한 변수만 변경한 후속 실험의 비교 지표로 사용한다.

## 22. 발표용 설명

한 문장:

> NASA cFS의 변경되지 않은 engineering baseline을 대상으로, 새로운 요구사항이나 변경사항의 잠재적 영향을 넓게 탐색하고 검증 가능한 atomic impact claim만 엔지니어에게 제공하는 fail-closed Engineering Change Impact Review Copilot이다.

발표의 중심은 Agent 수가 아니다.

```text
Broad semantic retrieval
+ deterministic engineering identifier relations
+ atomic impact review
+ deterministic citation validation
+ independent evidence verification
= human-reviewable change-impact docket
```

프로젝트는 AI가 정답을 대신 결정한다고 주장하지 않는다. 사람이 놓칠 수 있는 검토 대상을 찾고, 그 판단을 시작할 수 있는 안전하고 추적 가능한 evidence를 제공한다고 주장한다.
