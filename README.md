# HWP to PDF Converter API

![Status](https://img.shields.io/badge/status-operational-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![License](https://img.shields.io/badge/license-MIT-blue)

한컴 HWP/HWPX 파일을 PDF로 자동 변환하는 REST API 서비스입니다.

## 🎯 특징

- ✅ **빠른 변환**: 3.3초/파일
- ✅ **배치 처리**: 여러 파일 동시 변환
- ✅ **한글 지원**: 완벽한 한글 인식
- ✅ **팝업 제거**: 무인 자동화 가능
- ✅ **REST API**: 모든 플랫폼 호환
- ✅ **쉬운 통합**: Dify, LangChain 등과 연동

## 🚀 빠른 시작

### 서버 실행 (EC2 Windows)

\\\powershell
cd C:\hwp-api
.\venv\Scripts\Activate.ps1
python app.py
\\\

서버 시작 후 API: http://43.201.23.85:8000

### 파일 변환 (Python)

\\\python
import requests

response = requests.post(
    "http://43.201.23.85:8000/convert",
    files={"file": open("document.hwp", "rb")}
)

result = response.json()
print(f"변환 시간: {result['conversion_time_seconds']}초")
print(f"다운로드: {result['download_url']}")
\\\

### 배치 변환

\\\ash
python batch_convert.py
\\\

## 📡 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /convert | HWP/HWPX → PDF 변환 |
| GET | /download/{filename} | PDF 다운로드 |
| GET | /health | 상태 확인 |
| GET | /stats | 통계 조회 |

## 📊 성능

| 지표 | 값 |
|------|-----|
| 변환 속도 | 3.3초/파일 |
| 파일 크기 감소 | ~75% |
| 가용성 | 24/7 |
| 동시성 | 무제한 |
| API 응답시간 | <100ms |

## 🛠️ 설치 및 설정

### 요구사항

- Windows Server 2022+
- Python 3.11+
- 한컴 오피스 2024
- AWS EC2 (또는 Windows 머신)

### 초기 설정 (RDP - 한 번만)

\\\powershell
cd C:\hwp-api

# 1. Git 설정
git config --global user.name "Developer"
git config --global user.email "dev@example.com"

# 2. Python 가상환경 생성
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 필수 폴더 생성
@("input", "output", "logs", "scripts") | ForEach-Object {
    New-Item -ItemType Directory -Path "C:\hwp-api\" -Force
}

# 5. 팝업 제거 모듈 등록
\ = "HKLM:\Software\HNC\HwpCtrl\Modules"
if (-not (Test-Path \)) { New-Item -Path \ -Force }
Set-ItemProperty -Path \ -Name "FilePathCheckerModule" -Value "C:\hwp-api\scripts\FilePathCheckerModule.dll"

# 6. 서버 시작
python app.py
\\\

## 📝 사용 예제

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
else:
    print(f"❌ 오류: {response.json()}")
\\\

### 2. 배치 변환

\\\python
# batch_convert.py 실행
python batch_convert.py

# 출력:
# 🚀 배치 HWP → PDF 변환
# ✅ 자동차hwp.hwp → 자동차hwp.pdf (3.24초)
# ✅ 계약서.hwpx → 계약서.pdf (3.30초)
# 총 시간: 6.54초
\\\

### 3. cURL

\\\ash
# 파일 변환
curl -X POST "http://43.201.23.85:8000/convert" \
  -F "file=@document.hwp"

# PDF 다운로드
curl -O "http://43.201.23.85:8000/download/document.pdf"

# API 상태 확인
curl "http://43.201.23.85:8000/health"
\\\

### 4. Dify 통합

1. HTTP 요청 노드 생성
2. URL: \http://43.201.23.85:8000/convert\
3. 메서드: POST
4. 바디: multipart/form-data
5. 파일 필드: \ile\
6. 응답: \download_url\ 추출

## 🔧 트러블슈팅

### API 연결 안 됨

\\\powershell
# 1. 포트 확인
netstat -ano | findstr ":8000"

# 2. 서버 상태 확인
curl http://43.201.23.85:8000/health

# 3. EC2 보안 그룹 확인
# AWS 콘솔 → 보안 그룹 → 인바운드 규칙 (포트 8000 개방)

# 4. 서버 재시작
taskkill /F /IM python.exe
Start-Sleep 2
cd C:\hwp-api
.\venv\Scripts\Activate.ps1
python app.py
\\\

### 변환 실패 (500 오류)

\\\powershell
# 1. EC2 재부팅
Restart-Computer -Force

# 2. 서버 재시작
taskkill /F /IM python.exe
python app.py

# 3. 파일 형식 확인 (.hwp, .hwpx만 지원)
\\\

### 느린 변환

- EC2 인스턴스 성능 확인 (CPU, 메모리)
- 동시 요청 제한 또는 대기열 추가 고려

## 📊 모니터링

### 통계 조회

\\\ash
curl "http://43.201.23.85:8000/stats"

# 응답:
# {
#   "total_pdfs": 5,
#   "total_size_mb": 0.55,
#   "output_dir": "C:\\hwp-api\\output",
#   "files": ["자동차hwp.pdf", "보고서.pdf"]
# }
\\\

### 로그 확인

RDP 서버 실행 중 실시간 로그 확인:

\\\
INFO:__main__:[a9c375c7] 파일 저장: 자동차hwp.hwp
INFO:__main__:[a9c375c7] 변환 시작...
INFO:__main__:[a9c375c7] 변환 완료 (0.11MB, 3.30초)
\\\

## 🔄 서버 자동 시작 (Windows 스케줄러)

\\\powershell
# RDP에서 관리자 권한으로 실행
\ = New-ScheduledTaskTrigger -AtStartup
\ = New-ScheduledTaskAction -Execute "C:\hwp-api\venv\Scripts\python.exe" \
  -Argument "C:\hwp-api\app.py" \
  -WorkingDirectory "C:\hwp-api"
Register-ScheduledTask -TaskName "HWP-API-Server" -Trigger \ -Action \ -RunLevel Highest
\\\

## 📁 폴더 구조

\\\
C:\hwp-api\
├── app.py                    # FastAPI 메인 서버
├── convert_hwp.py            # HWP 변환 로직
├── batch_convert.py          # 배치 변환 스크립트
├── test_hwp_api.py           # 단일 파일 테스트
├── requirements.txt          # Python 의존성
├── README.md                 # 이 파일
├── .gitignore                # Git 무시 파일
├── venv/                     # Python 3.11 가상환경
├── scripts/
│   └── FilePathCheckerModule.dll    # 팝업 제거 모듈
├── input/                   # 임시 업로드 (자동 정리)
├── output/                  # 변환된 PDF 저장
└── logs/                    # 로그 파일
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

### 현재 상태 (개발)

- ✅ CORS 모두 허용
- ✅ 인증 없음
- ✅ HTTPS 미적용

### 프로덕션 시 권장 사항

1. **인증 추가**
   \\\python
   # API Key 인증
   api_key = Header(...)
   if api_key != "secret-key":
       raise HTTPException(401)
   \\\

2. **HTTPS 적용**
   - SSL 인증서 설치
   - nginx 리버스 프록시 설정

3. **Rate Limiting**
   \\\python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   \\\


## 📞 문의 및 지원

- **GitHub Issues**: [이슈 제출](https://github.com/gkwog/hwp-to-pdf-api/issues)
- **작성자**: hwan96-ai
- **상태**: 운영 중 ✅

## 📚 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [pywin32 가이드](https://github.com/pywin32/pywin32)
- [한컴 오피스 API](https://www.hancom.com/)



---

**마지막 업데이트**: 2025-11-06 10:26 KST
