import asyncio
from datetime import datetime
import json
import logging
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import signal
import sys
import time
from urllib.parse import quote
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

from worker_runtime import COM_CLEANUP_UNCERTAIN_EXIT_CODE, WindowsJob


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_VERSION = "1.5.0"
app = FastAPI(
    title="HWP to PDF Converter API",
    description="Windows에서 HWP/HWPX 파일을 PDF로 변환",
    version=API_VERSION,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
CONVERTER_SCRIPT = BASE_DIR / "convert_hwp.py"
CONVERSION_TIMEOUT_SECONDS = 120
SUPPORTED_EXTENSIONS = {".hwp", ".hwpx", ".hwt", ".hwtx"}
SERVER_START_TIME = datetime.now()

# Run one Uvicorn worker: this lock serializes Hancom COM use within that worker.
conversion_lock = asyncio.Lock()
conversion_blocked = False

for directory in (INPUT_DIR, OUTPUT_DIR, LOGS_DIR):
    directory.mkdir(exist_ok=True)


def upload_filename(filename: str | None) -> str:
    """Discard client-side paths; the name is used only for presentation."""
    name = PureWindowsPath(filename or "").name
    if not name or name in {".", ".."} or re.search(r'[<>:"|?*\x00-\x1f]', name):
        raise HTTPException(status_code=400, detail="올바르지 않은 파일명")
    return name


def contained_path(root: Path, *parts: str) -> Path:
    """Reject path and symlink escapes before reading any download data."""
    path = root.joinpath(*parts).resolve()
    if not path.is_relative_to(root.resolve()):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    return path


async def finish_cleanup(task: asyncio.Task) -> None:
    """Keep the serialization lock until cleanup finishes, even on repeat cancel."""
    cancelled = False
    while True:
        try:
            await asyncio.shield(task)
            break
        except asyncio.CancelledError:
            cancelled = True
            if task.cancelled():
                raise
    if cancelled:
        raise asyncio.CancelledError


async def stop_worker(
    spawn_task: asyncio.Task,
    communication_task: asyncio.Task | None,
    worker_job: WindowsJob | None = None,
) -> None:
    """Stop owned descendants even after the converter parent has exited."""
    try:
        process = await spawn_task
    except OSError:
        return  # Process creation failed, so there is no child to reap.

    if worker_job is not None:
        worker_job.terminate()
    elif os.name != "nt":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    # Also cover cancellation before the bootstrap has joined its job. It cannot
    # run converter code unless joining succeeds, even if the job is closed early.
    if process.returncode is None:
        try:
            process.kill()
        except ProcessLookupError:
            pass

    if communication_task is None:
        communication_task = asyncio.create_task(process.communicate())
    await asyncio.wait_for(asyncio.shield(communication_task), timeout=10)
    await process.wait()
    if worker_job is not None:
        async with asyncio.timeout(10):
            while worker_job.active_processes():
                await asyncio.sleep(0.01)


async def run_converter(input_path: Path, output_path: Path) -> int:
    global conversion_blocked
    async with conversion_lock:
        if conversion_blocked:
            raise HTTPException(status_code=503, detail="변환 프로세스 정리 상태 확인 필요")
        worker_job = WindowsJob() if os.name == "nt" else None
        command = [sys.executable, str(CONVERTER_SCRIPT), str(input_path), str(output_path)]
        if worker_job is not None:
            command = [
                sys.executable, str(BASE_DIR / "worker_runtime.py"), worker_job.name,
                str(CONVERTER_SCRIPT), str(input_path), str(output_path),
            ]
        options = {} if os.name == "nt" else {"start_new_session": True}
        # Shield spawning so cancellation cannot lose a just-created child.
        spawn_task = asyncio.create_task(asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **options,
        ))
        communication_task = None
        pending_error = False
        try:
            process = await asyncio.shield(spawn_task)
            communication_task = asyncio.create_task(process.communicate())
            # Keep draining both pipes during cancellation/timeout cleanup.
            await asyncio.wait_for(
                asyncio.shield(communication_task), timeout=CONVERSION_TIMEOUT_SECONDS
            )
            if process.returncode == COM_CLEANUP_UNCERTAIN_EXIT_CODE:
                # Record this before cleanup or releasing the serialization lock.
                conversion_blocked = True
                raise HTTPException(status_code=503, detail="한컴 종료 상태 확인 필요")
            return process.returncode
        except BaseException:
            pending_error = True
            raise
        finally:
            try:
                await finish_cleanup(asyncio.create_task(
                    stop_worker(spawn_task, communication_task, worker_job)
                ))
            except Exception:
                # Do not allow a second COM worker when termination is uncertain.
                conversion_blocked = True
                logger.error("Worker cleanup failed; further conversions disabled")
                if not pending_error:
                    raise HTTPException(status_code=503, detail="변환 프로세스 정리 상태 확인 필요") from None
            finally:
                # communicate() can remain pending on inherited child pipes after
                # the parent has already exited with known COM cleanup uncertainty.
                if spawn_task.done() and not spawn_task.cancelled():
                    try:
                        if spawn_task.result().returncode == COM_CLEANUP_UNCERTAIN_EXIT_CODE:
                            conversion_blocked = True
                    except OSError:
                        pass
                if worker_job is not None:
                    worker_job.close()


