# AI 시스템 8대 품질 속성 및 평가 메트릭 (ISO/IEC 25059:2023 기반 요약)

본 문서는 ISO/IEC 25059:2023(Software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — Quality model for AI systems) 및 AI Engineering 교육 과정을 기반으로, AI 시스템의 8대 핵심 품질 속성과 세부 평가 메트릭(Metric)을 정리한 기술 요약서입니다.

---

## 1. Functional Correctness (기능 정확성)
- **정의**: AI 시스템이 주어진 입력 및 작업 환경에서 의도된 목표와 기능 명세에 부합하는 예측, 분류, 생성 또는 의사결정 결과를 통계적/결정론적으로 올바르게 제공하는 정도. (ISO/IEC 25059에서는 확률적 특성을 고려하여 허용 오차 내의 정확한 작업 수행을 정의)
- **주요 평가 메트릭 (Metrics)**:
  - **분류/예측 메트릭**: Accuracy, Precision, Recall, F1-Score, ROC-AUC, PR-AUC.
  - **회귀/수치 예측**: MAE (Mean Absolute Error), RMSE (Root Mean Squared Error), R² Score.
  - **생성형 AI / LLM 메트릭**:
    - Task Success Rate (태스크 완료율): 요구된 작업을 끝까지 오류 없이 완수한 비율.
    - Hallucination Rate (환각율): 사실과 다르거나 입력 컨텍스트에 없는 허위 정보를 생성한 비율.
    - Schema / Syntax Compliance Rate: 생성된 코드/JSON/Diff 출력이 문법 및 기정의된 스키마를 준수하는 비율.
    - Code Pass@k / Exact Match (EM): 코드 생성 시 유닛 테스트 통과율.

---

## 2. Robustness (강건성 / 신뢰성 하위 속성)
- **정의**: 시스템에 노이즈(Noise), 이상치(Outlier), 적대적 공격(Adversarial Attack), 프롬프트 인젝션(Prompt Injection), 미분포 데이터(OOD: Out-Of-Distribution) 또는 예기치 않은 실행 환경 변화가 발생하더라도 사전에 정의된 기능 정확성과 안전성을 유지하는 능력.
- **주요 평가 메트릭 (Metrics)**:
  - **Adversarial Robustness Rate (적대적 공격 방어율)**: Jailbreak, Prompt Injection 등의 악의적 입력 시도 시 시스템이 오동작하지 않고 정상 방어하는 비율.
  - **Perturbation Invariance / Stability (변동 불변성)**: 입력 프롬프트의 미세 변형(동의어 치환, 오타, 문맥 순서 변경) 발생 시 결과값의 일관성 유지도.
  - **Out-of-Distribution Error Rate (OOD 에러율)**: 학습 데이터/사전 정의 도메인 외의 입력 인입 시 에러를 유발하거나 오동작하는 빈도.
  - **Fail-safe / Graceful Degradation Rate**: 모델 추론 실패 또는 툴 오류 시 시스템 전체 다운 없이 Fallback(예: 상위 에이전트 보고, 대체 툴 호출)으로 전환되는 성공률.

---

## 3. Privacy (프라이버시 / 정보보안 하위 속성)
- **정의**: AI 모델의 학습, 튜닝, 추론 및 에이전트 툴 실행 과정에서 개인식별정보(PII), 기밀 코드, 지적 재산권(IP) 및 민감 데이터가 무단 유출, 역추론(Membership Inference), 혹은 인가되지 않은 외부 엔드포인트로 전송되지 않도록 보호하는 능력.
- **주요 평가 메트릭 (Metrics)**:
  - **PII / Secret Leakage Rate (민감정보 유출률)**: LLM 출력 및 로그에 주민번호, 사내 API Key, 기밀 소스코드 등이 노출되는 빈도.
  - **Data Minimization Index**: 특정 목적 달성을 위해 Subagent나 외부 모델에 전달되는 컨텍스트 중 불필요한 민감 데이터가 필터링/마스킹된 비율.
  - **Compliance Score (규제 준수도)**: GDPR, 개인정보보호법, 사내 보안 규정 체크리스트 통과율.

---

## 4. Fairness (공정성 / 사회적·윤리적 위험 완화)
- **정의**: AI 시스템이 성별, 인종, 특정 그룹, 코딩 스타일, 서브 프로젝트 도메인 등에 대해 부당하게 차별적이거나 편향(Bias)된 결정을 내리지 않고 균등한 성능과 기회를 보장하는 능력.
- **주요 평가 메트릭 (Metrics)**:
  - **Demographic Parity / Disparate Impact (인구통계학적 패리티)**: 상이한 그룹/조건 간의 긍정 결정 비율의 편차.
  - **Equalized Odds / Equal Opportunity**: 그룹 간 True Positive Rate(TPR) 및 False Positive Rate(FPR)의 차이.
  - **Toxicity / Bias Score**: LLM 생성 텍스트의 혐오, 편견, 유해 표현 포함 정도 (Perspective API, 사내 안전 벤치마크 점수).

