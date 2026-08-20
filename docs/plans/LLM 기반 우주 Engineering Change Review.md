# LLM 기반 우주 Engineering Change Review의 추가 가치 검증

## Evaluation-Aligned Scoped Proof-of-Concept

**영문 제목**  
**Evaluating the Added Value of LLM-Assisted Engineering Change Review on NASA Space Engineering Artifacts**

---

## 1. 프로젝트 정의

본 프로젝트는 NASA 공개 우주 engineering artifact를 이용해 **Engineering Change Review 과정에 LLM 기반 semantic review를 추가했을 때 실제로 추가적인 가치가 있는지 확인하는 소규모 proof-of-concept**이다.

핵심 질문은 하나다.

> **Engineering change가 주어졌을 때, Hybrid Retrieval이 제공한 동일한 Top-K candidate 안에서 LLM semantic review를 추가하면 실제 검토가 필요한 artifact를 효과적으로 선별하고, 그 판단을 evidence와 함께 제시할 수 있는가?**

본 프로젝트는 새로운 LLM 모델을 제안하거나 실제 우주 산업 현장에 바로 적용 가능한 시스템을 만드는 것이 목적이 아니다. 또한 LLM이 Systems Engineer를 대체할 수 있는지 검증하지 않는다.

프로젝트의 목적은 다음을 확인하는 것이다.

> **우주 engineering 문서 검토 과정에서 LLM을 추가할 이유가 실제로 존재하는가? 존재한다면 어떤 종류의 문제에서 그 가치가 나타나는가?**

이번 평가 기준에 맞추기 위해 기존 PoC의 연구 질문과 실험 범위는 유지하되, 구현은 **최소한의 Multi-Agent 책임 분리와 GCP 배포 구조**로 구성한다.

---

## 2. Scope Freeze: 최종 기준선

이 프로젝트는 아래 범위에서 더 확장하지 않는다.

### 반드시 수행

- NASA cFS 계열 공개 engineering artifact 중 **한정된 subset 1개** 선정
- 실험용 **Clean Baseline** 구성
- BM25 + Embedding 기반 **Hybrid Retrieval** 구현
- 약 **12개의 controlled engineering mutation** 구성
- Clean / Benign control case 구성
- **Hybrid Retrieval vs Hybrid Retrieval + LLM Review** 비교
- **3개의 최소 역할 Agent** 구성
  - Change Analyst Agent
  - Engineering Review Agent
  - Evidence Verifier Agent
- Retrieval은 Agent가 아니라 **공용 Tool**로 구현
- GCP 상에서 동작하는 데모 배포
- Evidence 기반 fail-closed 검증
- LLM Review Success, False Alarm, Review Selection Added Value 확인
- 간단한 Demo UI 구현

### 수행하지 않음

- Agent 수 추가 확장
- Agent-to-Agent 자율 협상 또는 복잡한 orchestration
- Multi-Agent 자체의 알고리즘 연구
- Fine-tuning
- Knowledge Graph / Graph DB
- 상용 MBSE 도구 연동
- SysML 자동 처리
- 실제 spacecraft physics 계산
- Requirement / Design / Test 자동 수정
- 산업 수준 validation
- 대규모 benchmark 구축
- 통계적 유의성 검정 중심 연구
- 복잡한 ranking metric 또는 다수의 ablation study
- MODIS / CM1을 별도 핵심 실험으로 확장
- Vertex AI Vector Search, Agent Engine 등 추가 관리형 서비스를 필수 범위로 확대

새로운 기능을 제안할 때는 다음 질문 하나로 판단한다.

> **“이 기능이 LLM을 Engineering Change Review에 추가하는 것이 실제로 도움이 되는지 확인하거나, 평가 항목을 직접 충족하는 데 필요한가?”**

- 그렇다: 유지
- 있으면 좋아 보이는 정도다: 제외

---

## 3. 해결하려는 문제와 기존 시스템과의 차이

