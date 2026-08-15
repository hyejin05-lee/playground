# AI 8대 품질속성 별 AI System Design Style & Patterns 요약

본 문서는 AI 시스템 설계(AI System Design) 교육 과정을 바탕으로, AI 8대 품질 속성을 달성하기 위한 대표적인 아키텍처 스타일(Architecture Styles)과 디자인 패턴(Design Patterns), 그리고 Cline^HD 에이전트 하네스 설계에의 적용 방안을 정리한 문서입니다.

---

## 1. Functional Correctness (기능 정확성) 확보를 위한 설계 패턴
- **Multi-Agent Orchestration / Supervisor Pattern**: 단일 거대 프롬프트 대신 작업을 역할별(분석, 코드 생성, 검증 등) Subagent로 분할하고 Supervisor가 워크플로우를 조율.
- **Reflection / Self-Correction Pattern (자가 교정)**: 생성된 코드나 출력물에 대해 Linter, Compiler, Unit Test 결과를 피드백 루프로 주입하여 자체 검증 및 수정 반복.
- **Retrieval-Augmented Generation (RAG) Pattern**: 도메인별 최신 문서, 사내 코딩 컨벤션을 임베딩 검색하여 컨텍스트에 주입함으로써 환각 방지 및 정밀도 향상.
- **Strict Schema Enforcement / Type-Safe Tool Calling**: Pydantic, JSON Schema 등을 통해 LLM의 입출력 데이터 타입을 런타임에서 강제.

---

## 2. Robustness (강건성) 확보를 위한 설계 패턴
- **Sandboxed Execution & Isolated Runtime Pattern**: 에이전트가 실행하는 스크립트나 파일 I/O를 Docker/컨테이너 또는 격리된 가상 환경 내에서 실행하여 호스트 오염 방지.
- **Circuit Breaker / Fallback Pattern**: 특정 모델 호출 타임아웃, 토큰 한도 초과, 툴 실행 실패 시 대체 모델(사내 서빙 모델 3종 중 Fallback)이나 기본 안전 모드로 자동 전환.
- **Input/Output Guardrail Pattern (가드레일)**: LLM 입출력단에 NeMo Guardrails, Llama-Guard 등을 배치하여 프롬프트 인젝션 및 시스템 탈옥 시도를 사전 필터링.
- **Deterministic Validation Filter**: LLM 응답을 파싱할 때 구조적 불일치가 발생하면 상위 루프로 에러를 전파하지 않고 런타임 훅에서 재질의(Retry) 처리.

---

## 3. Privacy (프라이버시) 확보를 위한 설계 패턴
- **On-Premise / Local Inference Gateway Pattern**: 사내 서빙 모델 3종을 활용하여 민감 소스코드와 기밀 데이터가 외부 퍼블릭 클라우드로 전송되지 않도록 온프레미스 라우팅 보장.
- **Data Anonymization & Token Masking Pattern**: 프롬프트 전송 전 정규표현식 및 Named Entity Recognition(NER) 기반으로 PII 및 인증 토큰 자동 마스킹.
- **Principle of Least Privilege Context Pattern**: 서브에이전트에게 전체 레포지토리가 아닌 해당 Task 수행에 필수적인 특정 디렉토리/파일 슬라이스만 격리 전달.

---

## 4. Fairness (공정성) 확보를 위한 설계 패턴
- **Debiasing Prompting & System Persona Alignment**: 모델 지침에 공정하고 편향 없는 평가 기준을 명시적 규칙(Rule)으로 정의.
- **Multi-Model Cross-Validation (다중 모델 교차 검증)**: 중요한 의사결정(예: 아키텍처 평가, 보안 감사) 시 사내 서로 다른 기초 모델의 결과를 앙상블/비교하여 단일 모델 편향 제거.

---