---

## 5. Performance Efficiency (수행 효율성)
- **정의**: AI 시스템이 요구된 작업을 수행할 때 소비하는 컴퓨팅 자원(CPU, GPU, 메모리, 네트워크 대역폭) 및 토큰(Token), 시간(Latency)을 최소화하면서 최적의 성능을 도출하는 능력.
- **주요 평가 메트릭 (Metrics)**:
  - **Latency / Response Time (지연 시간)**: TTFT (Time to First Token), End-to-End Task Execution Time.
  - **Token Efficiency (토큰 소비 효율성)**:
    - 작업 단위당 총 소비 토큰 수 (Input + Output Token Count).
    - Context Compression Ratio (컨텍스트 압축률): Subagent 위임을 통해 절감된 주 에이전트 컨텍스트 윈도우 비율.
  - **Throughput / Concurrency (처리량 및 병렬성)**: 초당 처리 요청 수 (RPS/TPS), Subagent 병렬 실행 속도 개선율.
  - **Resource Utilization (자원 사용률)**: GPU VRAM 점유율, CPU 부하, 사내 추론 서버 비용(Cost per Query).

---

## 6. Functional Adaptability (기능 적응성)
- **정의**: AI 시스템이 새로운 도메인(모바일, TV, 가전, 네트워크 등 다양한 사내 SW 제품군), 새로운 작업 환경, 또는 추가적인 툴/스킬이 주어졌을 때 기본 엔진의 대규모 재설계 없이 신속하게 적응하여 기능을 확장할 수 있는 능력.
- **주요 평가 메트릭 (Metrics)**:
  - **Zero-shot / Few-shot Transfer Accuracy**: 새로운 제품 도메인의 태스크 수행 정확도.
  - **Skill / Tool Onboarding Time (도구 확장 용이성)**: 신규 Subagent/Skill 명세를 정의하고 시스템에 배포하여 정상 동작하기까지 소요되는 공수/시간.
  - **Context Switching Flexibility**: 다중 도메인 전환 시 이전 도메인의 간섭(Catastrophic Forgetting/Interference) 없이 독립적으로 태스크를 수행하는 비율.

---

## 7. Controllability (제어 가능성 / 사용자 제어 및 개입성)
- **정의**: 사람(개발자) 또는 상위 오케스트레이터가 AI 시스템(특히 자율 루프를 가진 Agent)의 도구 접근 범위, 파일 시스템 권한, 네트워크 통신, 출력 포맷, 실행 상태를 엄격하게 제한하고, 필요 시 런타임에 즉각적으로 개입(Intervene), 차단(Abort), 수정할 수 있는 능력.
- **주요 평가 메트릭 (Metrics)**:
  - **Tool / Permission Violation Rate (인가 외 도구 접근율)**: 허가되지 않은 도구(예: Read-only 역할에 File Write 툴) 호출 시도 및 실제 실행 차단 성공률 (Target: 차단율 100%).
  - **Structured Output Schema Compliance (출력 제어 준수율)**: 정의된 JSON Schema/Type/Diff 형식을 벗어나지 않고 파싱 가능한 정형 데이터로 응답한 비율.
  - **Intervention Latency & Success Rate (개입 성공률 및 지연)**: 사용자 또는 Runtime Hook에 의한 실행 중단(Abort/Cancel), 롤백, 승인(HITL) 요청의 정상 처리율.
  - **Deterministic Sandbox Boundary Enforcement**: 프롬프트 인젝션이나 환각 상황에서도 OS 셸 및 파일 I/O 경계를 하드웨어/런타임 레벨에서 강제하는 준수도.

---

## 8. Explainability (설명 용이성 / 투명성)
- **정의**: AI 시스템의 의사결정 과정, 내부 추론 논리, 호출된 도구와 그 인자(Arguments), 컨텍스트 참조 이력 등을 개발자와 이해관계자가 명확히 이해하고 검증할 수 있도록 근거를 제공하는 능력.
- **주요 평가 메트릭 (Metrics)**:
  - **Action / Tool Traceability (추적 가능성)**: Agent가 특정 도구를 호출하고 결과를 도출한 단계별 Thought-Action-Observation 이력의 가시화 비율 (100% 로깅 여부).
  - **Faithfulness / Groundedness (근거 충실도)**: 생성된 답변이나 코드가 실제 참조한 파일/컨텍스트에 기반하고 있는지에 대한 정량 지표.
  - **Event Subscription & Observability Coverage**: Runtime Hooks 및 Event Stream을 통해 에이전트의 내부 상태 변화를 실시간 모니터링할 수 있는 이벤트 커버리지.
