# XX전자 사내 Cline 기반 대용량 Log 분석 Agent 설계

## 1. 개요

**Cline 업스트림 기반 XX전자 자체 Cline**에서 동작하는 **대용량 Log 분석 Agent**를 `@cline/sdk` Plugin으로 설계한다. XX전자 사내 SW 개발 엔지니어(가전·모바일폰·TV·통신 제품군)가 임베디드/모바일/플랫폼/네트워크 로그를 IDE 내에서 분석할 수 있도록 지원한다.

### 대상 사용자 및 로그 유형

| 제품군 | 대상 엔지니어 | 주요 로그 유형 |
|--------|-------------|---------------|
| 📱 모바일폰 | Android Framework / App 개발자 | Android logcat, ANR trace, tombstone, bugreport |
| 📺 TV | Tizen/webOS 플랫폼 개발자 | Tizen dlog, 사내 플랫폼 로그, CEC/HDMI 이벤트 로그 |
| 🏠 가전 | 펌웨어/IoT 개발자 | 사내 펌웨어 시리얼 로그, RTOS 트레이스, OTA 업데이트 로그 |
| 📡 통신(NW) | 5G/네트워크 장비 개발자 | 5G 모뎀 로그, 패킷 덤프, 기지국 프로토콜 연동 로그 |
| 🔧 공통 | BSP/커널 개발자 | kernel dmesg, ftrace, /proc/kmsg |

### 선택한 AI 품질속성 (4개)

| # | 품질속성 | 선택 이유 |
|---|---------|----------|
| 2 | **기능 정확성 (Functional Correctness)** | Kernel Panic, ANR, 펌웨어 크래시 분석 정확성이 제품 품질에 직결 |
| 7 | **기능 적응성 (Functional Adaptability)** | 범용 LLM 모델만으로는 사내 시스템 특유의 이상(Abnormal) 징후 패턴이나 고유 비즈니스 로직을 놓치기 쉬움. 따라서 사내 도메인 지식/로그 포맷에 적응할 뿐 아니라, **다양한 분석 목적(에러 원인 추적, 성능 병목 식별, 보안 탐지 등)**과 **실행 환경(IDE ↔ 자율 Harness)**에 맞춰 분석 전략과 안전 제약(read-only)을 스스로 유연하게 강제해야 함 |
| 6 | **수행 효율성 (Performance Efficiency)** | 사내 Token Budget은 월 단위로 충분하나, 자원 효율 관점에서 Token 사용량이 최소한 유지되는 수준인지 지속적인 모니터링과 관리가 필요함 |
| 9 | **설명 용이성 (Explainability)** | 에이전트가 어떤 근거로 로그를 분석했는지 사용자가 먼저 명확히 이해할 수 있어야 하며, 이를 바탕으로 동료에게도 논리적으로 설명할 수 있도록 분석 결과가 제공되어야 함 |

---

## 2. QA 시나리오 (Bass-Style Quality Attribute Scenarios)

### QA-1: 기능 정확성 (Functional Correctness)

| 항목 | 내용 |
|------|------|
| **Source** | 모바일폰 Android Framework 개발 엔지니어 |
| **Stimulus** | 필드 테스트 중 수집된 800MB bugreport(logcat + ANR trace + tombstone 통합 로그)에 대해 "앱 ANR 발생 근본 원인 분석" 요청 |
| **Artifact** | Log Analysis Engine (LLM 추론 모듈 + 도구 체인) |
| **Environment** | XX전자 사내 Cline IDE 정상 운영 상태 |
| **Response** | ANR 발생 시점의 Main Thread 블로킹 원인을 시간순 이벤트 체인으로 식별하고, 근본 원인(예: Binder 교착, ContentProvider 지연)을 정확히 제시 |
| **Measure** | ① 근본 원인 식별 정확도 ≥ 85% (사내 벤치마크 대비) ② False Positive Rate < 10% ③ 인용된 로그 라인 참조 정확도 100% (존재하지 않는 라인을 인용하지 않음) |

