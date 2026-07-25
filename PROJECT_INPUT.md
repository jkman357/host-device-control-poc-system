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

## Initial Goals

1. Build and run the PC application in fake-device mode.
2. Build and flash the STM32 firmware.
3. Establish command/response communication.
4. Start and stop 5 ms telemetry streaming.
5. Confirm frame integrity, sequence behavior, and loss detection.
6. Display a stable waveform without coupling the UI refresh rate to the transport rate.
7. Retain reproducible system-level evidence.

## Non-Goals

- production release;
- medical-device validation;
- safety certification;
- cybersecurity certification;
- multi-device operation;
- installer, code signing, or field update support;
- regulated data-retention capability;
- automatic Framework conformance claim.

## Known Inputs Requiring Human Confirmation

- final system-level acceptance thresholds for jitter, loss, and recovery;
- exact STM32CubeIDE and toolchain versions;
- protocol source-of-truth migration decision;
- evidence storage and retention rules;
- release/tagging convention for the completed PoC baseline.
