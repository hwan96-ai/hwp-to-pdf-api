# HWP to PDF Converter API

Windows 환경에서 HWP 파일을 PDF로 변환하는 REST API

## 개요

pywin32로 한컴 오피스를 제어하여 HWP/HWPX 파일을 PDF로 변환합니다.

**지원 형식**: `.hwp`, `.hwpx`, `.hwt`, `.hwtx`

## 빠른 시작

### 서버 실행

cd C:\Users\AIService\Desktop\hwp-to-pdf-api
.\venv\Scripts\Activate.ps1
uvicorn app:app --host 0.0.0.0 --port 9000

text

### Python 예제

import requests

단일 파일 변환
response = requests.post(
"http://172.20.1.241:9000/convert",
files={"file": open("document.hwp", "rb")}
)
print(response.json())

PDF 다운로드
pdf_url = response.json()['download_url']
pdf = requests.get(f"http://172.20.1.241:9000{pdf_url}")
with open("output.pdf", "wb") as f:
f.write(pdf.content)

text

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/convert` | 단일 파일 변환 |
| POST | `/convert-batch` | 다중 파일 변환 |
| GET | `/download/{filename}` | PDF 다운로드 |
| GET | `/health` | 상태 확인 |

**API 문서**: `http://172.20.1.241:9000/docs`

## 설치

### 요구사항

- Windows Server 2022 이상
- Python 3.12 이상
- 한컴 오피스 2024

### 설정

가상환경 생성 및 활성화
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1

의존성 설치
pip install -r requirements.txt

pywin32 post-install
python -m pywin32_postinstall -install

text

### 레지스트리 설정

DLL 경로가 동적으로 설정되므로 별도 설정 불필요합니다.  
수동 설정이 필요한 경우:

$regPath = "HKCU:\Software\HNC\HwpAutomation\Modules"
$dllPath = "C:\Users\AIService\Desktop\hwp-to-pdf-api\scripts\FilePathCheckerModule.dll"

New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty -Path $regPath -Name "FilePathCheckerModule" -Value $dllPath -Force

text

### 방화벽 설정

netsh advfirewall firewall add rule name="HWP to PDF API Port 9000" dir=in action=allow protocol=TCP localport=9000

text

## 기술 스택

- FastAPI 0.121.0
- Python 3.12
- pywin32 311
- 한컴 오피스 2024

## 변경 이력

- **v1.4.0** (2025-11-10)
  - subprocess에서 sys.executable 사용하도록 수정
  - 레지스트리 경로 수정 (HwpCtrl → HwpAutomation)
  - DLL 경로 동적 설정
  - cp949 인코딩 오류 수정
  - 포트 변경 (8000 → 9000)

- **v1.3.0** (2025-11-06)
  - hwt, hwtx 형식 지원 추가

- **v1.2.0** (2025-11-06)
  - 다중 파일 변환 지원
  - 24시간 자동 재시작

## 라이선스

MIT License

---

마지막 업데이트: 2025-11-10