우주 시스템 개발에서는 Requirement, Design, Interface, Verification, Test 등 여러 engineering artifact가 함께 사용된다.

예를 들어 정상 baseline이 다음과 같다고 하자.

```text
Requirement
Telemetry rate shall support 100 Mbps.

Interface
Maximum supported telemetry rate: 100 Mbps.

Verification Test
Telemetry performance verified at 100 Mbps.
```

Requirement가 다음과 같이 변경된다.

```text
100 Mbps -> 250 Mbps
```

변경 자체가 틀린 것은 아니다. 그러나 기존 Interface와 Verification Test가 여전히 100 Mbps를 기준으로 한다면 해당 artifact는 추가 검토 대상이 될 수 있다.

이 프로젝트에서 각 계층의 역할은 명확히 구분한다.

| 계층 | 역할 | 질문 |
|---|---|---|
| Explicit Traceability | 이미 등록된 관계 추적 | 무엇과 이미 연결되어 있는가? |
| Hybrid Retrieval | 관련 가능성이 있는 artifact 후보 축소 | 무엇이 이 변경과 관련 있어 보이는가? |
| LLM Semantic Review | 후보의 실제 review 필요성 판단 | 이 변경 때문에 이 artifact를 검토할 이유가 있는가? |
| Human Engineer | 최종 engineering 판단 | 실제 조치가 필요한가? |

따라서 현재 PoC의 차별점은 **LLM이 검색되지 않은 문서를 새로 찾아내는 것**이 아니다.

> **Hybrid Retrieval이 확보한 candidate를 단순 similarity 목록으로 끝내지 않고, change-specific engineering review 판단과 evidence로 전환하는 것**이 현재 LLM layer의 역할이다.

---

## 4. 데이터 전략

### 4.1 메인 데이터

NASA cFS 및 관련 공개 engineering artifact 가운데 실험에 적합한 **작은 subset 하나**를 선정한다.

가능한 artifact 예시는 다음과 같다.

- Requirements
- Requirements-to-Design Trace
- Design Documentation
- Interface-related Documentation
- Unit Tests
- Verification-related Documentation
- Version / Change Documentation

### 4.2 Clean Baseline 구성

NASA 자료라는 이유만으로 전체 데이터를 완전한 정답으로 간주하지 않는다.

실험에 사용할 subset만 선정한 뒤 다음을 확인한다.

- 문서 내부에 명백한 contradiction이 없는가?
- Requirement와 Design / Test 관계를 사람이 이해할 수 있는가?
- 실험에 사용할 문서가 충분한 context를 제공하는가?
- mutation을 넣었을 때 예상되는 review target을 명확하게 정의할 수 있는가?

이 조건을 만족하는 subset만 **Experimental Clean Baseline**으로 고정한다.

NASA 데이터의 역할은 완전한 ground truth를 보장하는 것이 아니라 **실제 aerospace engineering vocabulary와 artifact 구조를 가진 현실적인 실험 배경**을 제공하는 것이다.

---

## 5. 최종 Multi-Agent 아키텍처

Multi-Agent는 프로젝트 주제를 바꾸기 위한 기능이 아니라 **역할 분리와 신뢰성 확보를 위한 최소 구현 구조**로 사용한다.

```text
Engineering Change
        |
        v
+-----------------------+
| Change Analyst Agent  |
+-----------+-----------+
            |
            | structured change
            v
+-----------------------+
| Hybrid Retrieval Tool |
| BM25 + Embedding      |
+-----------+-----------+
            |
            | same Top-K candidates
            v
+-----------------------+
| Engineering Review    |
| Agent                 |
+-----------+-----------+
            |
            | proposed REVIEW + evidence
            v
+-----------------------+
| Evidence Verifier     |
| Agent                 |
+-----------+-----------+
            |
       +----+----+
       |         |
       v         v
 VERIFIED    REJECT / ABSTAIN
 REVIEW
       |
       v
 Human Engineer
```

### 핵심 설계 원칙

