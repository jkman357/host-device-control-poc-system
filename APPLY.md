# Apply the stream-rate correction

Base repository: `host-device-control-poc-system`

Base commit:

```text
e418afc3b3e866039c583a8ba4dc1a1049a9cec1
```

This package is an overlay/patch package, not a replacement for the complete repository.

## What changes

- Changes `SET_STREAM_CONFIG.interval_us` from `1000..60000` to `2500..60000`.
- Defines a Protocol maximum of 400 Hz for 24-byte telemetry frames over 115200-bps UART using 8N1.
- Keeps the default at 5000 us / 200 Hz.
- Requires `DEVICE_INFO.maximum_stream_rate_hz <= 400`.
- Adds an independent capacity validator and regression tests.
- Adds CI execution of the new checks.
- Records the new implementation-alignment gap.

## Why two commits are required

The repository provenance validator pins the commit that contains the authoritative `protocol/protocol.yaml` blob. A Git commit cannot contain its own SHA, so an authority-changing update must use two local commits before pushing:

1. commit the Protocol correction;
2. pin that first commit and its Protocol SHA-256 in a second commit.

Do not push between these two commits because the first commit intentionally has stale provenance metadata.

## Apply

From a clean clone:

```bash
git checkout e418afc3b3e866039c583a8ba4dc1a1049a9cec1

git apply host-device-control-poc-system-e418afc-stream-rate-fix.patch

python tools/validate_transport_capacity.py
python tools/test_transport_capacity_validator.py

git add .
git commit -m "fix(protocol): cap stream rate to UART capacity"

python tools/finalize_protocol_authority.py

python tools/validate_project_repository.py
python tools/validate_protocol_contract.py --require-git-history
python tools/test_protocol_validator_regressions.py
python tools/validate_transport_capacity.py
python tools/test_transport_capacity_validator.py

git add baselines/repositories.yaml protocol/implementation-status.yaml
git commit -m "chore(protocol): pin corrected authority baseline"
```

After both commits are present locally, push them together.

## Expected capacity calculation

```text
UART:                         115200 bps, 8N1
Wire bits per byte:           10
Telemetry payload:            14 bytes
Protocol frame overhead:      10 bytes
Telemetry frame:              24 bytes / 240 bits
Theoretical telemetry limit:  480 Hz
Protocol maximum:             400 Hz
Minimum configured interval:  2500 us
Nominal TX utilization:       83.33%
Default:                      5000 us / 200 Hz
```

The 400-Hz value is a Protocol admission limit. It is not hardware interoperability or long-duration qualification evidence.
