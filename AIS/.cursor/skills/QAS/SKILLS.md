---
name: QAS
description: QA에 대해서 QAS (Quality Attribute Scenario)를 지정된 포맷으로 정리한다.
---

QA 요구사항에 대한 QAS (Quality Attribute Scenario)를 작성한다.

## 구성 지침

1. **QAS List 표**
   - QAS 섹션 시작 부분에 전체 QAS 목록 표를 작성한다.
   - 열 구성: `ID`, `Title`, `QA Type`, `description`

2. **QAS별 상세 내용**
   - 각 QAS 항목은 6개의 요소로 구성된 그림(Mermaid 다이어그램), 시나리오 한문장, 그리고 이 그림과 동일한 내용을 가지는 표로 구성된다.
   - 6개 요소:
     - Source of Stimulus
     - Stimulus
     - Artifact
     - Environment
     - Response
     - Response Measure
   - 시나리오 한문장 형태 : [환경]에서 [자극원]이 [자극]을 발생시키면, [대상]은 [응답]하고 [측정값]을 만족해야한다.
      - 예시
        - Source of Stimulus : 배터리센서
        - Stimulus : 잔량15% 이하
        - Artifact : 에너지·행동제어 컴포넌트
        - Environment : 청소수행중
        - Response : 청소중단 후 도킹 전환
        - Response Measure : 2초내 전환, 도킹성공률≥95%
        - 시나리오 한문장 => `청소수행중` `배터리센서`의 `잔량 15% 이하` 통지가 에너지행동제어 컴포넌트에 도달하면, `에너지행동제어` 컴포넌트는 `청소중단 후도킹 전환`을 `2초내 완료, 도킹성공률≥95% 달성` 한다.

3. **Response Measures 규격**
   - Response Measures 요소는 ISO/IEC 25023:2016 품질 측정 표준 기준을 사용한다.