async def convert_one(file: UploadFile) -> dict:
    name = upload_filename(file.filename)
    extension = Path(name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 형식: {extension}")
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > 50:
        raise HTTPException(status_code=413, detail="파일 크기 초과")

    job_id = uuid.uuid4().hex
    started = time.monotonic()
    input_directory = contained_path(INPUT_DIR, job_id)
    output_directory = contained_path(OUTPUT_DIR, job_id)
    input_path = input_directory / f"source{extension}"
    output_path = output_directory / "result.pdf"
    pdf_filename = f"{Path(name).stem}.pdf"
    succeeded = False
    input_created = False
    output_created = False
    try:
        input_directory.mkdir()
        input_created = True
        output_directory.mkdir()
        output_created = True
        input_path.write_bytes(content)
        logger.info("[%s] Conversion started", job_id)
        returncode = await run_converter(input_path, output_path)
        if returncode != 0:
            # Worker output may contain document names or local paths. Keep it private.
            raise HTTPException(status_code=500, detail=f"변환 실패 (종료 코드 {returncode})")
        if not output_path.is_file():
            raise HTTPException(status_code=500, detail="PDF 생성 실패")
        output_size_mb = output_path.stat().st_size / (1024 * 1024)
        # Durable mapping: downloads keep working after an ordinary server restart.
        (output_directory / "metadata.json").write_text(
            json.dumps({"pdf_filename": pdf_filename}, ensure_ascii=False),
            encoding="utf-8",
        )
        result = {
            "status": "success",
            "job_id": job_id,
            "original_filename": name,
            "original_size_mb": round(file_size_mb, 2),
            "pdf_filename": pdf_filename,
            "pdf_size_mb": round(output_size_mb, 2),
            "conversion_time_seconds": round(time.monotonic() - started, 2),
            "download_url": f"/download/{job_id}/{quote(pdf_filename, safe='')}",
        }
        succeeded = True
        logger.info("[%s] Conversion completed", job_id)
        return result
    except TimeoutError:
        raise HTTPException(status_code=504, detail="변환 시간 초과") from None
    except HTTPException:
        raise
    except Exception as error:
        logger.error("[%s] Conversion error: %s", job_id, type(error).__name__)
        raise HTTPException(status_code=500, detail="변환 중 오류가 발생했습니다") from None
    finally:
        # Only this job's directories are removed; successful PDFs remain downloadable.
        if input_created:
            shutil.rmtree(input_directory, ignore_errors=True)
        if output_created and not succeeded:
            shutil.rmtree(output_directory, ignore_errors=True)


@app.post("/convert")
async def convert_hwp_to_pdf(file: UploadFile = File(...)):
    """HWP/HWPX 파일을 PDF로 변환 (단일 파일)."""
    return await convert_one(file)


@app.post("/convert-batch")
async def convert_batch(files: list[UploadFile] = File(...)):
    """다중 파일 변환; 각 파일은 단일 변환과 같은 격리 규칙을 사용합니다."""
    batch_id = uuid.uuid4().hex
    results = []
    started = time.monotonic()
    for file in files:
        try:
            result = await convert_one(file)
            result["filename"] = result.pop("original_filename")
            results.append(result)
        except HTTPException as error:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": error.detail,
            })
    success_count = sum(result["status"] == "success" for result in results)
    return {
        "status": "completed",
        "batch_id": batch_id,
        "total_files": len(files),
        "success_count": success_count,
        "failed_count": len(files) - success_count,
        "total_time_seconds": round(time.monotonic() - started, 2),
        "results": results,
    }