---

### QA-2: 기능 적응성 (Functional Adaptability)

이 속성은 Agent가 새로운 **로그 포맷/도메인 지식**에 적응하는 능력(QA-2a)과 **실행 환경(IDE ↔ 자율 Harness)**에 적응하여 스스로 안전 제약을 강제하는 능력(QA-2b)을 포괄한다.

#### QA-2a: 도메인 지식 적응
| 항목 | 내용 |
|------|------|
| **Source** | TV 플랫폼 SW 개발 엔지니어 (신규 사용자) |
| **Stimulus** | Agent가 처음 보는 **사내 TV 플랫폼 독자 로그 포맷**(독자 타임스탬프 `[YYMMDD-HH:MM:SS.fff/TID]`, 독자 에러 코드 `TV-AV-ERR-2xxx`). 엔지니어가 다음 도메인 지식을 제공: "TV-AV-ERR-2로 시작하면 A/V 코덱 디코딩 실패. 이 시스템은 Pipeline 구조로 `pipe-session-id`로 연결되며, HDMI-CEC 이벤트와 연관 분석이 필요함" |
| **Artifact** | Domain Adaptation Module (FormatAdapter + DomainMemory + UserRuleEngine) |
| **Environment** | 최초 사용 시 (사전 학습 없는 Cold Start 상태) |
| **Response** | ① 비정형/다양한 사내 로그 포맷을 자동 감지하거나 사용자 힌트로 파싱 규칙 생성 ② **사용자 도메인 지식을 메모리에 저장하여 이후 분석에 자동 반영** ③ 다음 분석부터 "TV-AV-ERR-2xxx = A/V 디코딩 실패"를 자동 인식하고 `pipe-session-id` 기반 파이프라인 연쇄 추적 수행 |
| **Measure** | ① 새 포맷 적응에 사용자와 2회 이내 대화로 완료 ② 저장된 도메인 규칙의 이후 분석 반영률 100% ③ 사용자 정의 규칙 추가 후 재시작 없이 즉시 적용 |

#### QA-2c: 분석 목적 다변화 적응
| 항목 | 내용 |
|------|------|
| **Source** | 통신망(NW) 5G 네트워크 장비 개발자 |
| **Stimulus** | 에러 분석(패킷 드랍 원인)이 아닌, "특정 시간대 기지국 프로토콜 연동 지연(Latency) 병목 구간 식별"이라는 **성능 병목 탐지** 목적의 분석을 요청 |
| **Artifact** | Domain Adaptation Module (Dynamic Strategy Selector) |
| **Environment** | 성능 분석 또는 보안 탐지 목적의 쿼리 발생 시 |
| **Response** | ① 질의의 의도(에러 파악, 성능 분석, 보안/비정상 접근 탐지 등)를 감지 ② 목적에 맞게 분석 전략(예: 성능 분석 시에는 타임스탬프 델타 연산 및 지연율 높은 구간 집중 탐색)을 동적으로 변경하여 리포팅 |
| **Measure** | ① 3가지 이상의 상이한 분석 목적(에러, 성능, 보안 등) 요구사항에 대응 성공률 90% 이상 ② 목적 기반 분석 전략 전환 시 추가적인 사용자 프롬프팅 없이 1회 질의로 달성 |

