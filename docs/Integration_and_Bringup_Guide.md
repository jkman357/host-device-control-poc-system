# Integration and Bring-up Guide

## Phase A — PC Component Readiness

- Build the solution in Release configuration.
- Run the dependency-free Protocol tests.
- Start fake-device mode.
- Confirm connect, device information, start/stop stream, waveform, counters, and CSV behavior.
- Record results separately from hardware tests.

## Phase B — MCU Component Readiness

- Confirm Product-owned folders and generated-code boundaries.
- Build with warnings enabled.
- Flash the board.
- Confirm USART configuration and receive path.
- Exercise frame parser with known vectors where practical.
- Confirm command dispatch and streaming state transitions.
- Confirm 5 ms scheduling source and bounded transmit behavior.

## Phase C — First Link

Recommended order:

1. Open COM port.
2. Send `PING`; expect `ACK`.
3. Send `GET_DEVICE_INFO`; verify payload.
4. Send `SET_STREAM_CONFIG` with `5000` microseconds; expect `ACK`.
5. Send `START_STREAM`; expect `ACK` and telemetry.
6. Observe at least 10 seconds of sequence and timing behavior.
7. Send `STOP_STREAM`; expect bounded stop behavior.
8. Disconnect cleanly.

## Phase D — Fault and Recovery

- inject garbage bytes before a valid frame;
- corrupt CRC;
- fragment a frame across serial reads;
- send an unknown message ID;
- send a valid command in an invalid state;
- disconnect during streaming;
- reset the board during a session;
- slow or pause UI rendering while transport remains active.

## Evidence Minimum

- system, PC, firmware, and Protocol commit identities;
- board and ST-LINK identity where available;
- PC OS, .NET, Visual Studio, STM32CubeIDE, and compiler versions;
- serial configuration;
- execution date and operator;
- command/response transcript;
- timing/loss summary;
- screenshots or captures;
- anomaly and defect references;
- evidence hashes.
