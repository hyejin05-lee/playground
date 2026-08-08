# Detailed Design Specification for RVC SW Controller

## 1. 개요 (Overview)

본 문서는 RVC SW Controller의 상위 설계서인 `docs/Architecture_Design.md` 및 `docs/CDA_Evaluation_and_Design_Decision.md`를 바탕으로 작성된 공식 **Detailed Design (객체지향 상세 설계 명세서)**이다.

`docs/Architecture_Design.md`의 Element List에 명시된 서브시스템별 아키텍처 핵심 Component를 대상으로 정적 구조(Class Diagram)와 Provided Interface Operation Call 기반의 대표 내부 행위 시퀀스(Class/Object-level Sequence Diagram)를 상세 모델링한다. 각 Component의 Class Diagram에는 주 대상 클래스뿐만 아니라 Sequence Diagram에서 상호작용하는 관련 클래스 및 인터페이스 관계선(Association, Dependency, Realization)을 명확히 시각화한다.

---

## 2. Component Design Description (컴포넌트별 상세 설계)

### 2.1 Sensor Abstraction Subsystem (CDA-01-A) Component Design

#### 1) SensorFactory Component (Abstract Factory Pattern)

##### (1) Class Diagram
```mermaid
classDiagram
    namespace Sensor_Abstraction_Subsystem_CDA_01_A {
        class SensorType {
            <<enumeration>>
            ULTRASOUND
            INFRARED
            OPTICAL_DUST
        }
        class SensorFactory {
            +createObstacleSensor(type: SensorType) ObstacleSensorInterface*
            +createDustSensor(type: SensorType) DustSensorInterface*
        }
        class ObstacleSensorInterface {
            <<interface>>
            +getObstacleState()* ObstacleSignal
            +isObstacleDetected()* bool
        }
        class DustSensorInterface {
            <<interface>>
            +getDustLevel()* DustSignal
        }
        class UltrasoundSensorAdapter {
            +getObstacleState() ObstacleSignal
        }
        class InfraredSensorAdapter {
            +getObstacleState() ObstacleSignal
        }
        class OpticalDustSensorAdapter {
            +getDustLevel() DustSignal
        }
    }

    SensorFactory ..> UltrasoundSensorAdapter : instantiates
    SensorFactory ..> InfraredSensorAdapter : instantiates
    SensorFactory ..> OpticalDustSensorAdapter : instantiates

    UltrasoundSensorAdapter ..|> ObstacleSensorInterface : implements
    InfraredSensorAdapter ..|> ObstacleSensorInterface : implements
    OpticalDustSensorAdapter ..|> DustSensorInterface : implements
```

##### (2) Provided Interface Operation Call Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor InitSystem as System Boot Initializer

    box "System Boundary: RVC SW Controller System"
        participant Factory as SensorFactory
        participant UltraAdapter as UltrasoundSensorAdapter
        participant InfraAdapter as InfraredSensorAdapter
    end

    note over InitSystem, Factory: Provided Interface Operation Call: createObstacleSensor()
    InitSystem->>Factory: createObstacleSensor(ULTRASOUND)
    Factory->>UltraAdapter: static getInstance() / new UltrasoundSensorAdapter()
    UltraAdapter-->>Factory: return ObstacleSensorInterface*
    Factory-->>InitSystem: return ObstacleSensorInterface*
