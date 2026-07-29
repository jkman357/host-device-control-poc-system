# Project Input

## Project Identity

- Project name: `Host-Device Control PoC`
- System repository: `host-device-control-poc-system`
- Status: `Engineering proof of concept`
- Intended audience: embedded, PC application, system integration, and validation engineers

## Purpose

Demonstrate a traceable vertical slice in which a Windows PC application acts as the Coordinator and an STM32F446RE development board acts as the Node.

The PoC is intended to evaluate:

- shared Protocol definition before both implementations are complete;
- command/response communication;
- 5 ms telemetry generation and 200 Hz acquisition;
- transport separation from application behavior;
- PC fake-device development before hardware readiness;
- real serial integration through the ST-LINK Virtual COM Port;
- evidence-oriented use of the Host-Device Control Framework and Project Template.

## System Elements

| Element | Current choice | Project role |
|---|---|---|
| Coordinator | Windows WPF application, .NET 8 | Host-side control, display, logging, and command orchestration |
| Node | NUCLEO-F446RE / STM32F446RE firmware | Device-side command handling and telemetry generation |
| Transport | USART through ST-LINK Virtual COM Port | Byte transport between PC and MCU |
| Serial profile | 115200, 8-N-1, no flow control | Current PoC transport baseline |
| Protocol | Framed binary protocol, wire version `0x01` | Shared PC/MCU contract |
| Telemetry | Sine-wave sample every 5 ms | Initial streaming workload |
| UI refresh | 20 Hz target | Decoupled presentation rate |

## Presentation and Platform Boundary

| Input | Project value |
|---|---|
| Presentation present | Yes |
| Presentation framework | WPF on .NET 8 |
| Target platform | Windows desktop |
| Current cross-platform requirement | None; future UI replacement shall not require rewriting stable core behavior |
| UI-independent stable scope | Application use cases, device-session behavior, Protocol codec and correlation, device state, validation, data processing, timeout/retry policy, transport contracts, and non-UI tests |
| Presentation-specific scope | WPF View/XAML, ViewModel display state, binding, commands, navigation, dialogs, charts, visual styling, and UI-thread dispatch |
| Infrastructure-specific scope | Serial transport, fake transport, file/CSV output, logging adapters, and platform services |
| Composition root | WPF application startup assembles Presentation, Application/Core, and Infrastructure adapters |
| UI service ports | User notification, file selection, UI scheduling/dispatch, navigation, and other narrow presentation-facing services as actually required |
| Native or platform dependencies | WPF and Windows serial/device services; no Product-owned native DLL is currently required |
| Approved framework leakage exceptions | None recorded; any exception requires an identified owner, rationale, affected layer, and approval record |

The WPF layer is a replaceable Presentation adapter. Replaceable does not mean zero-cost migration: View, XAML, binding, navigation, charting, and other UI-framework-specific behavior may require reimplementation. The protected objective is to retain stable Application/Core, Protocol, device-session, and transport-contract behavior.

## Initial Goals

1. Build and run the PC application in fake-device mode.
2. Build and flash the STM32 firmware.
3. Establish command/response communication.
4. Start and stop 5 ms telemetry streaming.
5. Confirm frame integrity, sequence behavior, and loss detection.
6. Display a stable waveform without coupling the UI refresh rate to the transport rate.
7. Retain reproducible system-level evidence.
8. Demonstrate that core Coordinator tests can execute without creating a WPF application or window.

## Non-Goals

- production release;
- medical-device validation;
- safety certification;
- cybersecurity certification;
- multi-device operation;
- installer, code signing, or field update support;
- regulated data-retention capability;
- zero-cost UI-framework replacement;
- automatic Framework conformance claim.

## Known Inputs Requiring Human Confirmation

- final system-level acceptance thresholds for jitter, loss, and recovery;
- exact STM32CubeIDE and toolchain versions;
- exact PC and MCU implementation commits aligned to the shared Protocol authority;
- evidence storage and retention rules;
- release/tagging convention for the completed PoC baseline;
- any future approved UI-framework or platform-dependency exception.
