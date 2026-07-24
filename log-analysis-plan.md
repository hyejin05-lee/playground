# 로그 파일 분석 Agent 개발 검토 및 기획안 (log-analysis-plan.md)

대용량 시스템 및 애플리케이션 로그를 안전하고 효율적으로 분석하는 **LLM 기반 Log Analysis Agent** 개발을 위한 구체적인 검토 내용 및 기획안입니다. 

---

## 1. 개요 및 목적 (Overview & Goals)

### 1.1 배경 및 페인포인트
* **대용량 로그 처리 한계**: 수백 MB ~ 수 GB 단위의 로그 파일은 LLM의 Context Window(토큰 제한)를 초과하여 직접 입력 불가.
* **원본 보존의 중요성**: 장애 원인 분석 중 원본 로그 파일 수정/삭제 가능성을 원천 차단해야 함 (**Read-Only 안전성**).
* **도메인 지식의 공백**: LLM 범용 모델만으로는 시스템 특유의 이상(Abnormal) 징후 패턴이나 비즈니스 로직을 놓치기 쉬우므로, 사용자의 도메인 지식 결합 필수.
* **다양한 로그와 목적**: 웹서버, 분산 트레이스 등 로그 종류가 다양하며, 목적 또한 에러 분석, 성능 병목 식별, 보안 탐지 등으로 상이함.


### 1.2 개발 목표
* **안전한 읽기 전용 구조 보장**: write/delete 계열 도구를 원천 차단하는 Harness 적용.
* **계층적 대용량 분석**: Filter -> Chunk -> Aggregate 방식의 Map-Reduce 형태 로그 심층 분석.
* **목적에 따른 유연한 분석 및 해결 힌트 제시**: 에러 진단, 보안 침해 탐지, 성능 병목 분석 등 다양한 목적에 범용적으로 대응하며, 근본 원인(Root Cause) 추적 및 조치 가이드 생성.

---

## 2. 벤치마킹 및 실험 계획

1GB 이상의 대용량 로그를 대상으로 기존 AI 도구(Claude Code, 현재 Cline 등)들의 한계점 및 최적의 접근 전략을 파악합니다.

### 2.1 벤치마크 데이터셋 및 시나리오
* **데이터셋**: Loghub HDFS_v1 (11.1M lines, 1.47 GiB) 및 1GB 이상 규모의 Web Server Access Logs
* **시나리오 (다양한 목적의 분석 검증)**:
  1. **에러 분석**: "HTTP 500 에러의 빈도와 패턴 분석"
  2. **성능 분석**: "특정 시간대 응답시간 급증 원인 탐색"
  3. **분산 추적**: "특정 트랜잭션/BlockID 실패의 Root Cause 추적"
  4. **보안 탐지**: "대용량 로그에서 보안 침해(비정상 접근) 징후 탐색"

---

## 3. 일반화된 Agent 아키텍처 및 4단계 분석 프로세스 

로그 분석은 단순한 '에러 추출'에 국한되지 않습니다. 성능 병목 식별, 비정상 패턴 탐지 등 다양한 사용 목적에 범용적으로 적용할 수 있는 **일반화된 멀티 에이전트 파이프라인**을 설계합니다.

> **Context Discovery (초기 맥락 파악):**  
> 분석을 시작하기 전, Agent는 다음 질문들에 대한 답을 사용자에게 묻거나 시스템을 통해 스스로 파악하여 분석 방향을 구체화해야 합니다.
> 1. **로그 도메인 및 유형 (Domain & Log Type)**
>    - 웹서버 Access Log(Nginx/Apache), 애플리케이션 Structured Log(JSON), 커널 Syslog, 분산 시스템 Trace 중 어느 것에 해당하는가? (도메인 특화 파싱 전략 적용)
> 2. **분석 목적 (Goal)**
>    - 장애/에러 원인 추적 (RCA)인가?
>    - 통계 분석(Statistics & Patterns)인가?
>    - 이상 패턴(Anomaly) 탐지인가?
>    - 성능 병목(Performance) 식별인가?
>    - 보안 침해(Security) 조사인가?
> 3. **알려진 이상 징후 마커 (Abnormal Markers) 파악**
>    - 사용자가 이미 인지하고 있는 에러 코드(예: HTTP 500, Exception), 타임아웃, 특정 IP 등 검색 단서나 키워드가 존재하는가?

```mermaid
flowchart TD
    A[대용량 로그 파일] --> B[1단계: Context Discovery & Triage<br>(로그 인식 및 초기 맥락 파악)]
    B --> C[2단계: Pattern Filtering & Chunking<br>(목적별 타겟 데이터 추출 및 분할)]
    C --> D[3단계: Deep Reasoning / Investigation<br>(상관관계 및 인과 심층 분석)]
    D --> E[4단계: Synthesis & Reporting<br>(최종 리포트 및 가이드 제시)]
    
    U[분석 목적 및 사용자 정의 Config] -.-> C
    U -.-> D
```