```

##### (3) SOLID Principles & Design Patterns Rationale
- **Abstract Factory Pattern**: 구체적인 센서 드라이버 생성 로직을 팩토리에 캡슐화하여 제어 루틴이 생성 코드에 직접 결합되지 않도록 함 (DIP 준수).
- **OCP (개방-폐쇄 원칙)**: 신규 센서 타입 추가 시 `SensorFactory`에 매핑 케이스를 확장하여 기존 제어 로직 변경을 제로화함.

---

#### 2) UltrasoundSensorAdapter & InfraredSensorAdapter Component (Plugin Adapters)

##### (1) Class Diagram
```mermaid
classDiagram
    namespace Sensor_Abstraction_Subsystem_CDA_01_A {
        class ObstacleSignal {
            <<enumeration>>
            NONE
            SINGLE_FRONT
            SINGLE_LEFT
            SINGLE_RIGHT
            SURROUND_CRITICAL
        }
        class ObstacleSensorInterface {
            <<interface>>
            +getObstacleState()* ObstacleSignal
            +isObstacleDetected()* bool
        }
        class UltrasoundSensorAdapter {
            -gpioTriggerPin: uint16_t
            -gpioEchoPin: uint16_t
            -ringBuffer: LockFreeRingBuffer~ObstacleSignal~
            +getObstacleState() ObstacleSignal
            +isObstacleDetected() bool
            -readHardwareDistanceMs() uint32_t
        }
        class InfraredSensorAdapter {
            -adcChannel: uint8_t
            -voltageThreshold: float
            -ringBuffer: LockFreeRingBuffer~ObstacleSignal~
            +getObstacleState() ObstacleSignal
            +isObstacleDetected() bool
            -readAdcVoltage() float
        }
        class LockFreeRingBuffer~T~ {
            -buffer: std::array~T, 64~
            -head: std::atomic~size_t~
            -tail: std::atomic~size_t~
            +push(item: T) bool
            +pop(item: T&) bool
        }
    }

    namespace Controller_Subsystem_CDA_02_A {
        class CleaningController {
            +processEvent(event: SensorEvent)
        }
    }

    UltrasoundSensorAdapter ..|> ObstacleSensorInterface : implements (LSP)
    InfraredSensorAdapter ..|> ObstacleSensorInterface : implements (LSP)
    UltrasoundSensorAdapter *-- LockFreeRingBuffer~T~ : owns pre-allocated
    InfraredSensorAdapter *-- LockFreeRingBuffer~T~ : owns pre-allocated

    CleaningController ..> ObstacleSensorInterface : reads via abstract
```

##### (2) Provided Interface Operation Call Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor ObstacleHW as Physical Obstacle Sensors (ObstacleSensorSubsystem)

    box "System Boundary: RVC SW Controller System"
        participant Adapter as UltrasoundSensorAdapter
        participant RingBuf as LockFreeRingBuffer~ObstacleSignal~
        participant Controller as CleaningController
    end

    ObstacleHW->>Adapter: GPIO Echo Pulse Interrupt
    Adapter->>Adapter: readHardwareDistanceMs()
    Adapter->>RingBuf: push(SINGLE_FRONT)

    note over Controller, Adapter: Provided Interface Operation Call: getObstacleState()
    Controller->>Adapter: getObstacleState()
    Adapter->>RingBuf: pop(signal)
    RingBuf-->>Adapter: signal = SINGLE_FRONT
    Adapter-->>Controller: return SINGLE_FRONT
```

##### (3) SOLID Principles & Design Patterns Rationale
- **Adapter Pattern & LSP**: 이종 하드웨어 디바이스 신호(GPIO, ADC)를 공통 인터페이스 `ObstacleSensorInterface`로 변환하여 상호 치환 가능성(LSP)을 보장.
- **Lock-Free Ring Buffer Mitigation**: 부팅 시 Pre-allocation되는 락프리 링 버퍼를 내장하여 런타임 동적 메모리 할당(0 Allocation)을 달성하고 1ms 이내 초고속 센서 판독 지원.

---

#### 3) OpticalDustSensorAdapter Component (Dust Sensor Adapter)

##### (1) Class Diagram
```mermaid
classDiagram
    namespace Sensor_Abstraction_Subsystem_CDA_01_A {
        class DustSignal {
            <<enumeration>>
            DUST_NORMAL
            DUST_HIGH
        }
        class DustSensorInterface {
            <<interface>>
            +getDustLevel()* DustSignal
        }
        class OpticalDustSensorAdapter {
            -pulsePin: uint8_t
            -ringBuffer: LockFreeRingBuffer~DustSignal~
            +getDustLevel() DustSignal
            -readDustDensityUg() float
        }
        class LockFreeRingBuffer~T~ {
            -buffer: std::array~T, 64~
            +push(item: T) bool
            +pop(item: T&) bool
        }
    }

    namespace Controller_Subsystem_CDA_02_A {
        class CleaningController {
            +processEvent(event: SensorEvent)
        }
    }

    OpticalDustSensorAdapter ..|> DustSensorInterface : implements
    OpticalDustSensorAdapter *-- LockFreeRingBuffer~T~ : owns pre-allocated
    CleaningController ..> DustSensorInterface : reads via abstract
```

##### (2) Provided Interface Operation Call Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor DustHW as Physical Dust Sensors (DustSensorSubsystem)

    box "System Boundary: RVC SW Controller System"
        participant DustAdapter as OpticalDustSensorAdapter
        participant RingBuf as LockFreeRingBuffer~DustSignal~
        participant Controller as CleaningController
    end

    DustHW->>DustAdapter: ADC Voltage Interrupt Signal
    DustAdapter->>DustAdapter: readDustDensityUg() -> 180ug/m3
    DustAdapter->>RingBuf: push(DUST_HIGH)

    note over Controller, DustAdapter: Provided Interface Operation Call: getDustLevel()
    Controller->>DustAdapter: getDustLevel()
    DustAdapter->>RingBuf: pop(signal)
    RingBuf-->>DustAdapter: signal = DUST_HIGH
    DustAdapter-->>Controller: return DUST_HIGH
