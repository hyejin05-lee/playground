# 시나리오 4: 대용량 로그 파일 Abnormal 분석

> **배경:** 사용자가 제안한 대용량 로그 분석이 Perspective에 적합한지 평가하고, 실험 계획으로 구체화

---

## 적합성 평가

### ✅ Perspective와 궁합이 좋은 이유

| 요소 | 설명 | Perspective 대응 |
|:---|:---|:---|
| **Read-only 강제** | 로그 파일은 증거이므로 **절대 수정 불가**. Skill/Workflow는 "수정 금지"라고 말만 할 수 있음 | `allowed_tools: [read_files, search_files, list_files]`로 write 원천 차단 |
| **대용량 → 분할 분석** | 수 GB 로그를 한 번에 읽으면 컨텍스트 초과. 체계적 분할 필요 | `system_prompt`에 청킹 전략 하드코딩 + `allowed_paths`로 분석 범위 제한 |
| **사용자 도메인 지식** | 사용자가 로그 패턴/마커를 가장 잘 알고 있음 | Perspective YAML에 사용자 정의 패턴을 **파라미터화**하여 주입 |
| **문제/해결 힌트** | 단순 검색이 아닌 **맥락 기반 추론** 필요 | Perspective가 도구를 제한하되, 분석 깊이는 LLM에 위임하는 구조 |

### 기존 시나리오와의 차별점

| | 시나리오 1 (영향도) | 시나리오 2 (Py2→3) | 시나리오 3 (Merge) | **시나리오 4 (로그)** |
|:---|:---|:---|:---|:---|
| **제약 유형** | 도구 제한 | 경로+명령어 제한 | 패턴 보호 | **대용량 분할 + 사용자 패턴 주입** |
| **Perspective 핵심** | `allowed_tools` | `allowed_paths` | `protected_patterns` | **`chunk_strategy` + `user_patterns`** |
| **새로운 가치** | 읽기 전용 강제 | 범위 제한 | 코드 보호 | **컨텍스트 관리 + 도메인 지식 통합** |

---

## Perspective 구성

```yaml
name: "log-analyzer"
allowed_tools:
  - read_files          # 로그 읽기
  - search_files        # 패턴 검색
  - list_files          # 파일 목록 탐색
  # ❌ write_to_file 없음 → 원본 보존 보장
  # ❌ execute_command 없음 → 실수로 로그 삭제/변경 방지
allowed_paths:
  - ./logs/**/*.log     # 로그 디렉터리만
  - ./logs/**/*.txt
forbidden_commands: []  # execute_command 자체가 금지이므로 불필요
system_prompt: |
  You are a log analysis specialist.
  
  CRITICAL RULES:
  1. You are in READ-ONLY mode. Never attempt to modify or delete log files.
  2. The user will provide abnormal patterns/markers to search for.
  3. Follow this analysis strategy for large files:
  
  ANALYSIS STRATEGY:
  Phase 1 - Survey: list_files로 로그 파일 목록, 크기, 시간 범위 파악
  Phase 2 - Pattern Scan: search_files로 사용자 지정 abnormal 패턴 전체 스캔
  Phase 3 - Context Deep-dive: 발견된 각 abnormal 지점 전후 N라인 read_files
  Phase 4 - Correlation: 시간축 기준 이벤트 상관관계 분석
  Phase 5 - Report: 문제 요약 + 근본 원인 가설 + 해결 힌트
  
  CHUNKING RULES:
  - 단일 read_files 호출 시 최대 500라인씩 읽기
  - 동일 파일을 여러 번 나눠 읽되, 각 청크는 시간 범위 기준으로 분할
  - 전체 파일을 한 번에 읽으려 시도하지 않기
  
  OUTPUT FORMAT:
  - 발견된 abnormal 이벤트마다: [시간] [파일:라인] [심각도] [설명]
  - 이벤트 간 상관관계 다이어그램
  - 근본 원인 가설 (확신도 포함)
  - 해결 액션 아이템
```

> [!IMPORTANT]
> **`user_patterns` 파라미터화 설계**: 사용자가 매번 다른 로그/다른 패턴을 분석하므로, Perspective YAML의 `system_prompt` 내에 사용자 입력 패턴을 주입하는 메커니즘이 필요합니다.

