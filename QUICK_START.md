# Quick Start

## 1. Obtain the Sources

Clone the system repository and the two implementation repositories into sibling directories:

```text
workspace/
├── host-device-control-poc-system/
├── host-device-control-poc-pc-app/
└── host-device-control-poc-stm32f446re-fw/
```

Checkout the exact commits identified in `baselines/repositories.yaml` for the validation cycle.

## 2. Run PC-Only Mode

Prerequisites:

- Windows 10 or Windows 11;
- Visual Studio 2022 17.11 or later, or the .NET 8 SDK;
- `.NET desktop development` workload when using Visual Studio.

Commands:

```powershell
dotnet restore HostDeviceControl.Poc.sln
dotnet build HostDeviceControl.Poc.sln -c Release
./scripts/test.ps1
./scripts/run-fake.ps1
```

Expected engineering observation:

1. Select `Fake Device`.
2. Select `Connect`.
3. Select `Start Stream`.
4. Confirm waveform, sample count, and device tick activity.

This is a PC component and simulator check. It is not hardware interoperability evidence.

## 3. Build and Flash STM32 Firmware

1. Open the STM32CubeIDE project under `poc-446re`.
2. Confirm the active target is `STM32F446RE`.
3. Build without errors.
4. Flash through the ST-LINK USB connector.
5. Confirm the ST-LINK Virtual COM Port appears in Windows Device Manager.

Record IDE, compiler, board, firmware commit, build output, and flash outcome.

## 4. Run Hardware Integration

1. Open the PC application.
2. Select `Serial Port`.
3. Select the ST-LINK COM port.
4. Use `115200` baud.
5. Connect.
6. Execute device-information and stream-control commands.
7. Start telemetry.
8. Record protocol, timing, sequence, loss, and UI observations.

## 5. Record Evidence

For every executed test:

1. Copy `evidence/templates/Test_Execution_Record.md`.
2. Assign a unique execution ID.
3. Record exact repository commits and environment.
4. Preserve logs, screenshots, captures, and hashes.
5. Add the evidence to `docs/Evidence_Index.md`.
6. Update `docs/VV_Results.md` and `VALIDATION_STATUS.md`.

Do not mark a test `Pass` only because code exists or a README describes the expected behavior.
