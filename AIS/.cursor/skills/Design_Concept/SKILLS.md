---
name: Design_Concept
description: 아키텍처 디자인 후보(Candidate Design) 도출 시 활용하는 5가지 Design Concepts을 (Reference Architecture, Deployment Pattern, Architecture Style, Tactics, Externally Developed Components)를 참조하여 설계에 가이드 한다.
---

# Design Concepts

Design concepts는 아키텍처 구조를 생성하고 candidate design(후보)을 도출하기 위한 핵심 구성 요소(Building Blocks)이다.

## 5가지 Design Concepts 요소

### 1. Reference Architecture (참조 아키텍처)
- **개념**: 특정 애플리케이션 유형에 대한 논리적 청사진(Logical Structure).
- **예시**: Web Applications, Mobile Applications, Rich Client Applications, Service-oriented Applications

### 2. Deployment Pattern (배포 패턴)
- **개념**: 논리적 구조를 물리적 구조(Physical Structure)로 배치하는 방식. 주요 품질 속성(QA: 성능, 보안, 가용성 등) 달성에 필수적.
- **예시**: Nondistributed, Distributed, High Performance/Reliability/Security Deployment

### 3. Architecture Style (아키텍처 스타일)
- **개념**: 도메인 독립적이며 재사용 가능한 일반적 구조 레이아웃 및 특성 (Logical >> Physical).
- **예시**: Layered Architecture, MVC / MVP / MVVM, Client-Server, Microservices, Pipes and Filters, Blackboard

### 4. Tactics (아키텍처 전술)
- **개념**: 특정 품질 속성(QA)을 직접 제어하고 관리하기 위해 아키텍트가 사용하는 핵심 기법.
- **예시**: Availability Tactics, Performance Tactics, Security Tactics, Modifiability Tactics, Testability Tactics, Interoperability Tactics

### 5. Externally Developed Components (외부 개발 컴포넌트 / COTS)
- **개념**: 외부 상용/오픈소스 소프트웨어(COTS), 개발 프레임워크, 클라우드/플랫폼 활용.
- **예시**:
  - Application Framework: Spring, Hibernate, REST API, Swing 등
  - Platform: Java, .NET, Google Cloud, AWS 등
  - COTS (Commercial Off-The-Shelf) 및 기존 서드파티 라이브러리

---

## CDA 작성 시 활용 지침
- Candidate Design(CDA)을 도출할 때 각 QA/QAS를 만족시키기 위한 근거로 위의 **Design Concepts** 요소(스타일, 전술, COTS, 배포 패턴 등)를 조합하여 명시한다.
