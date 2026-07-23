## 대용량 로그파일 분석 전문 Agent 개발 계획

> **작성 기준일:** 2026-07-23  
> **컨텍스트:** Cline SDK 기반 자체 플랫폼 "Perspective" 위에 대용량 파일 로그 분석 전문 Agent 구현  
> **핵심 타겟:** 개발자가 로컬 또는 서버 환경에 위치한 대용량 파일 로그를 분석할 때, CLI(터미널) 환경에서 직접 복잡한 쿼리나 스크립트를 짜는 수고를 덜어주고 즉각적인 인사이트를 제공하는 **개발자 보조 도구 (Co-pilot)**


---

> [!IMPORTANT]
> 목표 확인이 최우선입니다. "대용량 로그 분석 Agent"가 의미하는 바가:
>
>>(A) "개발자가 로그를 분석할 때 AI가 도와주는 것"인지   <-----------------------------
>> 
>>(B) "기존 ELK/Splunk를 대체하는 AI 기반 로그 분석 플랫폼"인지
>>
>>(C) "장애 발생 시 자동으로 로그를 분석하고 근본 원인을 보고하는 자율 Agent"인지
>> 
>>에 따라 아키텍처와 리소스가 완전히 달라집니다.
>>
>=> 개발자 보조도구 > 자율 모니터링
> 
> 다양성
>> 도메인 다양성 -	웹서버 access log, 애플리케이션 structured log, 커널 syslog, 분산 시스템 trace… 각각 파싱/분석 방법이 전혀 다름
>>
>>"분석"의 정의 부재	- "에러 원인 찾기", "이상 패턴 탐지", "성능 병목 식별", "보안 침해 탐지" 사용 목적에 따라 Agent 설계가 완전히 달라짐


---

## 0. Executive Summary

"대용량 로그 분석"이라는 목표를 성공적으로 달성하기 위해 다음 2가지 트랙을 진행합니다.

| 트랙 | 목적 | 기간(추정) |
|:---|:---|:---:|
| **A. 타 도구 벤치마킹** | 1GB 이상의 대용량 로그를 대상으로 타 AI 도구들의 한계점 및 최적의 접근 전략 파악 | 1주 |
| **B. Perspective 아키텍처 설계** | 제약(Constraints) 및 툴 권한(Permissions)을 활용하여 일반화된 로그 분석 워크플로우 설계 | 트랙 A 이후 1주 |

---

## 1. 트랙 A: 타 AI 도구 벤치마킹 실험

### 1.1 실험 대상 도구

| 도구 | 실험 이유 |
|:---|:---|
| **Claude Code** | 최대 컨텍스트(200K) + 파일 읽기/터미널 툴 능력 확인 |
| **Antigravity** | Gemini의 1M+ 대형 컨텍스트 처리 한계 확인 |
| **Cline (현재 오픈소스)** | 베이스라인. SDK가 기본 제공하는 기능 수준 확인 |

### 1.2 대용량 샘플 로그(1GB 이상) 준비

실험의 핵심은 LLM이 한 번에 읽을 수 없는 **대용량(Out-of-Context) 데이터**를 어떻게 툴을 사용해 처리하는지 확실하게 검증하는 것입니다.

