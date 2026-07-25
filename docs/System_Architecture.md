# System Architecture

## Topology

```text
Windows PC
┌─────────────────────────────────────────────────────────────┐
│ WPF UI                                                      │
│  └─ Application / ViewModel                                 │
│      └─ Device Session                                      │
│          └─ Protocol Codec and Command Correlation           │
│              └─ ITransport                                  │
│                  ├─ Fake Device Transport                   │
│                  └─ Serial Transport                        │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ ST-LINK Virtual COM Port
                         │ 115200, 8-N-1
                         ▼
NUCLEO-F446RE
┌─────────────────────────────────────────────────────────────┐
│ USART Transport                                             │
│  └─ Frame Receive / Resynchronization                       │
│      └─ Protocol Dispatch and Command Handling              │
│          └─ Application State and Telemetry Generator       │
│              └─ 5 ms sine-wave sample production           │
└─────────────────────────────────────────────────────────────┘
```

## Boundary Principles

- UI code does not parse frames or calculate CRC.
- Core Coordinator logic does not depend on WPF or the concrete serial transport.
- Serial transport moves bytes and does not own message meaning.
- Fake transport substitutes device behavior for PC development but does not prove target behavior.
- MCU transport and Protocol logic remain separate from application state and signal generation.
- Shared Protocol semantics are controlled at the system/project layer.

## Timing Model

- Nominal telemetry period: 5 ms.
- Nominal telemetry rate: 200 Hz.
- UI presentation rate: approximately 20 Hz.
- UI therefore consumes buffered/latest application state rather than one render per received sample.

## Initial Failure Cases

- serial disconnect;
- partial frame reception;
- garbage bytes before a valid frame;
- invalid CRC;
- unsupported wire version;
- unknown message ID;
- command timeout;
- telemetry sequence gap;
- UI slowdown while transport continues;
- MCU restart during a PC session.

## Out-of-Scope Architecture

- multiple Nodes;
- automatic reconnect and session recovery;
- authenticated or encrypted Protocol;
- firmware update;
- safety-related local control;
- production logging and retention.