| 단계 | 역할 | 주요 동작 및 세부 전략 |
| :--- | :--- | :--- |
| **1단계: 로그 인식 및 파악** (Triage) | 초기 맥락 탐색 | • **로그 도메인 및 유형 파악**: Syslog, JSON, Nginx 여부 확인 및 타임스탬프 파싱<br>• 식별자(Trace ID, IP 등) 스캔 및 샘플링 분석 |
| **2단계: 타겟 추출 및 분할** (Filtering) | 데이터 1차 감축 | • **데이터 처리 전략 적용**: 전체 분석 불가 시 청킹 및 필터링 수행<br>• **분석 목적**에 부합하는 키워드/정규식 기반으로 관련 데이터 추출 및 시간대/식별자 단위 분할 |
| **3단계: 심층 원인 분석** (Investigation) | 상관관계 추론 | • 추출된 로그들의 전후 타임라인 Context 연관성 교차 분석<br>• 정상 패턴 vs 이상 패턴(Anomaly) 차이 식별 및 전파 경로 추적 |
| **4단계: 종합 리포팅** (Synthesis) | 결과 및 힌트 생성 | • Root Cause(근본 원인) 진단 요약 및 논리적 타임라인 정리<br>• 엔지니어 대상 조치 권고안(Actionable Hints) 제공 |

---

## 4. 자연어 사용 예제 (Usage Example)

사용자는 복잡한 도구 사용법을 몰라도, 목적에 따라 자연어로 에이전트에게 유연한 로그 분석을 요청할 수 있습니다.

* **에러 요약 및 원인 분석 (RCA)**
  * *"오늘 서버에 발생한 에러 로그들을 쭉 훑어보고, 가장 많이 발생한 에러 3가지와 원인을 요약해 줘."*
* **특정 식별자 기반 추적**
  * *"특정 BlockID(`blk_-3544583377289625738`)가 포함된 관련 로그를 모두 찾아보고, 타임라인 순으로 어떻게 실패했는지 설명해 줘."*
* **성능(Performance) 및 보안(Security) 상태 파악**
  * *"2026-07-20 14:00~15:00 사이에 응답시간이 급증한 원인을 access.log에서 찾아줘."*
  * *"로그 파일 중에 PII(개인 식별 정보)나 비밀번호가 노출된 부분이 있는지 스캔해 줘."*

---

## 5. 핵심 기능 및 가드레일 (Core Features & Guardrails)

### 5.1 Read-Only 안전 가드레일 (Safety Harness)
* Agent에 제공되는 도구 목록을 읽기 및 탐색 전용 도구(파일 검색, 리더 등)로 엄격 제한하여 원본 데이터 훼손 원천 차단.

### 5.2 사용자 도메인 지식 주입 (Domain Knowledge Injection)
```yaml
# log_agent_config.yaml 예시
log_analysis_config:
  analysis_focus: "security_and_performance" # 에러뿐만 아니라 목적 명시
  target_identifiers: ["blk_-", "TraceID", "ClientIP"]
  known_markers:
    - "WARN dfs.DataNode$DataXceiver"
    - "Invalid login attempt"
    - "Timeout"
```

---

## 6. 단계별 개발 로드맵 (Roadmap)

* **Phase 1 (MVP)**
  * Read-Only Toolset 기반 Agent Harness 구성 및 1차 이상 탐지 알고리즘 구현
* **Phase 2 (도메인 지식 & 템플릿 강화)**
  * YAML 기반 User Pattern Config 주입 엔진 개발
* **Phase 3 (리포팅 및 Multi-Agent 연동)**
  * Triage, Investigation, Reporting 역할을 수행하는 Subagent 계층 구조 분리 및 연동

---

## 7. 참고 사항 (Reference: Popular Skills & MCP Servers)

로그 분석 에이전트 개발 시 기존 오픈소스 커뮤니티에서 검증된 도구/방식을 벤치마킹할 수 있습니다.

### MCP (Model Context Protocol) Servers
> 대용량 데이터 필터링을 에이전트가 직접 쉘로 치지 않고, 전용 서버가 백엔드에서 처리 후 결과만 돌려주는 안정적인 방식입니다.

* **[Local Logs MCP Server](https://github.com/mariosss/local-logs-mcp-server)**
  - 실시간 Log tailing, 에러 트래킹, 텍스트 패턴 서치 전문 MCP. 파일 파싱 로직을 서버 단에 오프로드하는 구조로 벤치마킹하기 좋습니다.
* **[LogAnalyzer MCP](https://mcp-marketplace.io/server/io-github-fato07-log-analyzer-mcp)**
  - AI 기반 로그 분석에 특화되어 다수의 로그 포맷 파싱(Syslog, JSON, Docker 등) 및 스마트 에러 추출을 제공하는 MCP.
