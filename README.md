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
uvicorn app:app --host 127.0.0.1 --port 9000
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
| GET | `/download/{filename}` | Download converted PDF |
| GET | `/health` | Health check |

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
  - Added 24-hour automatic restart

Last updated: 2025-11-10