```yaml
# 사용자 패턴 주입 예시 (런타임 파라미터)
user_patterns:
  abnormal_markers:
    - "ERROR"
    - "FATAL"
    - "OutOfMemoryError"
    - "Connection refused"
    - "timeout exceeded"
  time_range: "2026-07-20T00:00:00 ~ 2026-07-20T12:00:00"
  focus_components:
    - "payment-service"
    - "auth-gateway"
```

---

## 실험 대상

> [!NOTE]
> 공개 로그 데이터셋을 사용하거나, 실제 운영 로그의 마스킹된 버전을 사용합니다.

### 🥇 추천 1: Loghub 데이터셋 — ⭐ 최우선 추천

| 항목 | 내용 |
|:---|:---|
| **GitHub** | https://github.com/logpai/loghub |
| **규모** | 16종 시스템 로그, 총 수백 MB ~ 수 GB |
| **적합 이유** | HDFS, Hadoop, Spark, OpenStack, Linux 등 **실제 시스템 로그** 포함. Anomaly label이 있어 Ground Truth 확보 용이. 학술 논문에서 널리 사용되는 벤치마크 |
| **Ground Truth** | 일부 데이터셋에 anomaly label 포함 (HDFS: `anomaly_label.csv`) |

### 🥈 추천 2: 실제 프로젝트 빌드/배포 로그

| 항목 | 내용 |
|:---|:---|
| **소스** | 자체 CI/CD 파이프라인 로그 또는 Kubernetes pod 로그 |
| **적합 이유** | 사용자가 도메인 지식을 갖고 있는 **실제 로그**. 패턴을 가장 잘 정의할 수 있음 |
| **Ground Truth** | 사용자가 이미 알고 있는 장애 사례의 로그 구간 |

---

## 실험 순서 (상세)

### Phase 0: Ground Truth 준비

```bash
# 1. Loghub HDFS 데이터셋 다운로드
git clone https://github.com/logpai/loghub.git
cd loghub/HDFS

# 2. anomaly label 확인
head -20 anomaly_label.csv
# BlockId,Label
# blk_-1608999687919862906,Normal
# blk_7503483334202473044,Anomaly

# 3. 특정 anomaly block의 관련 로그 라인 추출 → Ground Truth
python extract_anomaly_context.py HDFS.log anomaly_label.csv > ground_truth_anomalies.json
```

**Ground Truth JSON 형식:**

```json
[
  {
    "block_id": "blk_7503483334202473044",
    "label": "Anomaly",
    "log_lines": [
      {"line_number": 4521, "timestamp": "081109 204655", "content": "..."},
      {"line_number": 4523, "timestamp": "081109 204657", "content": "..."}
    ],
    "root_cause_category": "DataNode failure",
    "related_events": ["blk_...", "blk_..."]
  }
]
```

### Phase 1: 조건 A 실험 (Skill만 사용)

```
SKILL.md 내용:
---
name: log-analysis
description: Analyze log files for abnormal patterns
---
# Instructions
Analyze the provided log files for abnormal patterns.
The user will specify patterns to look for.
Do not modify any log files.
Produce a report of found anomalies with root cause hypotheses.
```

```
실험 순서:
1. Cline에 Skill 로드
2. 사용자 프롬프트: "HDFS.log에서 Anomaly 패턴을 찾아줘. 
   특히 'ERROR', 'Exception', 'failed' 패턴 중심으로. 
   파일이 크니까 나눠서 분석해줘."
3. 에이전트 실행 → 관찰 기록:
   a. 파일 전체를 한 번에 읽으려는 시도 여부 (컨텍스트 초과 위험)
   b. write_to_file로 "분석 결과 저장"을 위한 파일 생성 시도 여부
   c. execute_command로 grep/awk 등 시스템 명령 실행 시도 여부
   d. 체계적 분할 분석 수행 여부 (ad-hoc vs systematic)
   e. 발견된 anomaly 정확도 (Ground Truth 대비)
4. Ground Truth 대비 정밀도/재현율 계산
```

### Phase 2: 조건 B 실험 (Workflow 사용)

```
Cline /workflow 지시:
Step 1: list_files로 로그 파일 구조 파악
Step 2: 파일 크기 확인하고 분할 계획 수립
Step 3: search_files로 "ERROR", "Exception", "failed" 패턴 스캔
Step 4: 발견된 패턴 주변 컨텍스트 (전후 20라인) read_files
Step 5: 시간순 정렬하여 이벤트 상관관계 분석
Step 6: 분석 보고서 출력
주의: 로그 파일 절대 수정 금지. 파일 생성 금지.
```