- Retrieval은 Agent가 아니다.
- Change Analyst가 만든 구조화된 변경 정보는 **Baseline과 Proposed 방법에 동일하게 사용**한다.
- Hybrid Retrieval이 생성한 **동일한 Top-K candidate**를 기준으로 비교한다.
- Engineering Review Agent만 candidate의 review 필요성을 판단한다.
- Evidence Verifier Agent는 Review Agent의 판단을 그대로 신뢰하지 않는다.
- 최종 사용자에게는 **검증을 통과한 결과만** 표시한다.

이 구조를 통해 Multi-Agent 구현을 추가하더라도 기존 PoC의 공정한 비교 조건을 유지한다.

---

## 6. Agent별 역할

### 6.1 Change Analyst Agent

Engineering change를 검색과 review에 사용할 수 있는 구조로 정규화한다.

입력 예:

```text
Telemetry rate 100 Mbps -> 250 Mbps
```

출력 예:

```json
{
  "artifact_or_subsystem": "Telemetry",
  "parameter": "data rate",
  "old_value": "100 Mbps",
  "new_value": "250 Mbps",
  "change_type": "increase",
  "related_terms": ["telemetry", "throughput", "data rate", "verification"]
}
```

**하지 않는 것:**

- 관련 artifact 최종 판단
- REVIEW / NO_REVIEW 결정
- evidence 검증

이 Agent의 출력은 Baseline과 Proposed 방법 모두에 동일하게 제공한다.

### 6.2 Hybrid Retrieval Tool

Agent가 아니라 deterministic / retrieval component로 유지한다.

- BM25 lexical retrieval
- Embedding semantic retrieval
- 두 결과 결합
- Top-K candidate 반환

역할은 하나다.

> **전체 artifact 가운데 이 변경과 관련 가능성이 높은 후보를 좁힌다.**

### 6.3 Engineering Review Agent

동일한 Top-K candidate를 읽고 각 artifact가 실제 change review 대상인지 판단한다.

출력은 세 상태로 제한한다.

```text
REVIEW
NO_REVIEW
INSUFFICIENT_EVIDENCE
```

`REVIEW`인 경우 반드시 다음을 포함한다.

```text
Artifact
Evidence Span
Short Reason
```

예:

```text
Decision: REVIEW
Artifact: TEST-42
Evidence: "Telemetry performance verified at 100 Mbps."
Reason: The verification condition still reflects the pre-change value.
```

### 6.4 Evidence Verifier Agent

Review Agent의 결과를 독립적으로 검증한다.

검증 대상은 다음 세 가지다.

1. 제시한 evidence가 실제 retrieved artifact에 존재하는가?
2. evidence가 Review Agent의 주장과 semantic하게 연결되는가?
3. evidence가 부족한데도 과도한 결론을 내리지 않았는가?

검증 실패 시 최종 결과는 다음 중 하나로 처리한다.

```text
REJECTED_UNSUPPORTED
INSUFFICIENT_EVIDENCE
```

검증을 통과한 경우에만 다음으로 전달한다.

```text
VERIFIED_REVIEW
```

---

## 7. GCP 인프라 구성

GCP는 평가 항목을 충족하기 위해 사용하되, 서비스 수를 늘리는 것이 목적이 아니다.

### 필수 구성

| GCP 구성요소 | 역할 |
|---|---|
| Cloud Run | Demo UI/API 및 ADK Multi-Agent orchestration 실행 |
| Vertex AI | Gemini 기반 Agent inference 및 embedding 생성 |
| Cloud Storage | NASA 원본/전처리 artifact, mutation 정의, 실험 결과 저장 |
| Cloud Logging | Agent 판단, verifier 결과, 오류 및 실행 로그 기록 |
| IAM / Service Account | 서비스 간 최소 권한 접근 |

### Retrieval 저장 방식

PoC에서는 복잡한 managed vector database를 추가하지 않는다.