## 5. Performance Efficiency (수행 효율성) 확보를 위한 설계 패턴
- **Subagent Context Isolation Pattern (컨텍스트 격리 위임)**: 특정 서브태스크(예: 파일 검색, AST 분석)를 독립 세션으로 위임하고, 상위 세션에는 수천 줄의 로그 대신 '요약된 최종 JSON 결과'만 반환하여 토큰 윈도우 폭발 방지.
- **Asynchronous Parallel Execution Pattern (비동기 병렬 실행)**: 독립적인 Subagent(예: 모바일 빌드 점검, TV UI 검증)를 병렬 스레드/프로세스로 동시 디스패치하여 전체 소요 시간 단축.
- **Model Tiering / Dynamic Model Routing Pattern (모델 계층화 및 라우팅)**: 단순 분류/문법 검사는 경량 모델(사내 경량 LLM), 고도의 복합 추론은 고성능 모델로 작업 난이도별 사내 서빙 모델 3종을 분기 라우팅.
- **Prompt Caching & KV-Cache Reuse**: 공통 시스템 프롬프트 및 프로젝트 뼈대 구조를 캐싱하여 TTFT 및 토큰 비용 절감.

---

## 6. Functional Adaptability (기능 적응성) 확보를 위한 설계 패턴
- **Plugin / Skill Extensibility Architecture (플러그인 기반 확장)**: 도메인별(모바일, TV, 가전, 네트워크) 특화 규칙과 도구를 독립된 YAML/SKILL.md 포맷으로 캡슐화하여 런타임에 동적 로딩.
- **Perspective Pattern (목적 특화 관점 에이전트)**: AgentRuntime 위에 특정 도메인 페르소나, 사용 가능 도구 세트, 가드레일을 묶어 'Perspective' 객체로 정의하고 상황에 따라 손쉽게 교체/조합.
- **Adapter / Harness Layering Pattern**: Cline Core 엔진과 도메인별 하위 도구 사이에 SDK 기반의 추상화 계층(AgentRuntime, SessionRuntime)을 두어 엔진 수정 없이 기능 확장.

---

## 7. Controllability (제어 가능성) 확보를 위한 설계 패턴
- **Hard Tool Boundary & Dynamic Permission Masking Pattern**: LLM의 프롬프트(Soft Restriction)에 의존하지 않고, **AgentRuntime 레벨에서 각 Perspective별 허용 도구 화이트리스트(Whitelist)를 하드하게 강제(Hard Restriction)**. 비인가 도구는 LLM Tool Call 목록에서 완전히 제거하거나 런타임 훅에서 차단.
- **Runtime Hook & Interceptor Pattern**: 툴 실행 전/후(pre-tool-call, post-tool-call)에 런타임 훅을 배치하여 인자 유효성 검증, 실행 취소, 위험 명령어 차단 수행.
- **Human-in-the-Loop (HITL) Approval Pattern**: 위험 도구(파일 삭제, Git Push, 외부 배포) 실행 전 사용자 명시적 승인 단계 강제.
- **Type-Safe Structured Output Pipe Pattern**: Subagent의 리턴값을 JSON Schema 또는 엄격한 인터페이스로 고정하고, 런타임 레벨에서 검증 실패 시 상위 파이프라인으로 전파되지 않도록 격리.

---

## 8. Explainability (설명 용이성) 확보를 위한 설계 패턴
- **Event-Driven Observability & Subscription Pattern**: Cline SDK의 `event subscription` 메커니즘을 활용하여 에이전트 상태 변화, 도구 호출, 추론 단계를 실시간 이벤트 스트림으로 UI에 발행.
- **Hierarchical Execution Tree Visualization**: 주 에이전트와 서브에이전트 간의 호출 관계(Call Stack), 전달된 컨텍스트, 반환된 요약 데이터를 시각적 트리 형태로 기록/제공.
- **Structured Audit Logging Pattern**: 모든 LLM 프롬프트, 도구 실행 파라미터, 실행 시간, 토큰 소모량을 구조화된 JSON 로그로 영구 보관.
