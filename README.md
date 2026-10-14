# HWP to PDF Converter API

Windows 환경에서 HWP 계열 문서를 PDF로 변환하는 FastAPI 기반 API 프로토타입입니다.

## Overview

이 프로젝트는 `pywin32`로 한컴 오피스 자동화를 제어하여 HWP/HWPX 문서를 PDF로 변환합니다.

지원 형식:

- `.hwp`
- `.hwpx`
- `.hwt`
- `.hwtx`

## Public Positioning

문서 변환 API와 사내 문서 워크플로 자동화 PoC를 설명하기 위한 저장소입니다. AI Technical Consultant / GenAI Pre-Sales / PoC Builder 포지셔닝에서는 문서 처리 자동화와 API 기반 PoC 구현 사례로 볼 수 있습니다.

## Requirements

- Windows Server 2022 이상
- Python 3.12 이상
- 한컴 오피스 2024

## Setup

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pywin32_postinstall -install
```

## Run

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app:app --host 127.0.0.1 --port 9000 --workers 1
```

API 문서:

```text
http://127.0.0.1:9000/docs
```

## Python Example

```python
import requests

base_url = "http://127.0.0.1:9000"

with open("document.hwp", "rb") as file:
    response = requests.post(
        f"{base_url}/convert",
        files={"file": file},
    )

response.raise_for_status()
result = response.json()

pdf_url = result["download_url"]
pdf = requests.get(f"{base_url}{pdf_url}")
pdf.raise_for_status()

with open("output.pdf", "wb") as file:
    file.write(pdf.content)
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/convert` | Convert one file |
| POST | `/convert-batch` | Convert multiple files |
| GET | `/download/{job_id}/{filename}` | Download the completed PDF for one job |
| GET | `/download/{filename}` | Compatibility for existing flat output PDFs |
| GET | `/health` | Health check |
| GET | `/stats` | Completed PDF count, size, and relative download identifiers |

## File Isolation and API Compatibility

Each accepted file gets a full 32-character UUID job ID. Its input is stored as
`input/<job_id>/source.<extension>` and its PDF as `output/<job_id>/result.pdf`.
The original basename is used for `pdf_filename` and the browser download name,
not as a storage path. Client-side directory components are discarded. Both the
single and batch endpoints use these same rules, including duplicate names
within one batch or across concurrent requests.

The existing success fields remain. Batch success rows additionally include
`job_id`. Always follow the returned `download_url`; new URLs are
`/download/<job_id>/<URL-encoded-display-name>.pdf`. Clients that constructed URLs
from `pdf_filename` must switch to `download_url`. Existing flat PDFs remain
available through the old `/download/{filename}` route. Older PDFs that were
already overwritten cannot be recovered by this change.

The download mapping is stored in `metadata.json` beside each completed PDF and
survives server restarts. Downloads require the exact job ID and mapped display
name. `/stats.files` lists relative download identifiers, so a new entry includes
both the job ID and display name. These IDs distinguish outputs; they are not an
authentication or authorization system.

## Execution, Timeout, and Cleanup

Use **one Uvicorn worker and one server instance**. A process-local asynchronous
lock permits one Hancom conversion subprocess at a time. This does not support
multiple API processes sharing the same Hancom desktop/session. The HTTP event
loop awaits subprocess completion asynchronously and can serve health and other
requests while a conversion is running. On Windows, use the default Proactor
event loop; `--reload`, multiple workers, or a custom Selector event loop are not
supported by this execution model.

The conversion subprocess has a 120-second timeout, starting when it is spawned;
time queued for the conversion lock is additional. An ordinary nonzero exit or
missing PDF returns HTTP 500. A known Hancom `Quit()` failure has a distinct worker
exit status (2), disables further conversions while the serialization lock is
still held, and returns HTTP 503 instead of publishing the PDF. A timeout returns
HTTP 504. Batch requests retain their
`completed` response and report per-file failures. Detailed worker stdout/stderr
is drained but is not returned to clients because it can contain local paths or
document details.

On Windows, a small bootstrap joins a kernel Job Object before executing any
converter code. The API owns that job handle; ordinary descendants inherit job
membership, and job termination does not depend on a parent PID remaining alive.
The job also has `KILL_ON_JOB_CLOSE` enabled. After completion, failure, timeout,
or ASGI task cancellation, the server terminates remaining owned job members,
reaps its worker, and confirms the job has no active processes before releasing
the conversion lock. Repeated task cancellation cannot skip that cleanup. If cleanup
cannot be confirmed, further conversions are disabled with HTTP 503 and health
reports `degraded`. An ordinary client disconnect does not necessarily cancel an
ASGI task; that conversion may continue until completion or timeout.