```
실험 순서:
1. Cline 채팅창에 `/workflow` 슬래시 커맨드를 입력하고 워크플로우 지시 전달
2. 에이전트 실행 → Phase 1과 동일 항목 기록
3. Step 순서 준수 여부 관찰
4. 특히 대용량 파일 처리 전략의 체계성 관찰
```

### Phase 3: 조건 C 실험 (Perspective 사용)

```
perspective/log-analyzer.yaml 적용
핵심:
- allowed_tools: read_files, search_files, list_files만 허용
- allowed_paths: ./logs/** 만 허용
- system_prompt에 chunking 전략, 분석 Phase, 출력 형식 하드코딩
- user_patterns에 사용자 정의 abnormal 마커 주입
```

```
실험 순서:
1. Perspective YAML 로드
   - write_to_file → 시스템 레벨 차단
   - execute_command → 시스템 레벨 차단  
   - 파일 전체 읽기 시도 → chunking rule에 의해 제어
2. 사용자 프롬프트: "HDFS.log에서 abnormal 패턴을 분석해줘"
   (※ user_patterns YAML에 이미 패턴 정의됨 → 프롬프트 간소화 가능)
3. 에이전트 실행 → 관찰 기록:
   a. write_to_file 시도 → 시스템 차단 (Skill/Workflow와 차별점)
   b. execute_command 시도 → 시스템 차단
   c. 분할 분석 전략 준수 여부 (system_prompt의 Phase 1~5)
   d. user_patterns의 패턴 활용 여부
   e. 발견된 anomaly 정확도 + 근본 원인 가설 품질
4. Ground Truth 대비 정밀도/재현율 계산
```

---

## Perspective의 핵심 차별 가치 (이 시나리오)

### 1. 대용량 처리 전략의 "강제 가드레일"

> [!WARNING]
> **Skill/Workflow의 한계:** "파일이 크니까 나눠서 읽어"라고 지시해도, 에이전트가 "효율을 위해" 전체 파일을 한 번에 읽거나, `grep` 명령으로 우회하는 케이스가 빈번하게 발생합니다.

| 접근 | 대용량 파일 처리 |
|:---|:---|
| **Skill** | "나눠서 읽어" → 에이전트가 무시하고 전체 읽기 시도 → 컨텍스트 초과 → 분석 실패 |
| **Workflow** | Step별로 "500라인씩" 지시 → 에이전트가 "효율을 위해" execute_command로 `grep` 실행 → 우회 |
| **Perspective** | `allowed_tools`에 execute_command 없음 → grep 우회 불가. chunking rule 위반 시에도 read_files는 가능하되, 시스템 프롬프트 지시와 결합하여 체계적 분석 유도 |

### 2. 사용자 도메인 지식의 "구조화된 주입"

```
Skill/Workflow 방식:
  프롬프트: "ERROR, FATAL, OutOfMemory, Connection refused 패턴을 찾아줘. 
  특히 payment-service랑 auth-gateway 중심으로..."
  → 매번 긴 프롬프트 → 누락/오해 위험

Perspective 방식:
  user_patterns YAML에 구조화:
    abnormal_markers: [ERROR, FATAL, OutOfMemory...]
    focus_components: [payment-service, auth-gateway]
  → 프롬프트: "로그 분석해줘" (간결)
  → 패턴은 YAML에서 체계적으로 관리 → 재사용·버전 관리 가능
```

### 3. 반복 분석의 "일관성 보장"

같은 로그를 여러 사람이 분석하거나, 같은 유형의 장애가 반복될 때:
- **Skill/Workflow**: 분석자마다 다른 프롬프트 → 다른 분석 품질
- **Perspective**: 동일 YAML → 동일 제약·동일 전략 → **재현 가능한 분석 프로세스**

---

## 핵심 가설

