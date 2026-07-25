# Project Requirements

These are initial PoC requirements. They require human review before becoming an approved project baseline.

| ID | Requirement | Verification method | Status |
|---|---|---|---|
| SYS-001 | The system shall support one PC Coordinator connected to one STM32F446RE Node. | Architecture review and integration test | Draft |
| SYS-002 | The transport shall use the ST-LINK Virtual COM Port at 115200 baud, 8 data bits, no parity, 1 stop bit, and no flow control. | Configuration inspection and connection test | Draft |
| SYS-003 | PC and MCU shall implement the same identified Protocol wire version and test-vector baseline. | Baseline inspection and cross-language vector comparison | Draft |
| SYS-004 | The PC shall issue commands and correlate direct responses by sequence value. | Component and integration tests | Draft |
| SYS-005 | The MCU shall support start and stop control of telemetry streaming. | Integration test | Draft |
| SYS-006 | The MCU shall produce a telemetry sample at a nominal 5 ms interval when configured for 5000 microseconds. | Timing capture | Draft |
| SYS-007 | The PC shall acquire nominal 200 Hz telemetry without requiring the UI to refresh at 200 Hz. | Architecture inspection and performance test | Draft |
| SYS-008 | The PC shall expose detected loss through the telemetry sample counter. | Fault-injection or controlled-drop test | Draft |
| SYS-009 | Invalid CRC frames shall not be accepted as valid messages. | Component and target fault-injection tests | Draft |
| SYS-010 | Every validation conclusion shall identify exact PC, MCU, Protocol, and system-project baselines. | Evidence review | Draft |
| SYS-011 | Fake-device execution shall be reported separately from hardware interoperability execution. | Evidence review | Draft |
| SYS-012 | The PoC shall not be represented as production-ready, safety-approved, or regulatory-validated. | Release/document review | Draft |