| 로그 유형 | 데이터셋 다운로드 출처 / 생성 방법 |
|:---|:---|
| **다양한 서버 시스템 로그** (HDFS, Linux, Apache 등) | **Loghub Dataset (Zenodo)**: [다운로드 링크](https://zenodo.org/records/8196385)<br>- 세계에서 가장 널리 쓰이는 연구용 77GB 대형 로그 집합. |
| **Nginx / Apache Access Log** | **Kaggle**: [Web Server Access Logs](https://www.kaggle.com/search?q=web+server+access+logs)<br>- 수백 MB 단위의 리얼 월드/합성 웹서버 로그 다수 존재. 여러 개를 병합하여 1GB 이상 구성. |
| **합성 대용량 로그 생성** (필요시) | 파이썬 **Faker** 라이브러리 또는 `flog`([GitHub](https://github.com/mingrammer/flog)) 툴을 활용하여 원하는 포맷과 크기(예: 1GB 이상)의 에러 로그를 직접 생성. |

### 1.3 벤치마킹 시나리오

동일한 샘플 로그(최소 1GB 이상)를 제공하고 각 도구에 아래 지시를 내립니다.

| # | 시나리오 | 타겟 능력 |
|:---|:---|:---|
| S1 | "이 로그에서 HTTP 500 에러의 빈도와 패턴을 분석해줘" | 대용량 기본 파싱 및 쉘/스크립트 집계 전략 |
| S2 | "2026-07-20 14:00~15:00 사이에 응답시간이 급증한 원인을 찾아줘" | 대용량 데이터 내 시간 범위 필터링 + 상관관계 분석 |
| S3 | "분산 트랜잭션 X가 실패한 root cause를 trace log에서 추적해줘" | 여러 파일에 걸친 상관관계(Correlation ID) 추적 및 인과 추론 |
| S4 | "이 1GB 로그 파일에서 보안 침해(비정상 접근) 징후를 찾아줘" | 대용량 청킹 전략 + 보안 도메인 지식 기반 탐색 |

---

## 2. 트랙 B: 일반화된 로그 분석 파이프라인 설계

로그의 종류(Syslog, Nginx, App log 등)에 관계없이 범용적으로 적용할 수 있는 **일반화된 멀티 에이전트 파이프라인**을 설계합니다. 단일 에이전트가 모든 것을 처리하기보다, AI Best Practice에 맞게 단계를 나눕니다.

```mermaid
graph TD
    User([사용자 요청]) --> Triage[1. Triage Agent<br>(Context Discovery & Triage)]
    Triage -->|타임라인/키워드 필터링 룰 전달| TriageTool[(터미널/조회 도구)]
    TriageTool -->|압축된 관련 로그| Investigate[2. Investigation Agent<br>(상관관계 및 인과 추론)]
    Investigate -->|추가 검색 요청| InvestigateTool[(터미널/스크립트 도구)]
    InvestigateTool --> Investigate
    Investigate -->|발견된 원인/증거| Report[3. Reporting Agent<br>(RCA 문서화 및 시각화)]
    Report --> Final([분석 리포트 및 해결책 제시])
```

### 2.1 Step 1: Context Discovery & Triage (초기 맥락 파악 및 필터링)

Agent가 대용량 로그를 무작정 읽거나 검색하기 전에 분석의 '맥락'을 좁히고 데이터를 압축하는 핵심 첫 단계입니다.

* **초기 맥락 파악 (Context Discovery):**
  Agent는 다음 질문들에 대한 답을 사용자에게 묻거나 스스로 파악해야 합니다.
  1. **분석 목적 (Goal)**
     - 장애/에러 원인 추적 (RCA)인가?
     - 통계 분석(Statistics & Patterns)인가?
     - 이상 패턴(Anomaly) 탐지인가?
     - 성능 병목(Performance) 식별인가?
     - 보안 침해(Security) 조사인가?
  2. **타겟 로그 및 파일 사이즈 (Scope & Size)**
     - 어떤 파일(들)을 분석해야 하는가?
     - 분산 환경인지 단일 시스템인지?
     - 파일의 물리적 크기(`ls -lh` 등)를 사전 체크하여 데이터 처리 전략(전체 읽기 vs 청킹/필터링) 결정.
  3. **타임라인 및 범위 (Time Frame)**
     - 장애가 발생한 정확한 시간대(Window)는 언제인가?
  4. **마커 및 이상 패턴 (Markers/Clues)**
     - 사용자가 이미 알고 있는 에러 코드, Exception 이름, Correlation ID, 특정 IP 주소 등이 있는가?
  5. **로그 도메인 및 유형 (Domain & Log Type)**
     - 웹서버 Access Log(Nginx/Apache), 애플리케이션 Structured Log(JSON), 커널 Syslog, 분산 시스템 Trace 중 어느 것에 해당하는가? (도메인 특화 파싱 전략 적용)
  6. **로그 구조 이해 (Schema Parsing)**
     - 로그의 첫 10줄을 읽어 타임스탬프 형식 및 구분자(JSON, CSV 등) 파악.

* **필터링 (Triage):**
  - 파악된 위 힌트(시간대, 키워드, 정규식 구조)를 바탕으로 최적의 텍스트 조회/필터링 툴(내장 유틸리티 등)을 유연하게 사용하여 분석 대상 범위를 전체 파일 크기에서 LLM이 소화할 수 있는 수 MB 단위 이하로 좁힙니다.

### 2.2 Step 2: Investigation (심층 분석)

* **상관관계 추적:** 좁혀진 로그 조각들을 바탕으로 다중 파일 간 연관성을 추적(예: Access Log 에러를 App Log의 Exception과 교차 검증)합니다.
* **목적 정렬 (Goal Alignment):** 단순 에러 추적을 넘어, Step 1에서 파악한 '분석 목적'(통계 산출, 성능 병목, 보안 탐지 등)에 완벽하게 부합하는 심도 있는 분석을 수행합니다.
* **레거시 시스템 대응:** Trace ID가 없는 구형 시스템 로그의 경우, 타임스탬프 근접성과 IP 주소 기반의 휴리스틱(Heuristic) 상관관계 분석 알고리즘을 강하게 적용합니다.

### 2.3 Step 3: Reporting (문서화)

* 발견된 Root Cause나 인사이트를 정리하고 확실한 근거(Log snippet)와 함께 제공합니다.
* **맞춤형 출력:** 초기 분석 목적에 맞춰 최종 리포트의 형태(예: 통계 요약표, 장애 타임라인, 보안 권고안 등)를 유동적으로 생성하여 사용자에게 최적화된 결과물을 전달합니다.

### 2.4 Perspective 컨셉 (제약 및 권한) 매핑

Perspective 플랫폼 특성상, 파이프라인의 안전성을 보장하기 위해 다음과 같은 제약을 둡니다.

| 권한/제약 | 설정 | 설명 |
|:---|:---:|:---|
| **터미널 실행 (Strict Read-only)** | `bash` (✅ 제한적) | `grep`, `awk`, `tail`, `jq` 등 조회성 커맨드만 허용. `rm`, `mv` 등 파괴적 행위는 물론 **임시 스크립트 작성(예: python script.py 생성 후 실행)도 원천 차단**하여 완전한 안전 환경(Sandbox)을 보장합니다. |
| **파일 읽기** | `read_file` (✅) | LLM이 읽기 적합한 사이즈(수천 줄 이내)로 제한. |
| **파일 쓰기** | `write_file` (❌) | 로그 원본 훼손 방지. (단, 분석 리포트 출력을 위한 마크다운 파일 쓰기는 예외 허용) |
| **네트워크 접근** | `fetch_web` (❌) | 민감한 로그 데이터의 외부 API/웹서버 전송(유출) 원천 차단. |
| **Pll 마스킹 훅 (Hook)** | `beforeTool` 적용 | 에이전트가 툴 결과를 프롬프트로 받기 전, IP 주소, 주민번호 등 민감 정보를 `[MASKED]` 처리. |

---

## 3. 단계별 실행 로드맵

### Phase 1: 벤치마킹 및 워크플로우 검증 (1주)
- [ ] 1GB 이상의 Loghub Nginx/Apache 및 커스텀 에러 로그 데이터셋 준비.
- [ ] Claude Code, Antigravity, 오픈소스 Cline을 이용해 시나리오 4종 벤치마킹.
- [ ] 에이전트들이 1GB 로그를 만났을 때 어떤 터미널 명령(grep, jq 등)을 선호하는지 패턴 추출.

### Phase 2: Perspective Agent Prototype 개발 (2주)
- [ ] Cline SDK 기반으로 `Context Discovery & Triage` 프롬프트를 주입한 커스텀 에이전트 생성.
- [ ] `Triage -> Investigate -> Report` 파이프라인 로직 구현. (멀티 에이전트 또는 단일 에이전트의 명시적 단계(Plan/Act) 적용)
- [ ] Perspective 제약(Strict Read-only 터미널, 임시 파일 생성 차단, 네트워크 격리) 플러그인 훅 적용.
- [ ] 사내 개발자 대상 1GB 샘플 분석 알파 테스트 진행.

---

## 4. 참고 사항 (Reference: Popular Skills & MCP Servers)

로그 분석 에이전트 개발 시 기존 오픈소스 커뮤니티에서 검증된 도구/방식을 벤치마킹할 수 있습니다.

### MCP (Model Context Protocol) Servers
> 대용량 데이터 필터링을 에이전트가 직접 쉘로 치지 않고, 전용 서버가 백엔드에서 처리 후 결과만 돌려주는 안정적인 방식입니다.

* **[Local Logs MCP Server](https://github.com/mariosss/local-logs-mcp-server)**
  - 실시간 Log tailing, 에러 트래킹, 텍스트 패턴(grep) 서치 전문 MCP. 파일 파싱 로직을 서버 단에 오프로드하는 구조로 벤치마킹하기 좋습니다.
* **[LogAnalyzer MCP](https://github.com/djm81/log_analyzer_mcp)**
  - AI를 활용한 로그 파일 상호작용 및 분석 도구 모음.

### Skills 
  
