HWP to PDF Converter API
한컴 HWP/HWPX 파일을 PDF로 변환하는 REST API입니다.
개요
AWS EC2 Windows 환경에서 pywin32로 한컴 오피스 2024를 제어해서 HWP 파일을 PDF로 변환합니다.
서버 정보

주소: http://43.201.23.85:8000
인스턴스: t3.medium (Windows Server 2022)
현재 버전: v1.2.0

주요 기능

단일/다중 파일 변환
원본 한글 파일명 유지
변환 팝업 자동 처리
24시간마다 자동 재시작

빠른 시작
서버 실행
powershellcd C:\hwp-api
.\venv\Scripts\Activate.ps1
python app.py
Python 예제
pythonimport requests

# 파일 업로드
response = requests.post(
    "http://43.201.23.85:8000/convert",
    files={"file": open("document.hwp", "rb")}
)

result = response.json()
print(f"변환 완료: {result['pdf_filename']}")
print(f"소요 시간: {result['conversion_time_seconds']}초")

# PDF 다운로드
pdf = requests.get(f"http://43.201.23.85:8000{result['download_url']}")
with open(result['pdf_filename'], 'wb') as f:
    f.write(pdf.content)
다중 파일 변환
pythonfiles = [
    ("files", open("file1.hwp", "rb")),
    ("files", open("file2.hwpx", "rb")),
]

response = requests.post(
    "http://43.201.23.85:8000/convert-batch",
    files=files
)

result = response.json()
print(f"성공: {result['success_count']}/{result['total_files']}")
API
엔드포인트
메서드경로설명POST/convert단일 파일 변환POST/convert-batch다중 파일 변환GET/download/{filename}PDF 다운로드GET/health상태 확인GET/stats통계 조회
단일 파일 변환
bashcurl -X POST "http://43.201.23.85:8000/convert" \
  -F "file=@document.hwp"
응답:
json{
  "status": "success",
  "original_filename": "document.hwp",
  "pdf_filename": "document.pdf",
  "conversion_time_seconds": 3.3,
  "download_url": "/download/document.pdf"
}
다중 파일 변환
bashcurl -X POST "http://43.201.23.85:8000/convert-batch" \
  -F "files=@file1.hwp" \
  -F "files=@file2.hwpx"
상태 확인
bashcurl http://43.201.23.85:8000/health
서버 시작 시간과 다음 재시작 예정 시간을 확인할 수 있습니다.
설치 및 설정
요구사항

Windows Server 2022 이상
Python 3.11 이상
한컴 오피스 2024
AWS EC2

초기 설정
powershellcd C:\hwp-api

# 필요한 폴더 생성
@("input", "output", "logs", "scripts") | ForEach-Object { 
    New-Item -ItemType Directory -Path $_ -Force 
}

# 가상환경 생성
python -m venv venv
.\venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt
레지스트리 설정 (중요)
변환 시 나타나는 팝업을 자동으로 처리하려면 레지스트리 설정이 필요합니다.
수동 설정:

Win+R → regedit 실행
경로 이동: HKEY_CURRENT_USER\Software\Hnc\HwpAutomation\Modules
FilePathCheckerModule 값을 C:\hwp-api\scripts\FilePathCheckerModule.dll로 설정

자동 설정 (PowerShell):
powershell$regPath = "HKCU:\Software\Hnc\HwpAutomation\Modules"
$dllPath = "C:\hwp-api\scripts\FilePathCheckerModule.dll"

if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force | Out-Null
}

Set-ItemProperty -Path $regPath -Name "FilePathCheckerModule" `
    -Value $dllPath -Type String -Force
프로젝트 구조
C:\hwp-api\
├── app.py                    # FastAPI 서버
├── convert_hwp.py            # 변환 로직
├── batch_convert.py          # 배치 변환 스크립트
├── test_hwp_api.py           # 테스트 스크립트
├── requirements.txt
├── venv\
├── scripts\
│   └── FilePathCheckerModule.dll
├── input\                    # 임시 업로드
├── output\                   # 변환 결과
└── logs\
문제 해결
팝업창이 계속 나타남
레지스트리 설정을 확인하세요.

경로: HKEY_CURRENT_USER\Software\Hnc\HwpAutomation\Modules
값: FilePathCheckerModule = C:\hwp-api\scripts\FilePathCheckerModule.dll

API 연결 실패
powershell# 포트 확인
netstat -ano | findstr ":8000"

# 상태 확인
curl http://43.201.23.85:8000/health

# 서버 재시작
taskkill /F /IM python.exe
cd C:\hwp-api
.\venv\Scripts\Activate.ps1
python app.py
EC2 보안 그룹에서 포트 8000 인바운드 규칙도 확인하세요.
변환 실패

지원 형식: .hwp, .hwpx만 가능
파일 크기: 50MB 미만 권장
한컴 오피스 2024가 정상 설치되어 있는지 확인

기술 스택

FastAPI 0.104.1
Python 3.11
pywin32 306
한컴 오피스 2024
AWS EC2 (Windows Server 2022)

보안
현재는 개발 환경으로 운영 중입니다.
프로덕션 적용 시 고려사항:

API Key 인증
HTTPS 적용
Rate Limiting
CORS 제한

변경 이력

v1.2.0 (2025-11-06)

다중 파일 변환 지원
24시간 자동 재시작
레지스트리 자동 설정 스크립트


v1.1.0 (2025-11-05)

팝업 자동 처리
원본 파일명 유지


v1.0.0 (2025-11-05)

초기 버전



라이선스
MIT License

마지막 업데이트: 2025-11-06