- BM25 index: Cloud Run 애플리케이션에서 로드
- Embedding index: 작은 corpus이므로 로컬 FAISS 또는 동등한 경량 index 사용 가능
- index 파일과 전처리 결과는 Cloud Storage에 저장 가능

따라서 GCP 인프라는 **배포, 모델 호출, 데이터 저장, 관측 가능성**에 집중한다.

### 배포 형태

```text
User / Demo UI
      |
      v
Cloud Run
  - API / UI
  - ADK orchestration
  - Hybrid Retrieval Tool
      |
      +------------------------+
      |                        |
      v                        v
Vertex AI                Cloud Storage
Gemini / Embedding       NASA artifacts
      |                  Mutation data
      |
      v
Cloud Logging
Agent / Verifier traces
```

---

## 8. Hallucination 방어와 신뢰성 설계

평가 항목의 “무결점 신뢰성”을 LLM이 항상 100% 정확하다는 의미로 해석하지 않는다.

프로젝트의 신뢰성 목표는 다음이다.

> **근거 없는 LLM 출력이 최종 engineering recommendation으로 그대로 노출되지 않도록 fail-closed 구조를 만든다.**

### 8.1 Retrieval Grounding

Review Agent는 retrieval된 NASA artifact context만 근거로 사용한다.

### 8.2 Structured Decision

자유 형식 결론 대신 다음 상태만 허용한다.

```text
REVIEW
NO_REVIEW
INSUFFICIENT_EVIDENCE
```

### 8.3 Evidence Required

`REVIEW`에는 반드시 원문 evidence span이 포함되어야 한다.

### 8.4 Deterministic Evidence Check

Evidence text가 retrieved source span에 실제 존재하는지 코드로 확인한다.

- 존재하지 않음 -> reject
- source ID 불일치 -> reject

### 8.5 Evidence Verifier Agent

문장 존재 여부뿐 아니라 evidence가 review reason을 실제로 지지하는지도 별도로 확인한다.

### 8.6 Fail-Closed Final Output

```text
Review Agent says REVIEW
        |
        v
Evidence exact-span check
        |
        v
Verifier Agent
        |
   +----+----+
   |         |
 pass       fail
   |         |
   v         v
DISPLAY   REJECT / ABSTAIN
```

LLM confidence보다 **source evidence와 verifier 결과를 우선**한다.

---

## 9. Controlled Mutation 실험

프로젝트의 핵심 실험은 기존 계획과 동일하게 유지한다.

```text
Clean Baseline
      |
      v
Controlled Mutation
      |
      v
Known Expected Review Target
      |
      v
Hybrid Retrieval
      |
      +-------------------+
      |                   |
      v                   v
Baseline Result      Multi-Agent Review
                          |
                          v
                    Verified Result
      |                   |
      +---------+---------+
                |
                v
          Result Comparison
```

Mutation은 모델 결과를 보기 전에 정의한다.

각 mutation에 최소한 다음을 기록한다.

- Mutation ID
- 변경 artifact
- 원본 내용
- 변경 내용
- 예상 review target
- 기대 evidence

---

## 10. Mutation 유형과 Case 규모

복잡한 taxonomy를 만들지 않고 세 종류만 사용한다.

### Type A. Direct Conflict - 4개

직접적인 값 또는 조건 충돌.

```text
Requirement
Maximum command packet size = 1024 bytes

Interface
Maximum accepted command packet size = 512 bytes
```

**목적:** pipeline sanity check.  
기존 retrieval 또는 rule 방식으로도 충분할 가능성이 높으며 LLM 우수성을 주장하지 않는다.

### Type B. Semantic Relationship - 4개

동일하거나 관련된 engineering concept이 다른 표현으로 작성된 경우.

```text
Maximum command argument range
<->
Allowed command parameter values
```

**목적:** retrieval 결과 안에서 LLM semantic review가 실제 review judgment를 개선하는지 확인.

### Type C. Cross-Artifact / Indirect Review - 4개

