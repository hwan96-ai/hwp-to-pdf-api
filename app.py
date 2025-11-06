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

@app.post("/convert")
async def convert_hwp_to_pdf(file: UploadFile = File(...)):
    """HWP/HWPX 파일을 PDF로 변환"""
    
    job_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        # 파일 확장자 확인
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.hwp', '.hwpx']:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 형식: {file_ext}"
            )
        
        # 파일 크기 확인
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        if file_size_mb > 50:
            raise HTTPException(status_code=413, detail="파일 크기 초과")
        
        # 입력 파일 저장 (임시)
        input_filename = f"{job_id}_{file.filename}"
        input_path = INPUT_DIR / input_filename
        
        with open(input_path, "wb") as f:
            f.write(content)
        
        logger.info(f"[{job_id}] 파일 저장: {file.filename}")
        
        # 출력 파일명 = 원본 파일명 (확장자만 PDF로)
        output_filename = f"{Path(file.filename).stem}.pdf"
        output_path = OUTPUT_DIR / output_filename
        
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
    return {
        "status": "healthy",
        "service": "HWP-to-PDF Converter API",
        "version": "1.0.0",
        "base_dir": str(BASE_DIR),
        "output_dir": str(OUTPUT_DIR)
    }

@app.get("/stats")
async def get_stats():
    """통계"""
    pdf_files = list(OUTPUT_DIR.glob("*.pdf"))
    total_size_mb = sum(f.stat().st_size for f in pdf_files) / (1024 * 1024)
    
    return {
        "total_pdfs": len(pdf_files),
        "total_size_mb": round(total_size_mb, 2),
        "output_dir": str(OUTPUT_DIR),
        "files": [f.name for f in pdf_files]
    }

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("🚀 HWP to PDF Converter API 시작")
    logger.info("=" * 70)
    logger.info(f"📁 기본 디렉토리: {BASE_DIR}")
    logger.info(f"📡 API: http://0.0.0.0:8000")
    logger.info(f"📖 문서: http://0.0.0.0:8000/docs")
    logger.info("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
