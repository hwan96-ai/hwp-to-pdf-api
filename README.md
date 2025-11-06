# HWP to PDF Converter API

![Status](https://img.shields.io/badge/status-operational-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![License](https://img.shields.io/badge/license-MIT-blue)

한컴 HWP/HWPX 파일을 PDF로 자동 변환하는 REST API 서비스입니다.

## 🎯 특징

- ✅ **빠른 변환**: 3.3초/파일
- ✅ **단일 + 다중 파일**: 한 번에 여러 파일 변환
- ✅ **한글 지원**: 완벽한 한글 인식
- ✅ **팝업 제거**: 무인 자동화 가능
- ✅ **REST API**: 모든 플랫폼 호환
- ✅ **24시간 자동 재시작**: 메모리 누수 방지
- ✅ **쉬운 통합**: Dify, LangChain 등과 연동

## 🚀 빠른 시작

### 서버 실행 (EC2 Windows)

\\\powershell
cd C:\hwp-api
.\venv\Scripts\Activate.ps1
python app.py
\\\

서버 시작 후 API: http://43.201.23.85:8000

### 단일 파일 변환 (Python)

\\\python
import requests

response = requests.post(
    "http://43.201.23.85:8000/convert",
    files={"file": open("document.hwp", "rb")}
)

result = response.json()
print(f"변환 시간: {result['conversion_time_seconds']}초")
\\\

### 다중 파일 변환

\\\ash
python batch_convert.py
\\\

## 📡 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /convert | 단일 파일 변환 |
| POST | /convert-batch | **다중 파일 변환 (NEW)** |
| GET | /download/{filename} | PDF 다운로드 |
| GET | /health | 상태 확인 (재시작 시간 포함) |
| GET | /stats | 통계 조회 |

## 📊 성능

| 지표 | 값 |
|------|-----|
| 변환 속도 | 3.3초/파일 |
| 파일 크기 감소 | ~75% |
| 가용성 | 24/7 |
| 자동 재시작 | 24시간마다 |

## 🛠️ 설치 및 설정

### 요구사항

- Windows Server 2022+
- Python 3.11+
- 한컴 오피스 2024
- AWS EC2

### 1단계: 초기 설정 (한 번만)

\\\powershell
cd C:\hwp-api

# 폴더 생성
@("input", "output", "logs", "scripts") | ForEach-Object {
    New-Item -ItemType Directory -Path "C:\hwp-api\" -Force
}

# 가상환경 생성
python -m venv venv
.\venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt
\\\

### 2단계: 레지스트리 설정 (중요!) ⭐

**Windows 레지스트리 편집기에서 직접:**

1. Win+R → regedit 입력
2. 다음 경로로 이동:
   \\\
   Computer\HKEY_CURRENT_USER\Software\Hnc\HwpAutomation\Modules
   \\\
3. \FilePathCheckerModule\ 값 데이터를 다음으로 변경:
   \\\
   C:\hwp-api\scripts\FilePathCheckerModule.dll
   \\\

**또는 PowerShell로 자동 설정:**

\\\powershell
# 레지스트리 자동 등록
\ = "HKCU:\Software\Hnc\HwpAutomation\Modules"
\ = "C:\hwp-api\scripts\FilePathCheckerModule.dll"

if (-not (Test-Path \)) {
    New-Item -Path \ -Force | Out-Null
}

Set-ItemProperty -Path \ -Name "FilePathCheckerModule" -Value \ -Type String -Force

Write-Host "✅ 레지스트리 설정 완료"
\\\

### 3단계: 서버 시작

\\\powershell
cd C:\hwp-api
.\venv\Scripts\Activate.ps1
python app.py
\\\

## 💻 사용 예제

### 1. 단일 파일 변환

\\\python
import requests

response = requests.post(
    "http://43.201.23.85:8000/convert",
    files={"file": open("보고서.hwp", "rb")}
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ 변환 완료: {result['pdf_filename']}")
    print(f"   시간: {result['conversion_time_seconds']}초")
else:
    print(f"❌ 오류: {response.json()}")
\\\

### 2. 다중 파일 변환

\\\python
import requests

files = [
    ("files", open("자동차hwp.hwp", "rb")),
    ("files", open("계약서.hwpx", "rb")),
]

response = requests.post(
    "http://43.201.23.85:8000/convert-batch",
    files=files
)

result = response.json()
print(f"성공: {result['success_count']}/{result['total_files']}")
print(f"총 시간: {result['total_time_seconds']}초")
\\\

### 3. 상태 확인 (재시작 시간 포함)

\\\ash
curl http://43.201.23.85:8000/health

# 응답:
# {
#   "status": "healthy",
#   "started_at": "2025-11-06T10:54:00",
#   "uptime_hours": 2.5,
#   "next_restart_at": "2025-11-07T10:54:00",
#   "restart_interval_hours": 24
# }
\\\

### 4. Dify 통합

1. HTTP 요청 노드 생성
2. URL: \http://43.201.23.85:8000/convert\
3. 메서드: POST
4. 바디: multipart/form-data
5. 파일 필드: \ile\

### 5. cURL

\\\ash
# 파일 변환
curl -X POST "http://43.201.23.85:8000/convert" \
  -F "file=@document.hwp"

# PDF 다운로드
curl -O "http://43.201.23.85:8000/download/document.pdf"

# 상태 확인
curl "http://43.201.23.85:8000/health"
\\\

## 🔄 24시간 자동 재시작

서버가 24시간마다 자동으로 재시작됩니다:

- **시작 시간**: 서버 시작 시점
- **재시작 시간**: 시작 시간 + 24시간
- **목적**: 메모리 누수 방지, 안정성 향상

\/health\ 엔드포인트에서 다음 재시작 시간을 확인할 수 있습니다.

## 🔧 트러블슈팅

### 팝업창이 나옴

**해결책:**

1. Windows 레지스트리 편집기 열기 (Win+R → regedit)
2. 다음 경로로 이동:
   \\\
   Computer\HKEY_CURRENT_USER\Software\Hnc\HwpAutomation\Modules
   \\\
3. \FilePathCheckerModule\ 값을 \C:\hwp-api\scripts\FilePathCheckerModule.dll\로 설정

### API 연결 안 됨

\\\powershell
# 1. 포트 확인
netstat -ano | findstr ":8000"

# 2. 서버 상태 확인
curl http://43.201.23.85:8000/health

# 3. EC2 보안 그룹 확인
# AWS 콘솔 → 인바운드 규칙 → 포트 8000 개방 확인

# 4. 서버 재시작
taskkill /F /IM python.exe
Start-Sleep 2
cd C:\hwp-api
.\venv\Scripts\Activate.ps1
python app.py
\\\

### 변환 실패

- 파일 형식 확인 (.hwp, .hwpx만 지원)
- 파일 크기 확인 (50MB 이상이면 실패)
- 한컴 오피스 2024 설치 확인

## 📁 폴더 구조

\\\
C:\hwp-api\
├── app.py                    # FastAPI 메인 서버
├── convert_hwp.py            # 변환 로직
├── batch_convert.py          # 배치 변환 스크립트
├── test_hwp_api.py           # 단일 파일 테스트
├── requirements.txt          # Python 의존성
├── README.md                 # 이 파일
├── .gitignore                # Git 무시 파일
├── venv/                     # Python 가상환경
├── scripts/
│   └── FilePathCheckerModule.dll    # 팝업 제거 모듈
├── input/                    # 임시 업로드 폴더
├── output/                   # 변환된 PDF 저장
└── logs/                     # 로그 파일
\\\

## 📋 의존성

\\\
FastAPI==0.104.1
Uvicorn==0.24.0
python-multipart==0.0.6
pywin32==306
requests==2.31.0
\\\

## 🔐 보안 고려사항

### 현재 상태 (개발 환경)

- CORS 모두 허용
- 인증 없음
- HTTPS 미적용

### 프로덕션 시 권장사항

1. **API Key 인증 추가**
2. **HTTPS 적용** (SSL 인증서)
3. **Rate Limiting** 설정
4. **CORS 제한** (특정 도메인만)

## 📞 문의 및 지원

- **GitHub Issues**: 이슈 제출
- **작성자**: gkwog
- **상태**: 운영 중 ✅

## 📚 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [pywin32 가이드](https://github.com/pywin32/pywin32)

## 📄 라이선스

MIT License - 자유롭게 사용 가능

---

**마지막 업데이트**: 2025-11-06 10:55 KST

✨ **버전**: 1.2.0
- 다중 파일 변환 지원
- 24시간 자동 재시작 기능
- 레지스트리 설정 자동화