def job_download(job_id: str) -> tuple[Path, str]:
    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    path = contained_path(OUTPUT_DIR, job_id, "result.pdf")
    metadata_path = contained_path(OUTPUT_DIR, job_id, "metadata.json")
    try:
        name = json.loads(metadata_path.read_text(encoding="utf-8"))["pdf_filename"]
        if upload_filename(name) != name or Path(name).suffix != ".pdf" or not path.is_file():
            raise ValueError("Invalid download mapping")
    except (OSError, ValueError, KeyError, TypeError, HTTPException):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다") from None
    return path, name


@app.get("/download/{job_id}/{filename}")
async def download_job_pdf(job_id: str, filename: str):
    """Download only the completed PDF that belongs to this job."""
    path, display_name = job_download(job_id)
    if filename != display_name:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    return FileResponse(path, media_type="application/pdf", filename=display_name)


@app.get("/download/{filename}")
async def download_pdf(filename: str):
    """Compatibility for existing flat PDFs; new jobs use scoped URLs."""
    try:
        valid_name = upload_filename(filename) == filename and Path(filename).suffix == ".pdf"
    except HTTPException:
        valid_name = False
    if not valid_name:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    path = contained_path(OUTPUT_DIR, filename)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    return FileResponse(path, media_type="application/pdf", filename=filename)


@app.get("/health")
async def health_check():
    """Process liveness and configuration; this is not a Hancom integration probe."""
    return {
        "status": "degraded" if conversion_blocked else "healthy",
        "service": "HWP-to-PDF Converter API",
        "version": API_VERSION,
        "base_dir": str(BASE_DIR),
        "output_dir": str(OUTPUT_DIR),
        "started_at": SERVER_START_TIME.isoformat(),
        "uptime_hours": round((datetime.now() - SERVER_START_TIME).total_seconds() / 3600, 2),
        "automatic_restart_enabled": False,
        "next_restart_at": None,
        "restart_interval_hours": None,
        "conversion_concurrency": 1,
        "conversions_enabled": not conversion_blocked,
    }


@app.get("/stats")
async def get_stats():
    pdfs = []
    for candidate in OUTPUT_DIR.iterdir():
        try:
            if candidate.is_dir():
                path, name = job_download(candidate.name)
                pdfs.append((path, f"{candidate.name}/{name}"))
            elif candidate.suffix == ".pdf":
                path = contained_path(OUTPUT_DIR, candidate.name)
                if path.is_file() and upload_filename(candidate.name) == candidate.name:
                    pdfs.append((path, candidate.name))
        except HTTPException:
            continue
    return {
        "total_pdfs": len(pdfs),
        "total_size_mb": round(sum(path.stat().st_size for path, _ in pdfs) / (1024 * 1024), 2),
        "output_dir": str(OUTPUT_DIR),
        "files": sorted(name for _, name in pdfs),
        "uptime_hours": round((datetime.now() - SERVER_START_TIME).total_seconds() / 3600, 2),
        "automatic_restart_enabled": False,
        "next_restart_at": None,
    }


if __name__ == "__main__":
    logger.info("HWP to PDF API starting; conversion concurrency=1; automatic restart disabled")
    uvicorn.run(app, host="0.0.0.0", port=9000, log_level="info")