```

##### (3) SOLID Principles & Design Patterns Rationale
- **ISP (인터페이스 분리 원칙)**: 장애물 센서와 분리된 단일 먼지 센서 전용 pure virtual interface `DustSensorInterface`를 실현하여 불필요한 메서드 의존을 배제.

---

### 2.2 Controller Subsystem (CDA-02-A) Component Design

#### 1) CleaningController Component (HFSM Top Controller)

##### (1) Class Diagram
```mermaid
classDiagram
    namespace Controller_Subsystem_CDA_02_A {
        class CleanModeState {
            <<enumeration>>
            STATE_IDLE
            STATE_NORMAL_CLEANING
            STATE_SINGLE_AVOIDANCE
            STATE_EMERGENCY_ESCAPE
            STATE_DUST_BOOST
        }
        class SensorEvent {
            +eventType: uint16_t
            +priority: uint8_t
            +timestampMs: uint64_t
        }
        class CleaningController {
            -currentState: CleanModeState
            -eventQueue: PriorityEventQueue*
            -motionController: MotionController*
            -dustController: DustBoosterController*
            +processEvent(event: SensorEvent)
            +transitionTo(newState: CleanModeState)
            +getCurrentState() CleanModeState
        }
        class PriorityEventQueue {
            +popEvent() SensorEvent
        }
        class MotionController {
            +handleObstacleAvoidance(type: ObstacleSignal)
        }
        class DustBoosterController {
            +triggerDustBoost(durationSec: uint32_t)
        }
    }

    CleaningController *-- CleanModeState : holds state
    CleaningController --> PriorityEventQueue : reads events
    CleaningController --> MotionController : delegates navigation
    CleaningController --> DustBoosterController : delegates power boost
```

##### (2) Provided Interface Operation Call Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor EventSource as Internal Priority Queue

    box "System Boundary: RVC SW Controller System"
        participant Controller as CleaningController
        participant Motion as MotionController
    end

    note over EventSource, Controller: Provided Interface Operation Call: processEvent()
    EventSource->>Controller: processEvent(OBSTACLE_SINGLE_FRONT)
    Controller->>Controller: transitionTo(STATE_SINGLE_AVOIDANCE)
    Controller->>Motion: handleObstacleAvoidance(SINGLE_FRONT)
    Motion-->>Controller: status = IN_PROGRESS
```

##### (3) SOLID Principles & Design Patterns Rationale
- **HFSM (Hierarchical State Machine) Pattern**: 최상위 청소 주기와 서브 상태 머신을 분리하여 상태 전이 복잡도를 단일화하고 결정론적 전이를 보장.
- **SRP (단일 책임 원칙)**: 청소 주기의 상태 관리 책임만 부여하고 주행 제어 및 모터 출력은 서브 컴포넌트로 위임.

---

#### 2) PriorityEventQueue Component (Preemptible Event Queue)

##### (1) Class Diagram
```mermaid
classDiagram
    namespace Controller_Subsystem_CDA_02_A {
        class SensorEvent {
            +eventType: uint16_t
            +priority: uint8_t
            +timestampMs: uint64_t
        }
        class PriorityEventQueue {
            -mutex: std::mutex
            -queue: std::priority_queue~SensorEvent~
            +pushEvent(event: SensorEvent) bool
            +popEvent() SensorEvent
            +clearHighPriorityEvents()
        }
        class CleaningController {
            +processEvent(event: SensorEvent)
        }
    }

    PriorityEventQueue *-- SensorEvent : holds events
    PriorityEventQueue --> CleaningController : dispatches events
```

##### (2) Provided Interface Operation Call Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor SensorHW as Physical Obstacle Sensors (ObstacleSensorSubsystem)

    box "System Boundary: RVC SW Controller System"
        participant Queue as PriorityEventQueue
        participant Controller as CleaningController
    end

    note over SensorHW, Queue: Provided Interface Operation Call: pushEvent()
    SensorHW->>Queue: pushEvent(SURROUND_CRITICAL, priority=MAX)
    Queue->>Queue: std::priority_queue insertion (Sorted by Priority)
    
    Queue->>Controller: processEvent(SURROUND_CRITICAL) - High-Priority Preempt
