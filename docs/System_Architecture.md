# System Architecture

## Topology

```text
Windows PC
┌──────────────────────────────────────────────────────────────────────┐
│ Composition Root                                                    │
│  ├─ WPF Presentation Adapter                                        │
│  │   ├─ View / XAML / controls / charts                             │
│  │   ├─ ViewModel display and interaction state                     │
│  │   └─ UI service adapters and UI-thread scheduling                │
│  ├─ Application                                                     │
│  │   ├─ connect / disconnect / start / stop use cases               │
│  │   └─ workflow and session orchestration                          │
│  ├─ Core                                                            │
│  │   ├─ Device Session and device state                             │
│  │   ├─ Protocol Codec and Command Correlation                      │
│  │   ├─ validation / timeout / retry / data processing              │
│  │   └─ transport and persistence ports                             │
│  └─ Infrastructure Adapters                                         │
│      ├─ Fake Device Transport                                       │
│      ├─ Serial Transport                                            │
│      └─ file / CSV / logging services                               │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              │ ST-LINK Virtual COM Port
                              │ 115200, 8-N-1
                              ▼
NUCLEO-F446RE
┌──────────────────────────────────────────────────────────────────────┐
│ USART Transport                                                      │
│  └─ Frame Receive / Resynchronization                                │
│      └─ Protocol Dispatch and Command Handling                       │
│          └─ Application State and Telemetry Generator                │
│              └─ 5 ms sine-wave sample production                    │
└──────────────────────────────────────────────────────────────────────┘
```

## Dependency Direction

```text
WPF Presentation  ──►  Application  ──►  Core
       │                    ▲              ▲
       └──── UI ports ──────┘              │
Infrastructure Adapters ───────────────────┘
```

- The WPF Presentation project may depend on Application and Core contracts.
- Application may depend on Core.
- Infrastructure implements ports owned by Application/Core and is connected at the Composition Root.
- Core shall not depend on WPF, concrete serial/file implementations, windows, controls, visual types, or a UI Dispatcher.
- Dependencies shall not be inverted merely by moving WPF types into shared DTOs or broad wrapper interfaces.

## Presentation Boundary

WPF is a replaceable Presentation adapter, not the owner of Protocol, device-session, timeout/retry, validation, data-processing, or persistence rules.

Application and Core layers shall not reference WPF-specific assemblies, namespaces, controls, windows, brushes, visibility values, dialog classes, or Dispatcher implementations. When core behavior needs an external capability, it shall depend on a narrow project-owned port whose vocabulary reflects the use case rather than copying a UI Framework API.

Examples of Presentation-owned behavior include:

- XAML, View, control layout, styling, visual state, and chart configuration;
- ViewModel selection, expansion, navigation, display formatting, and command exposure;
- dialog/window ownership and UI-thread dispatch implementation;
- conversion from core state to colors, icons, localized text, and visibility.

Examples of protected Application/Core behavior include:

- connect, disconnect, start-stream, stop-stream, and export workflows;
- Protocol framing, parsing, CRC, message IDs, endianness, and correlation;
- device/session state, timeout, retry, error classification, and sequence/loss handling;
- telemetry buffering, validation, processing, and UI-independent logging decisions;
- ports for transport, persistence, time, notification intent, or other external services.

ViewModels may remain Presentation-layer artifacts and may require replacement with another UI technology. The architecture does not require every ViewModel or command abstraction to be cross-framework reusable.

## Composition Root and UI Service Ports

The WPF application startup is the Composition Root. It selects and wires:

- fake or serial transport;
- Application/Core services;
- WPF notification, file-selection, navigation, and UI-scheduling adapters;
- file, CSV, and logging infrastructure.

UI service ports shall remain narrow. They shall not expose `Window`, `Control`, `Brush`, `Visibility`, `Dispatcher`, or equivalent concrete UI-framework types to Application/Core.

## UI Replacement Scope

A future WPF replacement may require rewriting:

- View/XAML and layout;
- binding and command plumbing;
- navigation, dialogs, keyboard/mouse behavior, and accessibility integration;
- chart controls, virtualization, rendering caches, and UI-thread scheduling;
- framework-specific ViewModels or presentation adapters.

The intended retained scope is Application/Core behavior, Protocol authority and codec, device-session rules, transport contracts, data processing, persistence contracts, and their UI-independent tests.

## Boundary Principles

- UI code does not parse frames or calculate CRC.
- Core Coordinator logic does not depend on WPF or the concrete serial transport.
- Serial transport moves bytes and does not own message meaning.
- Fake transport substitutes device behavior for PC development but does not prove target behavior.
- MCU transport and Protocol logic remain separate from application state and signal generation.
- Shared Protocol semantics are controlled at the system/project layer.
- UI replacement shall not silently change Protocol semantics or device behavior.
- Any approved UI-framework leakage outside Presentation shall be explicit, narrow, reviewed, and recorded.

## Timing Model

- Nominal telemetry period: 5 ms.
- Nominal telemetry rate: 200 Hz.
- UI presentation rate: approximately 20 Hz.
- UI therefore consumes buffered/latest application state rather than one render per received sample.
- UI slowdown shall not block transport receive, Protocol parsing, sequence tracking, or evidence capture.

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
- UI thread unavailable or overloaded while non-UI processing continues;
- MCU restart during a PC session.

## Out-of-Scope Architecture

- multiple Nodes;
- automatic reconnect and session recovery;
- authenticated or encrypted Protocol;
- firmware update;
- safety-related local control;
- production logging and retention;
- cross-platform UI delivery in the current PoC.