> [!IMPORTANT]
> **조건 A (Skill)**: 
> - 에이전트가 `execute_command`로 `grep -c ERROR *.log` 등을 실행하여 "빠른 분석"을 시도
> - 대용량 파일 전체 읽기 시도 → 컨텍스트 초과 → 불완전한 분석
> - 패턴 누락 (사용자가 프롬프트에서 일부 패턴 언급 안 하면 무시)
>
> **조건 B (Workflow)**:
> - Step 순서는 따르지만, execute_command 사용 가능 → `tail`, `head`, `wc -l` 등 다양한 명령 실행
> - 분석 결과를 "편의를 위해" 파일로 저장 시도 가능
>
> **조건 C (Perspective)**:
> - read_files, search_files, list_files만으로 분석 → **순수 LLM 추론 기반 분석**
> - execute_command 차단 → 시스템 명령 우회 불가
> - write_to_file 차단 → 원본 로그 보존 보장
> - system_prompt의 Phase 전략 + user_patterns → **체계적이고 재현 가능한 분석**

---

## Open Questions

> [!IMPORTANT]
> **ClineSDK에서 `user_patterns` 같은 런타임 파라미터를 Perspective YAML에 주입하는 메커니즘이 현재 지원되는지 확인 필요.**
> 지원되지 않으면:
> - Option A: system_prompt에 직접 하드코딩 (패턴 변경 시 YAML 수정 필요)
> - Option B: 사용자 프롬프트에서 패턴을 입력받되, system_prompt에서 "사용자가 지정한 패턴만 분석하라" 지시
> - Option C: Perspective에 파라미터 주입 기능 자체를 개발 (ClineSDK 확장)

> [!NOTE]
> **대용량 파일의 "대용량" 기준:**
> - 로그 파일 100MB 이상이면 LLM이 read_files로 처리하기에 비현실적일 수 있음
> - search_files(grep 내부 구현)로 패턴 매칭 후 → 해당 지점만 read_files로 컨텍스트 확인하는 전략이 현실적
> - Perspective의 chunking rule이 이 전략을 **강제**하는 것이 핵심 가치

---

## 기존 실험 계획서와의 통합 위치

이 시나리오를 추가하면 Perspective가 증명하는 가치가 4가지로 확장됩니다:

| # | 시나리오 | 증명 포인트 | Perspective 핵심 기능 |
|:---|:---|:---|:---|
| 1 | 영향도 분석 | **안전성** (읽기 전용 강제) | `allowed_tools` |
| 2 | Py2→3 마이그레이션 | **범위 제한** (경로+명령어) | `allowed_paths` + `forbidden_commands` |
| 3 | 업스트림 Merge | **코드 보호** (패턴 보호) | `protected_patterns` |
| **4** | **로그 분석** | **대용량 전략 + 도메인 지식 통합** | **`chunking_rules` + `user_patterns`** |

> [!TIP]
> 시나리오 4는 시나리오 1(읽기 전용)과 제약 유형이 유사하지만, **대용량 처리 전략**과 **사용자 도메인 지식의 구조화된 주입**이라는 새로운 차원을 추가합니다. 시나리오 1이 "도구를 제한한다"면, 시나리오 4는 "제한된 도구로 **어떻게 쓸지**까지 가이드한다"는 점에서 Perspective의 더 깊은 가치를 보여줍니다.

---

## Appendix: Case Study — Loghub HDFS_v1 실제 데이터 분석