직접적인 문자열 충돌은 없지만 기존 Test / Design / Interface의 assumption이나 condition을 다시 확인해야 하는 경우.

```text
Command parameter range
0-100 -> 0-255

Existing Unit Test
Verifies only the previous 0-100 range
```

**목적:** LLM의 추가 가치가 가장 기대되는 유형.

### Control Cases

- Clean: 3개
- Benign Mutation: 3개

Benign 예:

```text
Message field width
16 bits -> 2 bytes
```

전체 주요 case는 약 **18개**로 고정한다.

---

## 11. 공정한 비교 방법

### Baseline

**Hybrid Retrieval**

- Change Analyst의 구조화된 change 사용
- BM25 + Embedding
- Top-K candidate 반환
- candidate rank와 원문 snippet 제공

### Proposed

**Hybrid Retrieval + Multi-Agent LLM Review**

- Baseline과 동일한 Change Analyst output 사용
- Baseline과 동일한 Top-K candidate 사용
- Engineering Review Agent가 REVIEW 여부 판단
- Evidence Verifier Agent가 근거 검증
- 검증된 결과만 표시

핵심 비교는 다음이다.

```text
Same Change
Same Hybrid Retrieval
Same Top-K Candidates

          |
    +-----+-----+
    |           |
    v           v
Baseline     LLM Review
Candidate    + Verifier
List         + Evidence
    |           |
    +-----+-----+
          |
          v
     Added Value?
```

따라서 LLM의 가치는 **더 좋은 문서를 검색했는가**가 아니라,

> **동일한 후보 문서가 주어졌을 때 실제 engineering review 판단과 근거를 더 유용하게 제공했는가?**

로 해석한다.

---

## 12. 평가 지표

### 12.1 Retrieval Coverage - 진단용

예상 review target이 Hybrid Retrieval Top-K 안에 포함되어 있는지 기록한다.

이 값은 LLM 성능으로 해석하지 않는다.

```text
12 mutation cases
10 targets present in Top-K
2 Retrieval Miss
```

### 12.2 LLM Review Success Rate - 핵심 효과 지표

Retrieval 가능한 mutation case 가운데 Engineering Review Agent가 예상 target을 올바르게 `REVIEW`하고 verifier를 통과한 비율.

```text
10 retrieval-hit cases
8 verified REVIEW

LLM Review Success Rate = 8 / 10
```

### 12.3 False Alarm - 핵심 신뢰성 지표

Clean / Benign case에서 최종적으로 잘못된 `VERIFIED_REVIEW`가 발생한 횟수.

```text
6 control cases
1 false verified REVIEW
```

### 12.4 Review Selection Added Value - 핵심 해석

이 항목은 LLM이 Top-K 밖의 새로운 artifact를 발견했는지를 측정하지 않는다. 동일한 Hybrid Retrieval Top-K가 주어진 상태에서, Multi-Agent Review가 candidate list를 **더 작은 evidence-backed review set으로 선별**하면서 예상 review target을 유지하는지를 본다.

기록할 내용은 다음과 같다.

- Hybrid Retrieval Top-K candidate 수
- 최종 `VERIFIED_REVIEW` 수
- 예상 review target이 최종 review set에 유지되었는지
- 각 `VERIFIED_REVIEW`에 실제 evidence와 short reason이 제공되었는지

특히 **Semantic / Cross-Artifact** 유형에서 단순 similarity candidate를 실제 engineering attention 대상으로 선별하는 효과가 있는지 확인한다.

### 12.5 Unsupported Output Blocked - 신뢰성 보조 지표

Review Agent가 생성했지만 verifier 또는 deterministic evidence check에 의해 차단된 unsupported result 수를 기록한다.

```text
Review Agent proposed REVIEW: 12
Blocked as unsupported: 3
Final verified REVIEW: 9
```

이 지표는 Verifier가 실제로 단순한 장식이 아니라 신뢰성 방어 역할을 수행했는지 보여준다.

---

## 13. 결과 분석 방식

