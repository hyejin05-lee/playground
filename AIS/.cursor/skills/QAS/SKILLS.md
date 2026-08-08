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
   - 각 QAS 항목은 6개의 요소로 구성된 그림(Mermaid 다이어그램)과 이 그림과 동일한 내용을 가지는 표로 구성된다.
   - 6개 요소:
     - Source of Stimulus
     - Stimulus
     - Artifact
     - Environment
     - Response
     - Response Measure

3. **Response Measures 규격**
   - Response Measures 요소는 ISO/IEC 25023:2016 품질 측정 표준 기준을 사용한다.