#### QA-2b: 실행 환경 적응 (안전 제약 강제)
| 항목 | 내용 |
|------|------|
| **Source** | CI/CD 자동화 파이프라인 (자율 Harness 환경) |
| **Stimulus** | 야간 자동화 Harness에서 Agent가 사람의 개입 없이 자율적으로 TV 필드 테스트 로그 500건을 일괄 분석하는 상황. Agent가 LLM 추론 과정에서 "로그를 수정하면 더 잘 분석할 수 있다" 또는 "시스템을 재시작하면 문제가 해결된다"는 판단을 내릴 수 있음 |
| **Artifact** | SafetyGuard (ToolPolicyEnforcer + ReadOnlyFileGuard + ActionAuditLog) |
| **Environment** | 무인 자율 실행 환경 (Harness/CI에서 사람 승인 없이 동작) |
| **Response** | ① 실행 환경이 Harness임을 감지하고 스스로 read-only 정책을 강제 ② 파일 쓰기·삭제·시스템 명령 실행을 구조적으로 차단 ③ LLM이 write 계열 행동을 제안하더라도 실행 단계에서 차단하고 감사 로그에 기록 ④ 허용된 도구 목록(allowlist) 외의 도구 호출 시도를 거부 |
| **Measure** | ① 로그 파일에 대한 쓰기 시도 차단율 = 100% (구조적 불가) ② 시스템 명령(exec, spawn 등) 실행 차단율 = 100% ③ 허용 목록 외 도구 호출 차단율 = 100% ④ 감사 로그 누락률 = 0% ⑤ Harness 모드에서 Human-in-the-loop 없이도 제약 유지 |

---

### QA-3: 수행 효율성 — Token 자원 효율 (Performance Efficiency)

| 항목 | 내용 |
|------|------|
| **Source** | 시스템 자체 (사내 LLM Token 사용량 모니터링 및 효율화 필요) |
| **Stimulus** | 가전 IoT 디바이스에서 수집된 2GB 펌웨어 시리얼 로그에 대해 "OTA 업데이트 실패 원인 분석" 요청 |
| **Artifact** | PatternCompressor + StatisticalPrefilter |
| **Environment** | 사내 Token Budget 월 단위로 설정된 상태 |
| **Response** | ① 통계적 사전 필터링으로 정상 heartbeat/센서 데이터 로그를 LLM에 전송하지 않음 ② "Sensor OK" 같은 반복 상태 메시지를 압축하여 토큰 소비 절감 ③ 기준량 내에서 분석 완료 또는 초과 예상 시 사용자에게 경고 알림 ④ 분석 완료 후 실제 토큰 사용량 리포트 제공 |
| **Measure** | ① 전체 로그 대비 LLM에 실제 전송되는 텍스트 비율 ≤ 5% ② 동일 분석 결과 대비 Naive 방식(전체 전송) 대비 Token 사용량 ≤ 50% ③ 불필요한 Token 낭비율 0% (기준량 도달 시 경고 알림 + 부분 결과 반환) ④ 중복 패턴 압축률 ≥ 70% (동일 heartbeat 메시지 N회 반복 → 1회 + 빈도 메타데이터) |

---

### QA-4: 설명 용이성 (Explainability)

| 항목 | 내용 |
|------|------|
| **Source** | 가전 펌웨어 개발 엔지니어 |
| **Stimulus** | 엔지니어가 "이 OTA 업데이트 실패 로그 분석해줘" 요청 |
| **Artifact** | Reasoning Trace Module + Evidence Linker |
| **Environment** | 분석 완료 후 결과 제시 단계 |
| **Response** | ① 판단 근거가 된 로그 라인들을 원본 파일 위치와 함께 제시 ② 추론 체인(Wi-Fi init timeout → DHCP 실패 → OTA 서버 접속 불가 → 다운로드 중단)을 단계별로 설명 ③ 각 단계의 확신도(Confidence)를 수치로 표시 ④ 클릭 시 원본 로그 해당 라인으로 점프 ⑤ **엔지니어의 추가 요청 없이도** 판단 근거를 리포트용 마크다운으로 자동 요약 생성 |
| **Measure** | ① 모든 결론에 최소 1개 이상의 원본 로그 증거 첨부 ② 추론 체인의 각 단계가 자연어로 설명됨 ③ 원본 라인 참조 링크의 유효율 100% ④ 사용자 만족도(설명 이해도) ≥ 4.0/5.0 |

---

