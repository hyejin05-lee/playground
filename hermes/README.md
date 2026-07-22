# Hermes Agent 평가 가이드: 자기학습 & Proactive 기능 테스트

> 작성 기준일: 2026-07-21

## 1. Hermes Agent 개요

Hermes Agent는 [Nous Research](https://nousresearch.com)가 개발한 **self-improving AI agent**입니다. 가장 큰 특징은 **closed learning loop** — 경험에서 skill을 생성하고, 사용 중 자동 개선하며, 주기적으로 memory를 남기도록 스스로 nudge하는 구조입니다.

---

## 2. 설치 (Windows)

### PowerShell 설치 (네이티브 Windows)
```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

> 이 스크립트가 uv, Python 3.11, Node.js, ripgrep, ffmpeg, 그리고 portable Git Bash까지 자동 설치합니다. 관리자 권한 불필요.

### WSL2 사용 시 (Linux 방식)
```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

### 설치 후 첫 설정
```bash
hermes setup            # 전체 설정 위저드 (모델, API 키 등)
# 또는
hermes setup --portal   # Nous Portal OAuth 로그인 (API 키 하나로 통합)
```

---

## 3. Hermes Agent 사용법 (대화 방법)

### 3.1 기본 CLI 대화

```bash
hermes                  # 대화형 TUI 시작 — 바로 채팅 가능
```

TUI(Terminal UI)가 열리면 자연어로 바로 대화할 수 있습니다. 멀티라인 편집, 슬래시 커맨드 자동완성, 대화 기록 등을 지원합니다.

### 3.2 모델 선택

```bash
hermes model            # 대화형으로 LLM 프로바이더/모델 선택
hermes model openrouter:anthropic/claude-sonnet-4   # 직접 지정
```

지원하는 프로바이더: Nous Portal, OpenRouter (200+모델), OpenAI, Anthropic, Google, DeepSeek, 로컬 모델 등.

### 3.3 핵심 슬래시 커맨드

| 커맨드 | 설명 |
|--------|------|
| `/new` 또는 `/reset` | 새 대화 시작 |
| `/model [provider:model]` | 모델 변경 |
| `/skills` | 설치된 skill 목록 확인 |
| `/learn <소스>` | 소스에서 새 skill 학습 |
| `/plan <요청>` | 실행 전 계획서 작성 |
| `/compress` | 컨텍스트 압축 (토큰 절감) |
| `/usage` | 토큰 사용량 확인 |
| `/insights [--days N]` | 사용 인사이트 확인 |
| `/retry`, `/undo` | 마지막 턴 재시도/취소 |
| `Ctrl+C` | 현재 작업 중단 |

### 3.4 비-CLI 대화 (메시징)

```bash
hermes gateway setup    # Telegram/Discord/Slack 등 설정
hermes gateway start    # 게이트웨이 시작 → 메시지 앱에서 봇과 대화
```

---

## 4. 확인하고 싶은 핵심 기능

### 4.1 Skill 자동 생성 (Autonomous Skill Creation)

Hermes Agent의 핵심 차별화 기능입니다. 소스코드를 분석한 결과:

- **Skill Nudge Interval**: Agent가 일정 횟수(기본 ~10회)의 tool 사용 후, "지금까지 한 작업을 skill로 만들 수 있는지" 스스로 검토합니다.
- **Background Review**: 대화 중 일정 주기마다 시스템이 자동으로 "skill을 만들어야 하는가?"를 LLM에게 묻는 내부 프로세스가 돌아갑니다.
- `skill_manage(action='create')` 도구로 `~/.hermes/skills/` 아래에 SKILL.md 파일을 자동 생성합니다.

### 4.2 Memory Nudge (자동 기억 저장)

- **Memory Nudge Interval**: N번의 사용자 턴마다 "기억해둘 만한 것이 있는가?"를 agent가 스스로 판단합니다.
- MEMORY.md, USER.md에 사용자 선호/패턴을 기록합니다.

### 4.3 Skill Self-Improvement (사용 중 스킬 자동 개선)

기존 skill을 사용하다 더 나은 방법을 발견하면, `skill_manage(action='patch')` 또는 `action='edit'`로 기존 skill을 자동 업데이트합니다.

### 4.4 `/learn` — 명시적 Skill 학습

소스 코드, URL, 대화 기록 등을 skill로 변환하는 기능:
```
/learn how I just renamed all those functions
```

---

## 5. 추천 오픈소스 프로젝트 (가벼운 테스트용)

### 추천 1: **[Flask-Todo](https://github.com/alisheikh/flask-todo)** 또는 유사 간단 Flask 앱

- **이유**: 파일 수가 적고 (5-10개), 함수명이 단순, 리팩터링 대상이 명확
- **크기**: ~500 LOC

### 추천 2: **직접 생성하는 미니 프로젝트** (가장 추천)

아래와 같은 간단한 Python 유틸리티 프로젝트를 직접 만들어서 테스트하면 가장 통제 가능합니다.

> [!NOTE]
> **snake_case란?** 소문자와 언더스코어(`_`)로 단어를 구분하는 네이밍 규칙입니다.
> 예: `get_user_name`, `calculate_total_price`. Python 공식 스타일 가이드(PEP 8)에서 함수명과 변수명에 권장하는 방식입니다.
> 반대로 `getUserName`은 camelCase, `GetUserName`은 PascalCase라고 합니다.

> [!TIP]
> **프로젝트 생성 위치**: Hermes 설치 위치(`~/.hermes/`)와는 **별도의 아무 디렉터리**에 만들면 됩니다.
> Hermes는 `hermes` 명령을 실행한 시점의 현재 디렉터리(working directory)를 작업 대상으로 인식합니다.
> 따라서 아래처럼 아무 곳에나 테스트 폴더를 만들고, 그 안에서 `hermes`를 실행하면 됩니다:
> ```bash
> mkdir ~/test-hermes && cd ~/test-hermes
> # 파일들 생성 후...
> hermes   # 여기서 실행하면 ~/test-hermes가 작업 디렉터리
> ```

```python
# utils.py — 일부러 일관성 없는 함수명으로 작성
def getUserName(user_id):
    return f"user_{user_id}"

def get_user_email(user_id):
    return f"user_{user_id}@example.com"

def fetchUserAge(user_id):
    return 25

def GetUserAddress(user_id):
    return "123 Main St"

def retrieve_user_phone(user_id):
    return "010-1234-5678"
```

```python
# calculator.py — 역시 혼재된 네이밍
def addNumbers(a, b):
    return a + b

def subtract_numbers(a, b):
    return a - b

def MultiplyNumbers(a, b):
    return a * b

def divideNums(a, b):
    return a / b if b != 0 else None
```

```python
# string_helpers.py — 함수를 많이 넣어서 반복 리네이밍 작업을 충분히 수행할 수 있도록 구성
def reverseString(s):
    return s[::-1]

def CountWords(s):
    return len(s.split())

def trimSpaces(s):
    return s.strip()

def toUpperCase(s):
    return s.upper()

def toLowerCase(s):
    return s.lower()

def capitalizeFirst(s):
    return s.capitalize()

def replaceSubstring(s, old, new):
    return s.replace(old, new)

def checkStartsWith(s, prefix):
    return s.startswith(prefix)

def checkEndsWith(s, suffix):
    return s.endswith(suffix)

def splitByDelimiter(s, delim=","):
    return s.split(delim)

def joinWithDelimiter(lst, delim="-"):
    return delim.join(lst)

def padLeftZeros(s, width=10):
    return s.zfill(width)

def removePrefix(s, prefix):
    return s[len(prefix):] if s.startswith(prefix) else s

def truncateString(s, max_len=50):
    return s[:max_len] + "..." if len(s) > max_len else s
```

```python
# data_processor.py — 데이터 처리 관련 함수 (역시 네이밍 혼재)
def readCsvFile(file_path):
    import csv
    with open(file_path) as f:
        return list(csv.reader(f))

def filterEmptyRows(rows):
    return [r for r in rows if any(cell.strip() for cell in r)]

def SortByColumn(rows, col_index=0):
    return sorted(rows, key=lambda r: r[col_index] if col_index < len(r) else "")

def removeDuplicates(lst):
    seen = set()
    result = []
    for item in lst:
        key = tuple(item) if isinstance(item, list) else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

def flattenList(nested):
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flattenList(item))
        else:
            result.append(item)
    return result

def chunkList(lst, chunkSize=3):
    return [lst[i:i+chunkSize] for i in range(0, len(lst), chunkSize)]

def mergeDicts(dict1, dict2):
    merged = dict1.copy()
    merged.update(dict2)
    return merged

def filterByThreshold(values, minVal=0, maxVal=100):
    return [v for v in values if minVal <= v <= maxVal]

def calculateAverage(numbers):
    return sum(numbers) / len(numbers) if numbers else 0

def findMaxValue(numbers):
    return max(numbers) if numbers else None

def findMinValue(numbers):
    return min(numbers) if numbers else None

def countOccurrences(lst, target):
    return lst.count(target)
```

```python
# file_utils.py — 파일 관련 유틸 (역시 네이밍 혼재)
import os

def getFileSize(file_path):
    return os.path.getsize(file_path)

def checkFileExists(file_path):
    return os.path.exists(file_path)

def ReadFileContent(file_path):
    with open(file_path, 'r') as f:
        return f.read()

def writeToFile(file_path, content):
    with open(file_path, 'w') as f:
        f.write(content)

def appendToFile(file_path, content):
    with open(file_path, 'a') as f:
        f.write(content)

def listDirContents(dir_path):
    return os.listdir(dir_path)

def getFileExtension(file_path):
    return os.path.splitext(file_path)[1]

def createDirIfNotExists(dir_path):
    os.makedirs(dir_path, exist_ok=True)

def deleteFile(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def renameFile(old_path, new_path):
    os.rename(old_path, new_path)
```

### 추천 3: **[httpie](https://github.com/httpie/cli)** (더 큰 규모 원할 경우)

- Python 기반 CLI HTTP 클라이언트
- 모듈 구조가 잘 되어있어 리팩터링 테스트 적합

---

## 6. 단계별 평가 시나리오

### 시나리오 A: 함수 리네이밍 패턴 반복 → Skill 자동 생성 확인

> [!IMPORTANT]
> Hermes의 skill 자동 생성은 **반복 작업 감지 기반**이 아니라, **일정 tool 사용 횟수 후 background review에서 LLM이 판단**하는 방식입니다.
> 따라서 "3번 반복하면 자동으로 skill이 만들어진다"는 식의 결정론적 동작은 아니고, LLM의 판단에 의존합니다.

#### Step 1: 미니 프로젝트 준비
```bash
mkdir ~/test-hermes && cd ~/test-hermes
# 위의 5개 파일(utils.py, calculator.py, string_helpers.py, data_processor.py, file_utils.py) 생성
```

> 총 약 40개 이상의 함수가 있으므로, 하나씩 리네이밍을 요청하면 충분한 tool 사용 횟수를 확보할 수 있습니다.

#### Step 2: Hermes 시작 후 1차 리네이밍
```
hermes
> utils.py의 getUserName을 snake_case(get_user_name)로 바꿔줘
```

#### Step 3: 2차 리네이밍
```
> calculator.py의 addNumbers도 snake_case(add_numbers)로 바꿔줘
```

#### Step 4: 3차 리네이밍
```
> string_helpers.py의 reverseString도 snake_case(reverse_string)로 바꿔줘
```

#### Step 5: 4~10차 반복 (충분히 많이)
```
> calculator.py의 MultiplyNumbers도 snake_case로 바꿔줘
> utils.py의 fetchUserAge도 snake_case로 바꿔줘
> string_helpers.py의 toUpperCase도 snake_case로 바꿔줘
> data_processor.py의 readCsvFile도 snake_case로 바꿔줘
> file_utils.py의 getFileSize도 snake_case로 바꿔줘
> data_processor.py의 SortByColumn도 snake_case로 바꿔줘
> file_utils.py의 ReadFileContent도 snake_case로 바꿔줘
```

> [!TIP]
> 기본 skill nudge interval이 ~10회이므로, **최소 10~15회 이상** 반복해야 background review가 트리거될 가능성이 높습니다.
> 함수가 40개 이상 있으므로 넉넉하게 반복할 수 있습니다.

#### 관찰 포인트
- **일정 횟수 후**, Hermes가 자발적으로 다음과 같은 행동을 하는지 확인:
  - "이 패턴을 skill로 만들까요?" 같은 제안
  - 또는 조용히 `~/.hermes/skills/` 아래에 skill 파일 생성
  - memory에 "사용자가 snake_case를 선호한다" 기록

```bash
# skill 생성 여부 확인:
ls ~/.hermes/skills/
cat ~/.hermes/skills/*/SKILL.md 2>/dev/null

# memory 기록 확인:
cat ~/.hermes/MEMORY.md 2>/dev/null
cat ~/.hermes/USER.md 2>/dev/null
```

### 시나리오 B: `/learn`으로 명시적 skill 학습 후 재사용

#### Step 1: 수동으로 리네이밍 작업 몇 번 수행 (시나리오 A)

#### Step 2: `/learn` 명령
```
/learn how I just renamed all those functions to snake_case
```

#### Step 3: 생성된 skill 확인
```
/skills
```
→ 새로 생성된 skill이 목록에 나타나야 합니다.

#### Step 4: 새 파일에서 해당 skill 호출
```
/rename-to-snake-case   (또는 생성된 skill 이름)
string_helpers.py의 나머지 함수들도 모두 바꿔줘
```

### 시나리오 C: Proactive 알림/평가 기능 확인

#### 설정 확인
```bash
hermes config set memory.nudge_interval 5    # 5턴마다 memory review
hermes config set skills.nudge_interval 5    # 5턴마다 skill review
```

> 기본값보다 낮게 설정하면 빠르게 확인 가능합니다.

#### 코드 품질 proactive 알림 확인
```
> utils.py를 읽어줘
```
→ Agent가 자발적으로 "이 파일에는 네이밍 일관성이 없습니다" 같은 피드백을 주는지 확인

#### Memory 자동 기록 확인
```
> 나는 항상 Python에서 snake_case를 사용해
> type hint도 꼭 넣어줘
> docstring은 Google 스타일로 써줘
```
→ 이런 대화 후 `~/.hermes/MEMORY.md`나 `USER.md`에 기록되었는지 확인

### 시나리오 D: Insights & 사용 분석

```
/insights --days 7
/usage
```
→ 사용 패턴 분석 리포트를 확인

---

## 7. 확인 체크리스트

| # | 확인 항목 | 커맨드/방법 | 기대 결과 |
|---|----------|------------|----------|
| 1 | Skill 자동 생성 | `ls ~/.hermes/skills/` | 반복 작업 후 새 skill 디렉터리 생성됨 |
| 2 | Memory 자동 기록 | `cat ~/.hermes/MEMORY.md` | 사용자 선호가 기록됨 |
| 3 | `/learn` 동작 | `/learn <소스>` → `/skills` | 학습된 skill이 목록에 나타남 |
| 4 | Skill Self-improve | 기존 skill 반복 사용 후 확인 | SKILL.md 내용이 개선/보완됨 |
| 5 | Proactive 제안 | 코드 작업 중 관찰 | Agent가 자발적으로 개선 제안 |
| 6 | 패턴 인식 → memory | 동일 스타일 반복 지시 | USER.md에 스타일 선호 기록 |
| 7 | Nudge 주기 동작 | 설정 후 N턴 대화 | 일정 턴 후 review 발생 |

---

## 8. 핵심 아키텍처 참고 (소스코드 기반)

### Nudge 메커니즘 (`run_agent.py`)
```
_memory_nudge_interval  →  N턴마다 memory review 실행
_skill_nudge_interval   →  N tool-iterations마다 skill review 실행
```
- Memory nudge: "대화에서 기억할 만한 것이 있는가?" → MEMORY.md/USER.md에 기록
- Skill nudge: "방금 한 작업을 재사용 가능한 skill로 만들 수 있는가?" → skill_manage(create) 실행

### Skill 파일 구조 (`~/.hermes/skills/`)
```
~/.hermes/skills/
├── my-skill/
│   ├── SKILL.md           # 메인 문서 (YAML frontmatter + Markdown)
│   ├── references/        # 참조 자료
│   ├── templates/         # 템플릿
│   ├── scripts/           # 스크립트
│   └── assets/            # 에셋
└── category-name/
    └── another-skill/
        └── SKILL.md
```

### Skill 생성 도구 (`tools/skill_manager_tool.py`)
- `action='create'`: 새 skill 생성
- `action='edit'`: 기존 skill 전체 교체
- `action='patch'`: 기존 skill 부분 수정 (fuzzy matching 지원)
- `action='delete'`: skill 삭제

---

## 9. 다른 도구와의 비교 참고

| 기능 | Hermes Agent | Claude Code | Codex CLI |
|------|-------------|-------------|-----------|
| Skill 자동 생성 | ● native | ○ 없음 | ○ 없음 |
| Memory Nudge | ● native | ◐ (CLAUDE.md) | ○ 없음 |
| `/learn` (명시적 학습) | ● native | ○ 없음 | ○ 없음 |
| Skill Self-improve | ● native | ○ 없음 | ○ 없음 |
| Skills Hub | ● agentskills.io | ○ 없음 | ○ 없음 |
| Proactive 제안 | ● nudge 기반 | ◐ 제한적 | ○ 없음 |

> ● = 1급(native·성숙) · ◐ = 부분 지원(제한적·간접) · ○ = 미지원/미확인
