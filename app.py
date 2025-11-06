from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import subprocess
import os
from pathlib import Path
import uuid
import time
import logging
from datetime import datetime, timedelta
import threading
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HWP to PDF Converter API",
    description="EC2 Windows에서 HWP/HWPX 파일을 PDF로 변환",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

for directory in [INPUT_DIR, OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)
    logger.info(f"✅ 폴더 확인: {directory}")

# 서버 시작 시간
SERVER_START_TIME = datetime.now()
RESTART_INTERVAL_HOURS = 24

def auto_restart_thread():
    """24시간마다 서버 자동 재시작"""
    global SERVER_START_TIME
    
    while True:
        now = datetime.now()
        elapsed_seconds = (now - SERVER_START_TIME).total_seconds()
        elapsed_hours = elapsed_seconds / 3600
        
        if elapsed_hours >= RESTART_INTERVAL_HOURS:
            logger.warning("=" * 70)
            logger.warning(f"⏰ {RESTART_INTERVAL_HOURS}시간 경과 - 서버 자동 재시작")
            logger.warning("=" * 70)
            
            # 프로세스 종료
            sys.exit(0)
        
        # 1시간마다 확인
        time.sleep(3600)

@app.post("/convert")
async def convert_hwp_to_pdf(file: UploadFile = File(...)):
    """HWP/HWPX 파일을 PDF로 변환 (단일 파일)"""
    
    job_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        # 파일 확장자 확인
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.hwp', '.hwpx', '.hwt', '.hwtx']:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 형식: {file_ext}"
            )
        
        # 파일 크기 확인
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        if file_size_mb > 50:
            raise HTTPException(status_code=413, detail="파일 크기 초과")
        
        # 입력 파일 저장
        input_filename = f"{job_id}_{file.filename}"
        input_path = INPUT_DIR / input_filename
        
        with open(input_path, "wb") as f:
            f.write(content)
        
        logger.info(f"[{job_id}] 파일 저장: {file.filename}")
        
        # 출력 파일명
        output_filename = f"{Path(file.filename).stem}.pdf"
        output_path = OUTPUT_DIR / output_filename
        
        # 변환 실행
        logger.info(f"[{job_id}] 변환 시작...")
        
        result = subprocess.run(
            ["python", str(BASE_DIR / "convert_hwp.py"), str(input_path), str(output_path)],
            capture_output=True,
            timeout=120,
            text=True
        )
        
        elapsed = time.time() - start_time
        
        # 입력 파일 삭제
        try:
            input_path.unlink()
        except:
            pass
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            logger.error(f"[{job_id}] 변환 실패: {error_msg}")
            raise HTTPException(status_code=500, detail=f"변환 실패: {error_msg[:100]}")
        
        if not output_path.exists():
            logger.error(f"[{job_id}] 출력 파일 없음")
            raise HTTPException(status_code=500, detail="PDF 생성 실패")
        
        output_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"[{job_id}] 변환 완료 ({output_size_mb:.2f}MB, {elapsed:.2f}초)")
        
        return {
            "status": "success",
            "job_id": job_id,
            "original_filename": file.filename,
            "original_size_mb": round(file_size_mb, 2),
            "pdf_filename": output_filename,
            "pdf_size_mb": round(output_size_mb, 2),
            "conversion_time_seconds": round(elapsed, 2),
            "download_url": f"/download/{output_filename}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{job_id}] 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"오류: {str(e)[:100]}")

@app.post("/convert-batch")
async def convert_batch(files: list[UploadFile] = File(...)):
    """다중 파일 변환 (배치)"""
    
    batch_id = str(uuid.uuid4())[:8]
    results = []
    total_start = time.time()
    
    logger.info(f"[배치-{batch_id}] {len(files)}개 파일 변환 시작")
    
    for idx, file in enumerate(files, 1):
        job_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        try:
            # 파일 확장자 확인
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ['.hwp', '.hwpx', '.hwt', '.hwtx']:
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": f"지원하지 않는 형식: {file_ext}"
                })
                continue
            
            # 파일 크기 확인
            content = await file.read()
            file_size_mb = len(content) / (1024 * 1024)
            
            if file_size_mb > 50:
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": "파일 크기 초과"
                })
                continue
            
            # 입력 파일 저장
            input_filename = f"{job_id}_{file.filename}"
            input_path = INPUT_DIR / input_filename
            
            with open(input_path, "wb") as f:
                f.write(content)
            
            logger.info(f"[배치-{batch_id}] [{idx}/{len(files)}] {file.filename} 저장")
            
            # 출력 파일명
            output_filename = f"{Path(file.filename).stem}.pdf"
            output_path = OUTPUT_DIR / output_filename
            
            # 변환 실행
            result = subprocess.run(
                ["python", str(BASE_DIR / "convert_hwp.py"), str(input_path), str(output_path)],
                capture_output=True,
                timeout=120,
                text=True
            )
            
            elapsed = time.time() - start_time
            
            # 입력 파일 삭제
            try:
                input_path.unlink()
            except:
                pass
            
            if result.returncode == 0 and output_path.exists():
                output_size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"[배치-{batch_id}] [{idx}/{len(files)}] {file.filename} 완료 ({elapsed:.2f}초)")
                
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "pdf_filename": output_filename,
                    "original_size_mb": round(file_size_mb, 2),
                    "pdf_size_mb": round(output_size_mb, 2),
                    "conversion_time_seconds": round(elapsed, 2),
                    "download_url": f"/download/{output_filename}"
                })
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"[배치-{batch_id}] [{idx}/{len(files)}] {file.filename} 실패")
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": error_msg[:100]
                })
        
        except Exception as e:
            logger.error(f"[배치-{batch_id}] [{idx}/{len(files)}] {file.filename} 오류: {str(e)}")
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)[:100]
            })
    
    total_elapsed = time.time() - total_start
    success_count = sum(1 for r in results if r["status"] == "success")
    
    logger.info(f"[배치-{batch_id}] 완료: {success_count}/{len(files)} 성공 ({total_elapsed:.2f}초)")
    
    return {
        "status": "completed",
        "batch_id": batch_id,
        "total_files": len(files),
        "success_count": success_count,
        "failed_count": len(files) - success_count,
        "total_time_seconds": round(total_elapsed, 2),
        "results": results
    }