전체 accuracy 하나로 결론내리지 않는다.

| Problem Type | Retrieval Hit@K | Verified LLM Review | 해석 |
|---|---:|---:|---|
| Direct Conflict | ? | ? | LLM 없이도 충분한가? |
| Semantic | ? | ? | Semantic review의 추가 가치가 있는가? |
| Cross-Artifact / Indirect | ? | ? | LLM의 핵심 가치가 나타나는가? |

추가로 reliability 결과를 함께 보여준다.

| Reliability | 결과 |
|---|---:|
| Clean / Benign False Alarm | ? |
| Unsupported Review Blocked | ? |
| Verified Review | ? |

가능한 결론은 모두 유효하다.

### 결과 A - LLM 가치 확인

Semantic 또는 Cross-Artifact case에서 동일 candidate를 대상으로 LLM이 올바른 review 판단과 evidence를 추가했다.

### 결과 B - Retrieval만으로 충분

해당 범위에서는 candidate 자체가 충분히 명확하여 LLM의 추가 비용을 정당화하기 어려웠다.

### 결과 C - Review Success는 높지만 Warning 증가

LLM은 second reviewer로 가치가 있으나 불필요한 warning trade-off가 나타났다.

### 결과 D - Verifier가 다수 출력을 차단

LLM Review Agent 단독 사용은 불안정하지만 evidence verification을 추가했을 때 unsupported output 노출을 줄일 수 있었다.

### 결과 E - 추가 가치 없음

본 controlled condition에서는 LLM semantic review의 실질적 추가 효과가 확인되지 않았다.

---

## 14. 비즈니스 임팩트와 문제 정의

본 프로젝트가 해결하려는 문제는 “위성을 LLM이 설계한다”가 아니다.

실제 가치 제안은 다음과 같다.

```text
Engineering Change
      |
      v
많은 관련 artifact 후보
      |
      v
무엇을 먼저 확인해야 하는가?
      |
      v
LLM Semantic Review
      |
      v
Verified Review Target
+ Evidence
```

기존 시스템과의 역할 차이는 다음과 같다.

> **Traceability tells what is already connected.**  
> **Retrieval tells what may be related.**  
> **LLM Review suggests what deserves engineering attention, with evidence.**

프로젝트가 주장하는 비즈니스 가치는 다음 수준으로 제한한다.

- Review candidate prioritization
- Potentially overlooked review need identification within retrieved candidates
- Evidence-backed review assistance
- 사람이 확인해야 할 정보의 탐색 부담 감소 가능성

다음은 주장하지 않는다.

- mission failure 감소율
- spacecraft safety 자동 검증
- 실제 engineering error 감소율
- 산업 배포 준비 완료

---

## 15. Demo 구성

발표 데모는 최대 네 장면으로 제한한다.

### Demo 1. Clean

```text
Original Baseline
-> NO_REVIEW
```

### Demo 2. Explicit Change

```text
100 Mbps -> 250 Mbps
```

```text
REVIEW
TEST-42
Evidence: Existing verification condition = 100 Mbps
Verifier: VERIFIED
```

### Demo 3. Restore

```text
250 Mbps -> 100 Mbps
-> NO_REVIEW
```

### Demo 4. Semantic / Cross-Artifact + Verifier

```text
Hybrid Retrieval
-> candidate exists but review need is unclear

Engineering Review Agent
-> REVIEW + evidence + reason

Evidence Verifier Agent
-> VERIFIED
```

가능하면 추가로 unsupported review 하나를 intentionally 보여준다.

```text
Review Agent
-> REVIEW

Evidence Verifier
-> evidence unsupported
-> REJECTED_UNSUPPORTED
```

이 장면은 Multi-Agent와 hallucination 방어를 동시에 설명한다.

---

## 16. 팀 역할과 프레젠테이션

2인 팀 기준으로 역할을 다음처럼 나눌 수 있다.

### Member A - AI / Infrastructure