> **데이터 소스:** [logpai/loghub](https://github.com/logpai/loghub) → HDFS_v1  
> **다운로드:** [Zenodo HDFS_v1.zip](https://zenodo.org/records/8196385/files/HDFS_v1.zip?download=1)

### 데이터셋 개요

| 항목 | 값 |
|:---|:---|
| **로그 파일** | `HDFS.log` (1.47 GB, 11,175,629 라인) |
| **시간 범위** | 38.7시간 |
| **전체 블록 수** | 575,061 |
| **Normal 블록** | 558,223 (97.1%) |
| **Anomaly 블록** | 16,838 (2.9%) |
| **Ground Truth** | `preprocessed/anomaly_label.csv` — BlockId별 Normal/Anomaly 라벨 |

**`anomaly_label.csv` 형식:**
```csv
BlockId,Label
blk_-1608999687919862906,Normal
blk_7503483334202473044,Normal
blk_-3544583377289625738,Anomaly     ← 이상 탐지됨
blk_-9073992586687739851,Normal
```

**HDFS 블록 라이프사이클 (정상 흐름):**
```
allocateBlock → Receiving → Received → addStoredBlock → Served → delete → Deleting ✅
```

---

### 🟢 Normal 블록: `blk_-1608999687919862906` (269 라인)

**전체 이벤트 시퀀스 요약:**

| 시간 | Phase | 이벤트 | 라인 수 | 특이사항 |
|:---|:---|:---|:---|:---|
| `20:35:18` | **① 할당** | `allocateBlock` | 1 | `/job_200811092030_0001/job.jar` 파일용 |
| `20:35:18~19` | **② 수신** | `Receiving` (3노드) | 3 | 10.250.19.102, 10.250.10.6, 10.250.14.224 |
| `20:35:19` | **③ 완료** | `PacketResponder terminating` + `Received` | 6 | 3노드 모두 size=**91178** 수신 완료 |
| `20:35:19` | **④ 저장** | `addStoredBlock` (3노드) | 3 | blockMap에 등록 |
| `20:35:21~26` | **⑤ 복제** | `ask to replicate` → `Transmitted` → `addStoredBlock` | 다수 | **10개 노드**로 복제 확장 |
| `20:35:23~203626` | **⑥ 서빙** | `Served block` | ~200 | 정상적인 읽기 서비스 |
| `21:38:09` | **⑦ 삭제 예약** | `NameSystem.delete → invalidSet` | **10** | 10개 노드 모두 무효화 |
| `21:38:10~40` | **⑧ 삭제 완료** | `Deleting block` | **10** | 10개 노드 모두 정상 삭제 ✅ |

**핵심 포인트 — 정상 블록의 삭제 과정:**
```
invalidSet 등록: 10개 노드 (10.250.10.6, 10.250.14.224, 10.251.107.19, ...)
Deleting block:  10회 (각 노드에서 1회씩 정상 삭제)
WARN/ERROR:      0건 ✅
```

---

### 🔴 Anomaly 블록: `blk_-3544583377289625738` (223 라인)

**전체 이벤트 시퀀스 요약:**

| 시간 | Phase | 이벤트 | 라인 수 | 특이사항 |
|:---|:---|:---|:---|:---|
| `20:35:21` | **① 할당** | `allocateBlock` | 1 | `/job_200811092030_0001/job.xml` 파일용 |
| `20:35:21~22` | **② 수신** | `Receiving` (3노드) | 3 | 10.250.19.102, 10.251.197.226, 10.250.11.100 |
| `20:35:22~23` | **③ 완료** | `PacketResponder terminating` + `Received` | 6 | 3노드 모두 size=**11971** 수신 완료 |
| `20:35:23` | **④ 저장** | `addStoredBlock` (3노드) | 3 | blockMap에 등록 |
| — | **⑤ 복제** | ❌ **`ask to replicate` 없음!** | 0 | 📛 **복제 단계 누락** |
| `20:35:23~203616` | **⑥ 서빙** | `Served block` | ~200 | 3개 노드에서만 서빙 |
| `21:38:09` | **⑦ 삭제 예약** | `NameSystem.delete → invalidSet` | **3** | ⚠️ 3개 노드만 (Normal은 10개) |
| `21:38:11~35` | **⑧ 삭제** | `Deleting block` | **3** | — |
| `21:38:38` | **⑨ ❌ ERROR** | `WARN: Unexpected error` | **1** | 📛 **BlockInfo not found in volumeMap** |

**핵심 포인트 — Anomaly 블록의 삭제 과정:**
```
invalidSet 등록: 3개 노드 (10.250.11.100, 10.251.197.226, 10.251.39.179)
Deleting block:  3회
⚠️ WARN:         1건 → "Unexpected error trying to delete block. 
                        BlockInfo not found in volumeMap."
```

---

### 🔍 Normal vs Anomaly 비교 분석

| 비교 항목 | 🟢 Normal (`blk_-160899...`) | 🔴 Anomaly (`blk_-354458...`) |
|:---|:---|:---|
| **블록 크기** | 91,178 bytes | 11,971 bytes |
| **수신 노드** | 3 → **10으로 복제** | 3 → **복제 없음** |
| **`ask to replicate`** | ✅ 4회 (계층적 복제) | ❌ **0회** |
| **`Transmitted`** | ✅ 4회 | ❌ **0회** |
| **`addStoredBlock`** | 10회 (10개 노드) | 3회 (3개 노드만) |
| **invalidSet 노드 수** | 10 | 3 |
| **Deleting block** | 10회 → 정상 완료 | 3회 → **마지막 삭제 실패** |
| **WARN/ERROR** | **0건** | **1건** (`BlockInfo not found`) |

### 근본 원인 가설

> [!CAUTION]
> **Anomaly 근본 원인: 복제 실패 → 메타데이터 불일치 → 삭제 오류**
>
> 1. **복제 단계 누락**: Normal 블록은 `ask to replicate`로 3→10개 노드로 복제가 확장되지만, Anomaly 블록은 복제가 전혀 이뤄지지 않음 (HDFS 정책상 최소 replication factor 미달)
> 2. **blockMap과 실제 저장소 불일치**: 3개 노드에서 3번 삭제를 시도했으나, volumeMap에 이미 제거된 엔트리를 다시 삭제하려 함
> 3. **Race condition**: invalidSet에 등록된 3개 노드의 삭제 요청이 동일 FSDataset 쓰레드(PID 19)에서 순차 처리되면서, 첫 삭제가 volumeMap까지 정리한 뒤 다음 삭제가 빈 맵을 참조

---

### 🎯 Perspective로 이 분석을 자동화하면?

**사용자가 제공하는 `user_patterns`:**
```yaml
user_patterns:
  abnormal_markers:
    - "WARN"
    - "ERROR" 
    - "Unexpected error"
    - "not found in volumeMap"
    - "BlockInfo not found"
  lifecycle_events:        # 정상 흐름 정의 → 누락 탐지에 활용
    - "allocateBlock"
    - "Receiving block"
    - "Received block"
    - "addStoredBlock"
    - "ask .* to replicate"  # ← 이것이 Anomaly에서 누락됨
    - "Transmitted block"
    - "Served block"
    - "NameSystem.delete"
    - "Deleting block"
  grouping_key: "blk_-?\\d+"   # Block ID로 그룹핑
```

**Perspective 분석 Phase 시뮬레이션:**

```
Phase 1 - Survey:
  → list_files: HDFS.log (1.47GB), anomaly_label.csv 확인
  → "파일이 1.47GB이므로 전체 읽기 불가. search_files로 패턴 스캔 후 
     해당 지점만 read_files로 컨텍스트 확인"

Phase 2 - Pattern Scan:
  → search_files("Unexpected error", HDFS.log)
  → search_files("not found in volumeMap", HDFS.log)
  → 결과: blk_-3544583377289625738 등 다수 블록 식별

Phase 3 - Context Deep-dive:
  → read_files(HDFS.log, 해당 WARN 라인 ±50라인)
  → 동일 블록 ID의 다른 이벤트 search_files로 추적
  → "이 블록은 allocate → receive → store → serve → delete는 있으나,
     replicate/Transmitted 단계가 누락됨"

Phase 4 - Correlation:
  → "비슷한 시간대(20:35~20:36)에 할당된 정상 블록과 비교하면,
     정상 블록은 replicate 단계가 있고 10개 노드로 확장됨.
     Anomaly 블록은 3개 노드에 머물러 HDFS replication factor 미달"

Phase 5 - Report:
  [21:38:38] [HDFS.log:L223] [HIGH] blk_-3544583377289625738
  - 증상: BlockInfo not found in volumeMap (삭제 실패)
  - 근본 원인: 블록 복제 단계 누락 → 3개 노드만 보유 → 메타데이터 불일치
  - 확신도: 85%
  - 해결 힌트: HDFS replication trigger 로직 점검, 
              NameNode의 복제 스케줄링 큐 확인
```

> [!IMPORTANT]
> **Perspective의 가치가 드러나는 순간:**
> - **Skill/Workflow**: 에이전트가 `grep -c "WARN" HDFS.log` 같은 명령으로 빠르게 건수만 세고 끝낼 수 있음. 또는 1.47GB 파일을 통째로 읽으려다 컨텍스트 초과
> - **Perspective**: `execute_command` 차단 → grep 우회 불가. `search_files`로 패턴을 찾고, `read_files`로 컨텍스트를 확인하는 **체계적 분석만 가능**. `user_patterns.lifecycle_events`로 정상 흐름을 알고 있으므로 **누락 탐지**(replicate 없음)까지 수행