Inputs are removed after success, failure, timeout, or task cancellation. Failed
or cancelled jobs' partial outputs are removed. Successful PDFs and their
metadata are retained until an operator removes the corresponding job directory;
there is no automatic expiry. Earlier successful files in an interrupted batch
are retained. Cleanup touches only directories created for the current job.

The COM script requests a separate automation object with `DispatchEx` and calls
`Quit()` in a `finally` block on normal completion or Python exceptions. A COM
server launched outside the owned worker job cannot be guaranteed to terminate
with that job. A known `Quit()` failure is therefore treated as cleanup uncertainty
even if the owned job was successfully stopped. Real Hancom timeout/cancellation behavior must be
verified in the intended Windows/Hancom session; do not kill unrelated `Hwp.exe`
processes by image name. If cleanup is uncertain, inspect the conversion session
and stop leftover automation before manually restarting this API.

## Health and Restart Policy

This repository does **not** implement automatic restart or include a deployment
supervisor. The former watchdog called `sys.exit()` in a background thread,
which could stop that thread but could not restart the API process; it has been
removed. `/health` and `/stats` now report `automatic_restart_enabled: false` and
`next_restart_at: null`; `/health.restart_interval_hours` is also `null`.
The health endpoint reports process liveness/configuration and cleanup-blocked
state, not successful Hancom integration. Restarts are an operator action unless
an external supervisor is separately configured and verified.

## Regression Tests

```powershell
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m py_compile app.py convert_hwp.py worker_runtime.py tests/test_app.py tests/test_convert_hwp.py tests/fake_converter.py
```

Tests use artificial input specifications and a synthetic Python conversion
worker in temporary directories. They cover duplicate filenames, single/batch
isolation, serialization, event-loop responsiveness, download mapping and path
boundaries, failure, timeout, repeated cancellation, process spawning races, and
worker/descendant termination on Windows, including a child holding inherited
pipes after its parent has exited. COM unit tests use mocks only and verify that
`Quit()` failures are propagated as cleanup uncertainty. The parent-exit fixtures
use the base Python interpreter so the Windows virtual-environment launcher's
own process cleanup cannot mask this scenario.
The symlink boundary test skips explicitly if Windows does not grant symlink
creation permission. These tests do not prove real Hancom conversion or COM
server cleanup, and they do not restart a deployment.

## Optional HWP Automation Module Path

The app sets the DLL path dynamically. If manual setup is needed, use an environment-specific absolute path rather than committing a local machine path.

```powershell
$regPath = "HKCU:\Software\HNC\HwpAutomation\Modules"
$dllPath = "<repo-root>\scripts\FilePathCheckerModule.dll"

New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty -Path $regPath -Name "FilePathCheckerModule" -Value $dllPath -Force
```

## Firewall Example

Only open the port in environments where this service is intentionally exposed.

```powershell
netsh advfirewall firewall add rule name="HWP to PDF API Port 9000" dir=in action=allow protocol=TCP localport=9000
```

## Tech Stack

- FastAPI 0.121.0
- Python 3.12
- pywin32 311
- 한컴 오피스 2024

## Limitations

- Windows and local 한컴 오피스 automation are required.
- This is a document workflow/API prototype, not a hosted conversion service.
- Network host, firewall, and deployment choices should be reviewed per environment.

## Change History

- **v1.5.0** (2026-10-14)
  - Isolated every conversion job and added durable scoped download URLs
  - Serialized asynchronous conversion execution and Job Object worker ownership
  - Blocked further conversions on known Hancom termination uncertainty
  - Removed the ineffective automatic restart watchdog and corrected health fields
  - Added synthetic worker and mocked COM regression tests
- **v1.4.0** (2025-11-10)
  - Changed subprocess execution to use `sys.executable`
  - Updated registry path from `HwpCtrl` to `HwpAutomation`
  - Added dynamic DLL path setup
  - Fixed cp949 encoding issue
  - Changed port from 8000 to 9000
- **v1.3.0** (2025-11-06)
  - Added HWT/HWTX format support
- **v1.2.0** (2025-11-06)
  - Added batch conversion support
  - Added a 24-hour watchdog (ineffective restart behavior; removed in v1.5.0)

Last updated: 2026-10-14