- ADK Multi-Agent 구성
- Vertex AI 연동
- Hybrid Retrieval
- Cloud Run 배포
- Cloud Logging / execution trace

### Member B - Data / Evaluation / UX

- NASA artifact subset 구성
- Clean Baseline 검증
- Controlled Mutation 12개 설계
- Evaluation script
- Demo UI 및 결과 시각화

### 공동 작업

- Agent prompt와 output schema 확정
- 대표 성공 / 실패 case 선정
- 최종 presentation story
- Demo rehearsal

1인 프로젝트라면 위 역할을 두 workstream으로 나누어 순차 진행한다.

### 발표 흐름

1. Engineering Change Review 문제
2. 기존 Traceability / Retrieval의 역할과 한계
3. 핵심 질문
4. 3-Agent + GCP Architecture
5. Controlled Mutation 실험
6. Hybrid vs Multi-Agent 결과
7. Evidence Verifier가 차단한 사례
8. 어떤 문제에서 LLM이 필요했는지 결론

---

## 17. 평가 기준 대응

### 17.1 Multi-Agent 아키텍처 및 GCP 인프라 완성도 - 35점

보여줄 것:

- 3-Agent 책임 분리
- Retrieval Tool과 Agent 역할 분리
- ADK 기반 orchestration
- Cloud Run 실제 배포
- Vertex AI 기반 Gemini / embedding
- Cloud Storage 데이터 관리
- Cloud Logging execution trace
- 동일 Top-K candidate를 사용하는 공정한 pipeline

핵심 메시지:

> **Agent 수를 늘린 것이 아니라 Change Analysis, Review, Verification 책임을 분리했다.**

### 17.2 할루시네이션 방어 및 무결점 신뢰성 - 20점

보여줄 것:

- retrieval-grounded context
- structured decision
- evidence mandatory
- deterministic exact-span validation
- independent Evidence Verifier Agent
- fail-closed output
- Clean / Benign false alarm test
- unsupported output blocked 사례

핵심 메시지:

> **LLM confidence를 신뢰하지 않고 source evidence가 검증된 결과만 사용자에게 노출한다.**

### 17.3 비즈니스 임팩트 및 문제 정의 - 30점

보여줄 것:

- engineering change가 여러 artifact review로 확산되는 문제
- Traceability / Retrieval / LLM 역할의 명확한 구분
- NASA engineering artifact 사용
- Controlled Mutation으로 LLM 추가 가치 직접 비교
- 과장 없이 review attention allocation 문제로 정의

핵심 메시지:

> **LLM이 engineer를 대체하는 것이 아니라 candidate list를 evidence-backed review set으로 선별하는 데 가치가 있는지 검증한다.**

### 17.4 팀 시너지 및 프레젠테이션 - 15점

보여줄 것:

- AI/Infra와 Data/Evaluation 역할 분리
- 하나의 end-to-end demo로 통합
- 성공 case뿐 아니라 false alarm / rejected output도 공개
- 구조 -> 실험 -> 결과 -> 한계 순서로 단순한 발표 구성

---

## 18. 실행 계획

### 1단계. Data / Baseline

- NASA cFS subset 선정
- 문서 구조 확인
- Clean Baseline 확정

### 2단계. Retrieval

- parsing
- BM25
- embedding
- Hybrid Retrieval
- Top-K 고정

### 3단계. Controlled Mutation

- Direct 4개
- Semantic 4개
- Cross-Artifact 4개
- Clean 3개
- Benign 3개

### 4단계. Multi-Agent

- Change Analyst Agent
- Engineering Review Agent
- Evidence Verifier Agent
- structured output
- deterministic evidence check

### 5단계. GCP Deployment

- Cloud Storage 데이터 업로드
- Vertex AI model 연결
- Cloud Run deployment
- Cloud Logging 확인

### 6단계. Evaluation

- Retrieval Coverage
- LLM Review Success Rate
- False Alarm
- Review Selection Added Value
- Unsupported Output Blocked
- 유형별 결과 정리