```

##### (3) SOLID Principles & Design Patterns Rationale
- **Thread-Safe Priority Queue Pattern**: 일반 이벤트를 선점(Preemption)하는 우선순위 정렬 큐로 100ms 이내 실시간 응답 보장.

---

#### 3) WatchdogPreemptionGuard Component (Safety Watchdog Guard)

##### (1) Class Diagram
```mermaid
classDiagram
    namespace Controller_Subsystem_CDA_02_A {
        class WatchdogPreemptionGuard {
            -timerId: timer_t
            -timeoutMs: uint32_t
            +armWatchdog(timeoutMs: uint32_t)
            +disarmWatchdog()
            +triggerPreemption()
        }
        class PriorityEventQueue {
            +triggerPreemption()
        }
    }

    WatchdogPreemptionGuard ..> PriorityEventQueue : interrupts & preempts
```

##### (2) Provided Interface Operation Call Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor SensorHW as Physical Obstacle Sensors (ObstacleSensorSubsystem)

    box "System Boundary: RVC SW Controller System"
        participant Watchdog as WatchdogPreemptionGuard
        participant Queue as PriorityEventQueue
    end

    SensorHW->>Watchdog: armWatchdog(50ms)
    
    alt Event Queue Blocking Timeout (50ms Elapsed)
        Watchdog->>Watchdog: timer_interrupt_handler()
        note over Watchdog, Queue: Provided Interface Operation Call: triggerPreemption()
        Watchdog->>Queue: triggerPreemption() - Hard Priority Preempt
    else Normal Event Processed
        SensorHW->>Watchdog: disarmWatchdog()
    end
```

##### (3) SOLID Principles & Design Patterns Rationale
- **Watchdog Mitigation Pattern**: 큐 동기화 지연 및 Deadlock 위험 발생 시 50ms 인터럽트로 선점을 하드 제어하여 안전성 100% 보장.

---

#### 4) MotionController Component (Sub-HFSM Avoidance Navigation)

##### (1) Class Diagram
```mermaid
classDiagram
    namespace Controller_Subsystem_CDA_02_A {
        class MovementDirection {
            <<enumeration>>
            DIR_FORWARD
            DIR_BACKWARD
            DIR_TURN_LEFT
            DIR_TURN_RIGHT
            DIR_STOP
        }
        class MotionController {
            -currentDirection: MovementDirection
            +navigateForward()
            +handleObstacleAvoidance(type: ObstacleSignal)
            +emergencyReverseAndTurn()
            +stopMovement()
        }
        class CleaningController {
            +transitionTo(newState: CleanModeState)
        }
    }

    namespace Actuator_Interface_Subsystem {
        class WheelActuatorInterface {
            <<interface>>
            +moveForward()*
            +moveBackward()*
            +turnLeft()*
            +turnRight()*
            +stop()*
        }
    }

    CleaningController --> MotionController : delegates navigation
    MotionController --> WheelActuatorInterface : commands wheel
```

##### (2) Provided Interface Operation Call Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor TopController as CleaningController

    box "System Boundary: RVC SW Controller System"
        participant Motion as MotionController
        participant WheelDriver as WheelActuatorInterface
    end

    actor WheelHW as Physical Wheel Motors (WheelActuatorInterface)

    note over TopController, Motion: Provided Interface Operation Call: handleObstacleAvoidance()
    TopController->>Motion: handleObstacleAvoidance(SINGLE_FRONT)
    Motion->>WheelDriver: stop()
    WheelDriver->>WheelHW: Motor Stop Signal
    Motion->>WheelDriver: turnLeft()
    WheelDriver->>WheelHW: PWM Turn Signal
```

##### (3) SOLID Principles & Design Patterns Rationale
- **Sub-HFSM Pattern & DIP**: 회피 주행 및 갇힘 탈출 이동 로직을 세부 추상화하고 `WheelActuatorInterface`에만 의존하여 모터 하드웨어 변경에 미치는 영향을 차단.

---

#### 5) DustBoosterController Component (Sub-HFSM Suction Booster)

##### (1) Class Diagram
```mermaid
classDiagram
    namespace Controller_Subsystem_CDA_02_A {
        class DustBoosterController {
            -boostTimerSec: uint32_t
            +triggerDustBoost(durationSec: uint32_t)
            +restoreNormalPower()
        }
        class CleaningController {
            +transitionTo(newState: CleanModeState)
        }
    }

    namespace Actuator_Interface_Subsystem {
        class CleanerActuatorInterface {
            <<interface>>
            +setVacuumPower(level: uint8_t)*
        }
    }

    CleaningController --> DustBoosterController : delegates power boost
    DustBoosterController --> CleanerActuatorInterface : commands suction