### 대체 시나리오: Loghub HDFS_v1 오픈소스 데이터셋 기반

> [!NOTE]
> 사내 제품군 로그 확보가 어려운 경우, 아래 오픈소스 데이터셋 기반 대체 시나리오로 각 QA의 정량적 검증이 가능하다.
> **데이터셋**: [Loghub HDFS_v1](https://github.com/logpai/loghub) — `HDFS.log` (1.47 GB, 11,175,629 라인) + `anomaly_label.csv` (575,061 블록, Anomaly 16,838건/2.9%)

#### QA-1 대체: 기능 정확성 — HDFS Anomaly 블록 탐지 정확도

| 항목 | 내용 |
|------|------|
| **Source** | 검증 담당 엔지니어 |
| **Stimulus** | 1.47GB HDFS.log에 대해 "이상치 현황 분석해줘" 요청 |
| **Artifact** | Log Analysis Engine (LLM 추론 모듈 + 도구 체인) |
| **Environment** | Loghub HDFS_v1 데이터셋 + `anomaly_label.csv` Ground Truth |
| **Response** | Agent가 블록 라이프사이클(`allocate → receive → replicate → serve → delete`)에서 누락/오류 패턴을 식별하여 Anomaly 블록 목록을 도출 |
| **Measure** | `anomaly_label.csv` Ground Truth 대비: ① **Recall ≥ 80%** (16,838 Anomaly 블록 중 탐지 비율) ② **Precision ≥ 70%** (Agent가 Anomaly로 지목한 블록 중 실제 Anomaly 비율) ③ 인용된 로그 라인 참조 정확도 100% |

> **검증 방법**: Agent가 출력한 Anomaly 블록 ID 목록과 `anomaly_label.csv`의 `Label=Anomaly` 목록을 대조하여 Recall/Precision/F1 자동 산출.

#### QA-2 대체: 기능 적응성 — HDFS 도메인 지식 적응 + 분석 목적 전환

| 항목 | 내용 |
|------|------|
| **Source** | 검증 담당 엔지니어 (Cold Start 상태) |
| **Stimulus** | (a) Agent가 처음 보는 HDFS 로그 포맷에서, 엔지니어가 "`blk_` 접두사가 블록 ID이고, 정상 흐름은 `allocateBlock → Receiving → Received → addStoredBlock → ask to replicate → Transmitted → Served → delete → Deleting`이다"라는 도메인 지식을 제공 (b) 이후 "에러 분석" 대신 "복제 실패 패턴을 가진 블록들의 성능 병목(복제 지연 시간) 분석해줘"로 분석 목적을 전환 |
| **Artifact** | Domain Adaptation Module (FormatAdapter + DomainMemory + Dynamic Strategy Selector) |
| **Environment** | 사전 학습 없는 Cold Start → 도메인 지식 주입 후 |
| **Response** | ① HDFS 로그 포맷(`081109 hhmmss msec INFO ...`)을 자동 감지 ② 사용자가 가르친 블록 라이프사이클을 메모리에 저장하여 이후 분석에 반영 ③ 목적 전환 시 에러 탐지가 아닌 타임스탬프 델타 기반 복제 지연 분석으로 전략 자동 전환 |
| **Measure** | ① 포맷 감지 2회 이내 대화로 완료 ② 저장된 라이프사이클 규칙의 이후 분석 반영률 100% ③ 목적 전환 시 추가 프롬프팅 없이 1회 질의로 전략 변경 |

#### QA-3 대체: 수행 효율성 — 1.47GB HDFS 로그 Token 유지 / 절감

| 항목 | 내용 |
|------|------|
| **Source** | 시스템 자체 (Token 사용량 모니터링) |
| **Stimulus** | 1.47GB HDFS.log (11.1M 라인)에 대해 "Anomaly 블록 식별 및 근본 원인 분석" 요청 |
| **Artifact** | PatternCompressor + StatisticalPrefilter |
| **Environment** | 사내 Token Budget 월 단위로 설정된 상태 |
| **Response** | ① 정상 블록의 반복 `Served block` 로그(전체의 ~70%)를 압축/스킵 ② `WARN`/`ERROR` 밀도가 높은 시간대 청크를 우선 분석 ③ 동일 패턴의 정상 라이프사이클 로그를 "원본 1개 + 반복 N회" 메타데이터로 치환 |
| **Measure** | ① 전체 11.1M 라인 대비 LLM에 실제 전송되는 텍스트 비율 ≤ 5% ② Naive 방식(전체 전송) 대비 Token 사용량 ≤ 50% ③ 압축 후에도 QA-1 대체 시나리오의 Recall 저하 ≤ 5%p |

#### QA-4 대체: 설명 용이성 — HDFS Anomaly 근본 원인 추론 체인

| 항목 | 내용 |
|------|------|
| **Source** | 검증 담당 엔지니어 |
| **Stimulus** | 엔지니어가 "Anomaly 블록 `blk_-3544583377289625738`의 원인 분석해줘" 요청 |
| **Artifact** | Reasoning Trace Module + Evidence Linker |
| **Environment** | 분석 완료 후 결과 제시 단계 |
| **Response** | ① 해당 블록의 라이프사이클에서 `ask to replicate` 단계 누락을 식별 ② 추론 체인(`복제 단계 누락 → 3개 노드만 보유 → replication factor 미달 → 삭제 시 volumeMap 불일치 → BlockInfo not found WARN`)을 단계별로 설명 ③ 각 단계의 확신도 표시 ④ 원본 로그 라인 참조 딥링크 ⑤ **추가 요청 없이도** 자동 마크다운 리포트 생성 |
| **Measure** | ① 모든 결론에 최소 1개 이상의 원본 로그 증거(라인 번호) 첨부 ② 추론 체인의 각 단계가 자연어로 설명됨 ③ 정상 블록(예: `blk_-1608999687919862906`)과의 비교 분석이 포함됨 ④ 원본 라인 참조의 유효율 100% |

---


## 3. QA 시나리오별 Architecture Approach

본 장에서는 각 QA 시나리오 요구사항을 달성하기 위한 구조적 대안(Alternatives)을 도출하고, 장단점을 비교하여 최종 Architecture Approach를 선택한다.

> **TBD (To Be Determined)**: 본 설계안에 대한 전체 아키텍처 다이어그램은 접근 방식 확정 후 상세 설계 시 업데이트.

### 3.1 기능 정확성 (QA-1)

* **목표**: Hallucination을 방지하고 실제 존재하는 로그 라인만 근거로 인용해야 함.
* **Option A: RAG (Retrieval-Augmented Generation) 기반 Exact Match**
  * **장점**: 사전에 벡터화된 청크를 그대로 가져오므로 원본 데이터 변형이 적음.
  * **단점**: 로그 특성상 단순 유사도 검색(Vector Search)은 시간순 맥락과 원인-결과 추적에 취약하며, 라인 번호 매핑이 어려움.
* **Option B: ReAct 루프 + 도구 기반 Ground Truth 검증 (Selected)**
  * **장점**: LLM이 검색 도구(`grep_log`, `search_by_time`)를 직접 사용하며 추론하고, 최종 결과 도출 전 `GroundTruthVerifier`가 인용된 라인 번호를 실제 원본 파일과 대조 검증.
  * **단점**: 다중 도구 호출로 인한 처리 시간(Latency) 증가.
  * **결정 사유**: 처리 시간이 다소 걸리더라도, 제품 품질과 직결되는 '정확성'과 '허위 사실 배제(Hallucination 0%)'가 최우선이므로 Option B를 선택.

### 3.2 기능 적응성 (QA-2a, QA-2c)

* **목표**: 다양한 제품군의 비정형 로그 포맷과 도메인 지식, 분석 목적(에러/성능/보안)에 적응.

> [!IMPORTANT]
> 현재 아래 3가지 Option을 검토 중이며, **최종 선택은 TBD**입니다. Cline 업스트림의 Skill 체계를 그대로 활용할지, SDK의 Plugin/Perspective 런타임을 활용하여 자체 구현할지가 핵심 분기점입니다.

* **Option A: 사내 도메인 특화 모델(Fine-Tuning) 구축**
  * **장점**: 모델 내재적 지식으로 인해 프롬프트 길이가 짧아지고 성능이 안정적.
  * **단점**: 사내 수많은 제품군과 끊임없이 변하는 에러 코드/포맷마다 재학습이 필요하여 유지보수 비용이 막대함.

* **Option B: Cline Skill 기반 — 슬래시 커맨드로 사용자가 진입하는 방식** ([cline/cline](https://github.com/cline/cline))
  * **개요**: Cline 업스트림이 제공하는 **Skill** 체계를 활용. 제품군별 로그 분석 지식을 `SKILL.md` 파일에 정의하고, 사용자가 `/log-analyze-tv`, `/log-analyze-mobile` 등 **슬래시 커맨드**로 원하는 분석 스킬을 선택하여 진입하는 방식.
  * **장점**:
    - Cline의 기존 Skill 인프라(자동 탐색, Progressive Loading, Enable/Disable)를 그대로 활용하여 **개발 비용이 낮음**.
    - 도메인 지식을 `SKILL.md` + 번들 리소스(에러코드 사전 JSON 등)로 **선언적 관리** 가능.
    - 사용자가 슬래시 커맨드로 명시적으로 스킬을 선택하므로 **진입 의도가 명확**함.
  * **단점**:
    - Skill은 기본적으로 **프롬프트 인스트럭션 주입** 방식이므로, 도구 호출 정책 강제나 런타임 레벨의 동적 전략 전환(성능/보안 목적 분기) 같은 **프로그래매틱 제어가 제한적**.
    - 분석 목적에 따른 동적 전략 전환(QA-2c)을 Skill 내 프롬프트만으로 유도해야 하므로 **LLM의 지시 이행에 의존**.
    - `teach_domain`처럼 사용자가 런타임에 새 지식을 가르치고 영구 저장하는 흐름을 Skill 체계만으로 구현하기에는 **커스텀 도구 등록이 추가로 필요**.

* **Option C: `@cline/sdk` Plugin + Perspective 런타임 활용 — 자체 기능 구현** ([cline/cline SDK](https://github.com/cline/cline))
  * **개요**: `@cline/sdk`가 제공하는 **Plugin 아키텍처**(커스텀 도구 등록, `beforeRun`/`beforeTool`/`afterRun` 라이프사이클 훅)와 **Perspective 런타임**(IDE ↔ CI/CD Harness 간 세션 이관 가능한 공유 런타임)을 활용하여, 로그 분석 전용 Agent를 자체 Plugin으로 구현하는 방식.
  * **장점**:
    - Plugin 내에서 커스텀 도구(`grep_log`, `teach_domain` 등)를 **Zod 스키마 기반으로 타입 안전하게 등록**하고, 허용된 도구만 `allow_tool`로 선언하는 **Application 수준의 엄격한 Allowlist 관리**로 Safety Guard(QA-2b)를 Plugin 레벨에서 통합 구현 가능. `beforeTool` 훅에서 미허용 도구 호출을 가로채 차단하고, 모든 통과/차단 내역을 감사 로그(`ActionAuditLog`)에 기록.
    - Perspective 런타임 덕분에 IDE에서 시작한 분석 세션을 CI/CD Harness에서 이어받는 **Surface 간 세션 이관**이 가능하며, Harness 환경 진입 시 자동으로 read-only 정책이 강제되어 QA-2b(Harness 환경 적응)가 자연스럽게 통합됨.
    - `Dynamic Strategy Selector`와 `DomainMemory`를 **프로그래매틱하게 제어**할 수 있어, LLM 프롬프트 의존도를 낮추고 더 정밀한 전략 전환 가능.
  * **단점**:
    - SDK의 Plugin API와 Perspective 구조에 대한 **깊은 이해와 개발 비용**이 필요.
    - 업스트림 SDK API 변경 시 **유지보수 부담**이 Option B 대비 큼.

* **결정 사유**: *검토 중 (TBD)*
  - Option A는 유지보수 비용 문제로 **제외 방향**.
  - Option B(Skill)와 Option C(SDK Plugin)는 각각 **낮은 진입 비용 vs. 높은 제어력**이라는 트레이드오프가 있어, 사내 Cline 커스터마이징 수준과 운영 역량을 고려하여 최종 결정 예정.
  - 특히 Option C는 Safety Guard(QA-2b)까지 `allow_tool` Allowlist + 라이프사이클 훅으로 통합 관리할 수 있다는 구조적 이점이 있음.


### 3.3 수행 효율성 (QA-3)

* **목표**: 대용량 로그 분석 시 Token 낭비 방지.
* **Option A: 대용량 Context Window LLM 무조건 활용**
  * **장점**: 구현이 가장 단순(전체 로그를 프롬프트에 삽입).
  * **단점**: 분석당 Token 낭비가 극심하며, 노이즈(정상 센서 데이터 등)로 인해 모델의 집중력이 분산(Lost in the middle)될 위험이 큼.
* **Option B: Client-Side 통계적 사전 필터링 및 패턴 압축 (Selected)**
  * **장점**: `PatternCompressor`가 무의미한 정상 패턴을 스킵하고 반복 메시지를 횟수로 치환하며, `StatisticalPrefilter`가 관련성 높은 청크만 추출. LLM에 전송되는 Token을 극적으로 절감.
  * **단점**: 필터링 알고리즘 설계가 까다롭고, 중요한 단서를 실수로 누락할 위험(False Negative) 존재.
  * **결정 사유**: 사내 Token 정책을 준수하고 분석 집중도를 높이기 위해 Option B를 선택하되, 누락 방지를 위해 에이전트가 언제든 추가 컨텍스트를 요청(`get_context`)할 수 있도록 보완.

### 3.4 설명 용이성 (QA-4)

* **목표**: 분석 결과에 대한 신뢰성 확보 및 동료 설명용 근거(Evidence) 제시.
* **Option A: 프롬프팅에 의존한 자연어 추론 유도 (Chain of Thought)**
  * **장점**: 별도 컴포넌트 없이 프롬프트만으로 구현 가능.
  * **단점**: 출력 결과에 원본 딥링크(IDE 네비게이션)를 체계적으로 강제하기 어려움.
* **Option B: Reasoning Trace Module + Evidence Linker (Selected)**
  * **장점**: 추론 각 단계(`ReasoningTrace`)와 증거 라인을 구조화하여 매핑(`EvidenceLinker`). IDE 환경에서 클릭 시 해당 로그 라인으로 점프하는 딥링크를 제공하고, 신뢰도 점수를 명시적으로 산출.
  * **단점**: 결과 포맷팅을 위한 추가 모듈과 프론트엔드 연동이 필요.
  * **결정 사유**: 동료에게 설명하기 쉽고, 분석 결과를 시각적(리포트+링크)으로 신뢰할 수 있어야 한다는 요구사항(QA-4)을 완벽히 충족하기 위해 Option B를 선택.

---

## 4. ATAM 기반 품질속성 트레이드오프 분석

> **ATAM (Architecture Tradeoff Analysis Method)**: 아키텍처 설계 결정이 여러 품질속성 간에 미치는 영향과 트레이드오프를 식별하는 분석 방법론.

| 설계 결정 (Architecture Decision) | 긍정적 영향 (+) | 부정적 영향 (–) | 트레이드오프 포인트 |
|:------|:------|:------|:------|
| **ReAct 루프 + GroundTruthVerifier** (QA-1) | 기능 정확성 ↑ (Hallucination 방지) | 수행 효율성 ↓ (다중 도구 호출로 Latency 증가) | 정확성이 제품 품질과 직결되므로 정확성을 우선 |
| **Client-Side 통계적 필터링 + 패턴 압축** (QA-3) | 수행 효율성 ↑ (Token 유지 / 절감) | 기능 정확성 ↓ (중요 단서 누락 위험, False Negative) | `get_context` 도구로 에이전트가 추가 컨텍스트를 요청할 수 있도록 보완하여 완화 |
| **In-Context Learning (Domain Memory 프롬프트 주입)** (QA-2a) | 기능 적응성 ↑ (재학습 없이 새 도메인 적응) | 수행 효율성 ↓ (Context Window 점유로 Token 사용 증가) | 도메인 지식 주입을 최소화하고 압축률을 높여 상쇄 완화 |
| **Application-level Allowlist (`allow_tool`)** (QA-2b) | 기능 적응성 ↑ (Harness 환경 안전 보장) | 기능 적응성 ↓ (허용된 도구만 사용 → 에이전트 자율도 제한) | 로그 분석 도메인은 6개 도구로 충분하며, 안전성이 자율도보다 우선 |
| **Reasoning Trace + Evidence Linker** (QA-4) | 설명 용이성 ↑ (딥링크 + 자동 리포트) | 수행 효율성 ↓ (추론 추적 오버헤드 + 출력 포맷팅 비용) | 사용자 신뢰와 설명 가능성이 실제 업무에서 핵심이므로 설명 용이성을 우선 |

---

## 5. 전체 Architecture

### 5.1 Architecture 구조도

> **TBD (To Be Determined)** — 3장의 Architecture Approach 확정 후 상세 설계 시 업데이트.

### 5.2 QA 시나리오 ↔ 아키텍처 매핑

| QA 시나리오 | 대응 컴포넌트 | 핵심 설계 메커니즘 (TBD) |
|:----------:|:------------|:-----------------|
| **QA-1** 기능 정확성 | `RootCauseAnalyzer`, `GroundTruthVerifier`, `EvidenceLinker` | **Hallucination 방지**: LLM이 언급하는 모든 라인 번호를 실제 원본 로그 파일과 대조 검증. 허위 라인 참조 시 재분석 강제 |
| **QA-2a** 기능 적응성 | `FormatAdapter`, `DomainMemory`, `UserRuleEngine`, `teach_domain` Tool | **제품군 적응**: 다양한 로그 포맷 동적 감지 + `teach_domain`으로 가르친 에러코드 및 비즈니스 로직(아키텍처)을 LLM Context에 주입 |
| **QA-2c** 분석 목적 적응성 | `Dynamic Strategy Selector`, `RootCauseAnalyzer` | **목적 기반 전략 전환**: 사용자의 질의 의도(성능/에러/보안)를 식별하고 ReAct 루프의 탐색 방향을 동적으로 조정 |
| **QA-3** 수행 효율성 | `PatternCompressor`, `StatisticalPrefilter` | **Token 낭비 방지**: 통계 기반 무관련 로그 제거 → 반복/주기적 로그 압축 및 스킵으로 토큰 전송량 최소화 |
| **QA-4** 설명 용이성 | `ReasoningTrace`, `EvidenceLinker`, `explain_reasoning` Tool | **투명한 근거 제시**: 추론 단계별 설명 및 원본 로그 딥링크 강제. 자동 마크다운 리포트 생성 |


## Open Questions

> [!NOTE]
> **Q1**: 도메인 메모리를 **제품군(모바일/TV/가전/통신) 단위**로 관리할지, **프로젝트(모델명) 단위**로 관리할지 결정이 필요합니다. 현재 설계는 프로젝트 단위이며, 제품군은 메모리 내 `productLine` 필드로 구분합니다.