### 7단계. Demo / Presentation

- 대표 성공 case 2~3개
- LLM 불필요 case 1개
- Verifier rejection case 1개
- 간단한 UI
- 평가 기준별 핵심 장면 정리

---

## 19. 프로젝트 성공 기준

특정 accuracy 수치로 성공을 정의하지 않는다.

다음 질문에 실제 결과로 답할 수 있으면 프로젝트는 성공이다.

1. Hybrid Retrieval 단계에서 어떤 종류의 artifact를 충분히 후보로 확보할 수 있었는가?
2. 동일한 candidate에서 LLM Review를 추가했을 때 실제 review judgment와 evidence가 개선된 문제는 무엇인가?
3. LLM이 필요 없거나 Retrieval만으로 충분했던 문제는 무엇인가?
4. Verifier는 unsupported output을 실제로 차단했는가?
5. Clean / Benign case에서 최종 false warning은 어느 정도였는가?

최종 결과는 다음 형태가 이상적이다.

```text
Direct Conflict
-> Retrieval만으로 충분 / LLM 차이 적음

Semantic Relationship
-> LLM Review 효과 있음 / 없음

Cross-Artifact Review
-> LLM Review 효과 있음 / 없음

Reliability
-> Unsupported output N건 차단
-> Clean/Benign false alarm N건
```

---

## 20. 발표에서 주장할 수 있는 범위

결과가 좋더라도 다음 정도로만 말한다.

> **선정된 NASA engineering artifact를 이용한 controlled proof-of-concept에서, 동일한 Hybrid Retrieval candidate 뒤에 evidence-grounded Multi-Agent LLM review를 추가했을 때 일부 engineering review case에서 candidate 선별과 evidence 제공에 추가적인 value가 있는지 확인했다.**

다음은 주장하지 않는다.

- LLM이 spacecraft engineering을 검증할 수 있다.
- Multi-Agent 구조이므로 정확성이 보장된다.
- 실제 mission error를 몇 % 줄인다.
- NASA 데이터에서 잘 됐으므로 산업 적용이 가능하다.
- LLM이 engineering reasoning을 완벽히 수행한다.
- Verifier가 모든 hallucination을 제거한다.

---

## 21. 최종 프로젝트 포지셔닝

본 프로젝트의 최종 정의는 다음과 같다.

> **NASA Engineering Artifacts를 이용해 Engineering Change Review pipeline에서 evidence-grounded Multi-Agent LLM review를 추가할 가치가 실제로 존재하는지 확인하는 Controlled Proof-of-Concept**

프로젝트의 가치는 LLM 또는 Multi-Agent의 절대적인 우수성을 보여주는 것이 아니다.

오히려 다음을 구분하는 데 있다.

- **LLM이 필요 없는 문제**
- **Hybrid Retrieval만으로 충분한 문제**
- **LLM semantic review가 추가적인 가치를 줄 수 있는 문제**
- **LLM 판단이 있었지만 evidence 검증 때문에 차단해야 하는 문제**

최종 질문은 하나로 유지한다.

> **“Engineering Change Review에 LLM을 추가할 이유가 있는가? 있다면 어떤 종류의 문제에서이며, 그 출력을 어떻게 신뢰할 수 있게 만들 것인가?”**

이 질문과 평가 기준에 직접 필요하지 않은 기능과 실험은 추가하지 않는다.

---

## 22. 구현 참고

현재 GCP 구현 계획은 Google Cloud의 Agent Development Kit(ADK)를 이용한 agent 구축 및 Cloud Run 배포 모델과 정합되도록 구성한다. ADK는 역할이 분리된 agent를 조합하는 구조에 사용하고, 실제 PoC에서는 복잡한 agent autonomy보다 예측 가능한 sequential orchestration을 우선한다.

핵심 GCP 구성은 Cloud Run, Vertex AI, Cloud Storage, Cloud Logging으로 고정한다.