```

##### (2) Provided Interface Operation Call Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor TopController as CleaningController

    box "System Boundary: RVC SW Controller System"
        participant Booster as DustBoosterController
        participant CleanerDriver as CleanerActuatorInterface
    end

    actor CleanerHW as Physical Vacuum Motors (CleanerActuatorInterface)

    note over TopController, Booster: Provided Interface Operation Call: triggerDustBoost()
    TopController->>Booster: triggerDustBoost(10)
    Booster->>CleanerDriver: setVacuumPower(100)
    CleanerDriver->>CleanerHW: MAX Suction PWM Signal
```

##### (3) SOLID Principles & Design Patterns Rationale
- **SRP (단일 책임 원칙)**: 먼지 감지 시 청소 흡입 출력 강화 및 타이머 복원 제어만을 독립 담당.

---

### 2.3 Actuator Interface Subsystem Component Design

#### 1) WheelDriverAdapter Component (Wheel Actuator Driver)

##### (1) Class Diagram
```mermaid
classDiagram
    namespace Actuator_Interface_Subsystem {
        class WheelActuatorInterface {
            <<interface>>
            +moveForward()*
            +moveBackward()*
            +turnLeft()*
            +turnRight()*
            +stop()*
        }
        class WheelDriverAdapter {
            -leftPwmPin: uint8_t
            -rightPwmPin: uint8_t
            +moveForward()
            +moveBackward()
            +turnLeft()
            +turnRight()
            +stop()
            -writePwmDuty(left: float, right: float)
        }
    }

    namespace Controller_Subsystem_CDA_02_A {
        class MotionController {
            +navigateForward()
        }
    }

    WheelDriverAdapter ..|> WheelActuatorInterface : implements (LSP)
    MotionController --> WheelActuatorInterface : commands drive
```

##### (2) Provided Interface Operation Call Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor Motion as MotionController

    box "System Boundary: RVC SW Controller System"
        participant Driver as WheelDriverAdapter
    end

    actor WheelHW as Physical Wheel Motors (WheelActuatorInterface)

    note over Motion, Driver: Provided Interface Operation Call: moveForward()
    Motion->>Driver: moveForward()
    Driver->>Driver: writePwmDuty(0.8, 0.8)
    Driver->>WheelHW: Write PWM Register to /dev/pwmchip0
```

##### (3) SOLID Principles & Design Patterns Rationale
- **Adapter Pattern & LSP**: 물리 바퀴 모터 레지스터 드라이버 제어를 `WheelActuatorInterface`에 맞춰 실현(LSP 준수).

---

#### 2) CleanerDriverAdapter Component (Cleaner Actuator Driver)

##### (1) Class Diagram
```mermaid
classDiagram
    namespace Actuator_Interface_Subsystem {
        class CleanerActuatorInterface {
            <<interface>>
            +setVacuumPower(level: uint8_t)*
            +setMopEnabled(enabled: bool)*
        }
        class CleanerDriverAdapter {
            -suctionPwmPin: uint8_t
            -mopRelayPin: uint8_t
            +setVacuumPower(level: uint8_t)
            +setMopEnabled(enabled: bool)
            -writeRelayState(state: bool)
        }
    }

    namespace Controller_Subsystem_CDA_02_A {
        class CleaningController {
            +processEvent(event: SensorEvent)
        }
    }

    CleanerDriverAdapter ..|> CleanerActuatorInterface : implements (LSP)
    CleaningController --> CleanerActuatorInterface : commands vacuum/mop
```

##### (2) Provided Interface Operation Call Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    actor Controller as CleaningController

    box "System Boundary: RVC SW Controller System"
        participant Driver as CleanerDriverAdapter
    end

    actor CleanerHW as Physical Suction & Mop Motors (CleanerActuatorInterface)

    note over Controller, Driver: Provided Interface Operation Call: setMopEnabled()
    Controller->>Driver: setMopEnabled(true)
    Driver->>Driver: writeRelayState(true)
    Driver->>CleanerHW: Write Relay GPIO Output Signal
```

##### (3) SOLID Principles & Design Patterns Rationale
- **Adapter Pattern & LSP**: 흡입 모터 PWM 및 물걸레 모터 리레이 출력을 추상화 인터페이스 `CleanerActuatorInterface`로 격리 변환.