@app.get("/download/{filename}")
async def download_pdf(filename: str):
    """변환된 PDF 다운로드"""
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        logger.warning(f"파일 찾기 실패: {filename}")
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    
    logger.info(f"PDF 다운로드: {filename}")
    return FileResponse(str(file_path), media_type="application/pdf", filename=filename)

@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    now = datetime.now()
    uptime_seconds = (now - SERVER_START_TIME).total_seconds()
    uptime_hours = uptime_seconds / 3600
    next_restart = SERVER_START_TIME + timedelta(hours=RESTART_INTERVAL_HOURS)
    
    return {
        "status": "healthy",
        "service": "HWP-to-PDF Converter API",
        "version": "1.0.0",
        "base_dir": str(BASE_DIR),
        "output_dir": str(OUTPUT_DIR),
        "started_at": SERVER_START_TIME.isoformat(),
        "uptime_hours": round(uptime_hours, 2),
        "next_restart_at": next_restart.isoformat(),
        "restart_interval_hours": RESTART_INTERVAL_HOURS
    }

@app.get("/stats")
async def get_stats():
    """통계"""
    pdf_files = list(OUTPUT_DIR.glob("*.pdf"))
    total_size_mb = sum(f.stat().st_size for f in pdf_files) / (1024 * 1024)
    
    now = datetime.now()
    uptime_hours = (now - SERVER_START_TIME).total_seconds() / 3600
    next_restart = SERVER_START_TIME + timedelta(hours=RESTART_INTERVAL_HOURS)
    
    return {
        "total_pdfs": len(pdf_files),
        "total_size_mb": round(total_size_mb, 2),
        "output_dir": str(OUTPUT_DIR),
        "files": [f.name for f in pdf_files],
        "uptime_hours": round(uptime_hours, 2),
        "next_restart_at": next_restart.isoformat()
    }

if __name__ == "__main__":
    # 자동 재시작 스레드 시작
    restart_thread = threading.Thread(target=auto_restart_thread, daemon=True)
    restart_thread.start()
    
    logger.info("=" * 70)
    logger.info("🚀 HWP to PDF Converter API 시작")
    logger.info("=" * 70)
    logger.info(f"📁 기본 디렉토리: {BASE_DIR}")
    logger.info(f"📡 API: http://0.0.0.0:8000")
    logger.info(f"📖 문서: http://0.0.0.0:8000/docs")
    logger.info(f"📌 단일 파일: POST /convert")
    logger.info(f"📌 다중 파일: POST /convert-batch")
    logger.info(f"⏰ 자동 재시작: {RESTART_INTERVAL_HOURS}시간마다")
    logger.info(f"⏰ 예정 재시작: {(SERVER_START_TIME + timedelta(hours=RESTART_INTERVAL_HOURS)).strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
