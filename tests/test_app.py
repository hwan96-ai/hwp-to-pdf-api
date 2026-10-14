import asyncio
import ctypes
from ctypes import wintypes
from io import BytesIO
import json
import logging
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import httpx
from fastapi import HTTPException, UploadFile

import app as service

logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("app").setLevel(logging.WARNING)


def process_alive(pid: int) -> bool:
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        exit_code = wintypes.DWORD()
        try:
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code))) and exit_code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


class ConversionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.input = self.root / "input"
        self.output = self.root / "output"
        self.input.mkdir()
        self.output.mkdir()
        self.patches = patch.multiple(
            service,
            INPUT_DIR=self.input,
            OUTPUT_DIR=self.output,
            CONVERTER_SCRIPT=Path(__file__).with_name("fake_converter.py"),
            CONVERSION_TIMEOUT_SECONDS=5,
            conversion_lock=asyncio.Lock(),
            conversion_blocked=False,
        )
        self.patches.start()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=service.app), base_url="http://test"
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        self.patches.stop()
        self.temporary.cleanup()

    async def convert(self, filename="document.hwp", **spec):
        return await self.client.post(
            "/convert", files={"file": (filename, json.dumps(spec).encode(), "application/octet-stream")}
        )

    def events(self):
        path = self.root / "events.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    async def wait_event(self, event="start", count=1):
        async with asyncio.timeout(5):
            while len([item for item in self.events() if item["event"] == event]) < count:
                await asyncio.sleep(0.01)

    async def assert_download(self, result, payload):
        response = await self.client.get(result["download_url"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, f"synthetic-pdf:{payload}".encode())
        self.assertIn("attachment", response.headers["content-disposition"])

    async def test_same_filename_sequential_requests_preserve_both_pdfs(self):
        first = (await self.convert(payload="first")).json()
        second = (await self.convert(payload="second")).json()
        self.assertNotEqual(first["job_id"], second["job_id"])
        self.assertNotEqual(first["download_url"], second["download_url"])
        self.assertEqual(first["pdf_filename"], "document.pdf")
        self.assertEqual(len(first["job_id"]), 32)
        await self.assert_download(first, "first")
        await self.assert_download(second, "second")
        self.assertEqual(list(self.input.iterdir()), [])

    async def test_concurrent_requests_are_serialized_and_health_is_responsive(self):
        first_task = asyncio.create_task(self.convert(payload="first", delay=0.4))
        await self.wait_event()
        second_task = asyncio.create_task(self.convert(payload="second", delay=0.1))
        started = time.monotonic()
        health = await asyncio.wait_for(self.client.get("/health"), timeout=0.25)
        self.assertEqual(health.status_code, 200)
        self.assertLess(time.monotonic() - started, 0.25)
        self.assertFalse(first_task.done())
        first, second = await asyncio.gather(first_task, second_task)
        self.assertEqual([event["event"] for event in self.events()], ["start", "end", "start", "end"])
        await self.assert_download(first.json(), "first")
        await self.assert_download(second.json(), "second")

    async def test_batch_duplicate_filenames_and_concurrent_single_are_isolated(self):
        files = [
            ("files", ("document.hwp", json.dumps({"payload": "batch-one", "delay": 0.1}).encode())),
            ("files", ("document.hwp", json.dumps({"payload": "batch-two"}).encode())),
        ]
        batch_task = asyncio.create_task(self.client.post("/convert-batch", files=files))
        await self.wait_event()
        single_task = asyncio.create_task(self.convert(payload="single"))
        batch, single = await asyncio.gather(batch_task, single_task)
        result = batch.json()
        self.assertEqual((result["success_count"], result["failed_count"]), (2, 0))
        rows = result["results"]
        self.assertEqual(len({row["download_url"] for row in [*rows, single.json()]}), 3)
        self.assertEqual(rows[0]["filename"], "document.hwp")
        await self.assert_download(rows[0], "batch-one")
        await self.assert_download(rows[1], "batch-two")
        await self.assert_download(single.json(), "single")

    async def test_batch_mixed_failure_keeps_success_and_continues(self):
        response = await self.client.post("/convert-batch", files=[
            ("files", ("document.hwp", b'{"payload":"before"}')),
            ("files", ("document.hwp", b'{"fail":true,"partial":true}')),
            ("files", ("document.txt", b"unsupported")),
            ("files", ("document.hwp", b'{"payload":"after"}')),
        ])
        result = response.json()
        self.assertEqual((result["success_count"], result["failed_count"]), (2, 2))
        self.assertEqual(result["results"][1]["status"], "failed")
        self.assertIn("7", result["results"][1]["error"])
        self.assertEqual(len(list(self.output.iterdir())), 2)
        await self.assert_download(result["results"][0], "before")
        await self.assert_download(result["results"][3], "after")

    async def test_failure_and_missing_output_remove_only_failed_job(self):
        success = (await self.convert(payload="keep")).json()
        for spec in ({"fail": True, "partial": True}, {"missing": True}):
            response = await self.convert(**spec)
            self.assertEqual(response.status_code, 500)
        self.assertEqual(list(self.input.iterdir()), [])
        self.assertEqual(len(list(self.output.iterdir())), 1)
        await self.assert_download(success, "keep")

    async def test_timeout_kills_and_reaps_worker_and_descendant(self):
        with patch.object(service, "CONVERSION_TIMEOUT_SECONDS", 0.3):
            response = await self.convert(delay=60, partial=True, child=True)
        self.assertEqual(response.status_code, 504)
        pids = [event["pid"] for event in self.events() if "pid" in event]
        self.assertEqual(len(pids), 2)
        self.assertTrue(all(not process_alive(pid) for pid in pids))
        self.assertFalse(service.conversion_lock.locked())
        self.assertFalse(service.conversion_blocked)
        self.assertEqual(list(self.input.iterdir()), [])
        self.assertEqual(list(self.output.iterdir()), [])
        self.assertEqual((await self.convert(payload="after-timeout")).status_code, 200)

    async def test_cancellation_holds_lock_until_tree_is_dead_despite_repeat_cancel(self):
        real_stop = service.stop_worker
        cleanup_started = asyncio.Event()
        allow_cleanup = asyncio.Event()

        async def delayed_cleanup(*arguments):
            cleanup_started.set()
            await allow_cleanup.wait()
            await real_stop(*arguments)

        with patch.object(service, "stop_worker", delayed_cleanup):
            first = asyncio.create_task(self.convert(delay=60, child=True, partial=True))
            await self.wait_event("child")
            first.cancel()
            await asyncio.wait_for(cleanup_started.wait(), 2)
            second = asyncio.create_task(self.convert(payload="next"))
            first.cancel()
            await asyncio.sleep(0.05)
            self.assertTrue(service.conversion_lock.locked())
            self.assertEqual(len([event for event in self.events() if event["event"] == "start"]), 1)
            allow_cleanup.set()
            with self.assertRaises(asyncio.CancelledError):
                await first
            pids = [event["pid"] for event in self.events() if "pid" in event]
            self.assertTrue(all(not process_alive(pid) for pid in pids))
            result = await second
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(list(self.output.iterdir())), 1)
        self.assertEqual(list(self.input.iterdir()), [])

    async def test_cancellation_during_spawn_still_reaps_created_worker(self):
        real_spawn = asyncio.create_subprocess_exec
        created = asyncio.Event()
        processes = []

        async def delayed_spawn(*arguments, **options):
            process = await real_spawn(*arguments, **options)
            if str(arguments[0]) == service.sys.executable:
                processes.append(process)
                created.set()
                await asyncio.sleep(0.1)
            return process

        with patch.object(asyncio, "create_subprocess_exec", delayed_spawn):
            request = asyncio.create_task(self.convert(delay=60))
            await asyncio.wait_for(created.wait(), 3)
            request.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await request
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].returncode)
        self.assertFalse(process_alive(processes[0].pid))
        self.assertEqual(list(self.input.iterdir()), [])
        self.assertEqual(list(self.output.iterdir()), [])

    async def test_cancelled_queued_request_does_not_cancel_active_worker(self):
        first = asyncio.create_task(self.convert(payload="active", delay=0.2))
        await self.wait_event()
        queued = asyncio.create_task(self.convert(payload="queued"))
        await asyncio.sleep(0.02)
        queued.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await queued
        result = await first
        await self.assert_download(result.json(), "active")
        self.assertEqual(len([event for event in self.events() if event["event"] == "start"]), 1)
        self.assertEqual(list(self.input.iterdir()), [])

    async def test_cleanup_failure_blocks_new_workers_and_reports_degraded_health(self):
        real_stop = service.stop_worker

        async def failed_cleanup(*arguments):
            await real_stop(*arguments)
            raise OSError("Synthetic cleanup uncertainty")

        with patch.object(service, "stop_worker", failed_cleanup), patch.object(
            service, "CONVERSION_TIMEOUT_SECONDS", 0.15
        ):
            self.assertEqual((await self.convert(delay=60)).status_code, 504)
        self.assertEqual((await self.convert()).status_code, 503)
        health = (await self.client.get("/health")).json()
        self.assertEqual(health["status"], "degraded")
        self.assertFalse(health["conversions_enabled"])
        self.assertEqual(len([event for event in self.events() if event["event"] == "start"]), 1)

    async def test_com_cleanup_uncertainty_blocks_queued_request_before_lock_release(self):
        real_stop = service.stop_worker
        state_at_cleanup = []

        async def observe_cleanup(*arguments):
            state_at_cleanup.append((service.conversion_blocked, service.conversion_lock.locked()))
            await real_stop(*arguments)

        with patch.object(service, "stop_worker", observe_cleanup):
            first = asyncio.create_task(self.convert(cleanup_uncertain=True, delay=0.1))
            await self.wait_event()
            second = asyncio.create_task(self.convert(payload="must-not-run"))
            first_response, second_response = await asyncio.gather(first, second)
        self.assertEqual(first_response.status_code, 503)
        self.assertEqual(second_response.status_code, 503)
        self.assertEqual(state_at_cleanup, [(True, True)])
        self.assertEqual(len([event for event in self.events() if event["event"] == "start"]), 1)
        self.assertEqual(list(self.input.iterdir()), [])
        self.assertEqual(list(self.output.iterdir()), [])
        self.assertEqual((await self.client.get("/health")).json()["status"], "degraded")

    async def test_cancel_after_parent_exit_reaps_inherited_pipe_descendant(self):
        processes = []
        real_spawn = asyncio.create_subprocess_exec

        async def record_spawn(*arguments, **options):
            process = await real_spawn(*arguments, **options)
            processes.append(process)
            return process

        # Use the base interpreter so the Windows venv launcher's own child-job
        # cleanup cannot hide this exited-parent/inherited-pipe regression.
        with patch.object(service.sys, "executable", service.sys._base_executable), patch.object(
            asyncio, "create_subprocess_exec", record_spawn
        ):
            request = asyncio.create_task(self.convert(child=True, exit_parent=True, partial=True))
            await self.wait_event("parent_exit")
            async with asyncio.timeout(3):
                while processes[0].returncode is None:
                    await asyncio.sleep(0.01)
            self.assertEqual(processes[0].returncode, 7)
            self.assertFalse(request.done())
            child_pid = next(event["pid"] for event in self.events() if event["event"] == "child")
            self.assertTrue(process_alive(child_pid))
            started = time.monotonic()
            request.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await asyncio.wait_for(request, timeout=2)
        self.assertLess(time.monotonic() - started, 2)
        self.assertTrue(all(not process_alive(event["pid"]) for event in self.events() if "pid" in event))
        self.assertFalse(service.conversion_blocked)
        self.assertFalse(service.conversion_lock.locked())
        self.assertEqual(list(self.input.iterdir()), [])
        self.assertEqual(list(self.output.iterdir()), [])
        self.assertEqual((await self.convert()).status_code, 200)

    async def test_timeout_after_parent_exit_reaps_inherited_pipe_descendant(self):
        with patch.object(service.sys, "executable", service.sys._base_executable), patch.object(
            service, "CONVERSION_TIMEOUT_SECONDS", 0.3
        ):
            response = await self.convert(child=True, exit_parent=True)
        self.assertEqual(response.status_code, 504, response.text + str(self.events()))
        self.assertTrue(all(not process_alive(event["pid"]) for event in self.events() if "pid" in event))
        self.assertFalse(service.conversion_blocked)
        self.assertFalse(service.conversion_lock.locked())

    async def test_parent_failure_also_stops_descendant_without_inherited_pipes(self):
        with patch.object(service.sys, "executable", service.sys._base_executable):
            response = await self.convert(child=True, exit_parent=True, inherit_pipes=False)
        self.assertEqual(response.status_code, 500)
        self.assertTrue(all(not process_alive(event["pid"]) for event in self.events() if "pid" in event))
        self.assertFalse(service.conversion_blocked)
        self.assertEqual(list(self.output.iterdir()), [])

    async def test_cancel_during_normal_completion_cleanup_is_preserved(self):
        real_stop = service.stop_worker
        cleanup_started = asyncio.Event()
        allow_cleanup = asyncio.Event()

        async def delayed_cleanup(*arguments):
            cleanup_started.set()
            await allow_cleanup.wait()
            await real_stop(*arguments)

        with patch.object(service, "stop_worker", delayed_cleanup):
            request = asyncio.create_task(self.convert())
            await asyncio.wait_for(cleanup_started.wait(), 3)
            request.cancel()
            await asyncio.sleep(0)
            self.assertTrue(service.conversion_lock.locked())
            allow_cleanup.set()
            with self.assertRaises(asyncio.CancelledError):
                await request
        self.assertFalse(service.conversion_lock.locked())
        self.assertFalse(service.conversion_blocked)
        self.assertEqual(list(self.input.iterdir()), [])
        self.assertEqual(list(self.output.iterdir()), [])

    @unittest.skipUnless(os.name == "nt", "Windows ownership bootstrap")
    async def test_bootstrap_does_not_execute_converter_without_job_ownership(self):
        source = self.input / "synthetic-spec.json"
        source.write_text('{"payload":"must-not-execute"}')
        process = await asyncio.create_subprocess_exec(
            service.sys.executable, str(service.BASE_DIR / "worker_runtime.py"),
            "Local\\HwpConversion-missing-job", str(service.CONVERTER_SCRIPT),
            str(source), str(self.output / "must-not-exist.pdf"),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(process.communicate(), 3)
        self.assertEqual(process.returncode, 3)
        self.assertEqual(self.events(), [])
        self.assertFalse((self.output / "must-not-exist.pdf").exists())

    async def test_download_rejects_path_escape_wrong_job_and_unpublished_pdf(self):
        success = (await self.convert(payload="safe")).json()
        (self.root / "outside.pdf").write_bytes(b"synthetic-outside")
        incomplete_job = "0" * 32
        (self.output / incomplete_job).mkdir()
        (self.output / incomplete_job / "result.pdf").write_bytes(b"incomplete")
        for url in (
            "/download/..%5coutside.pdf",
            "/download/..%2foutside.pdf",
            f"/download/{success['job_id']}/metadata.json",
            f"/download/{success['job_id']}/other.pdf",
            f"/download/{incomplete_job}/document.pdf",
            "/download/not-a-job/document.pdf",
        ):
            self.assertEqual((await self.client.get(url)).status_code, 404, url)
        with self.assertRaises(HTTPException):
            service.contained_path(self.output, "..", "outside.pdf")
        await self.assert_download(success, "safe")

    async def test_symlink_cannot_escape_output_root(self):
        target = self.root / "outside.pdf"
        target.write_bytes(b"synthetic-outside")
        try:
            (self.output / "linked.pdf").symlink_to(target)
        except OSError as error:
            self.skipTest(f"Symlink creation unavailable: {type(error).__name__}")
        self.assertEqual((await self.client.get("/download/linked.pdf")).status_code, 404)

    async def test_legacy_download_and_persisted_job_mapping_remain_usable(self):
        (self.output / "old.pdf").write_bytes(b"synthetic-legacy")
        response = await self.client.get("/download/old.pdf")
        self.assertEqual(response.content, b"synthetic-legacy")
        job_id = "1" * 32
        folder = self.output / job_id
        folder.mkdir()
        (folder / "result.pdf").write_bytes(b"synthetic-persisted")
        (folder / "metadata.json").write_text('{"pdf_filename":"persisted.pdf"}')
        response = await self.client.get(f"/download/{job_id}/persisted.pdf")
        self.assertEqual(response.content, b"synthetic-persisted")
        stats = (await self.client.get("/stats")).json()
        self.assertEqual(stats["total_pdfs"], 2)
        self.assertEqual(stats["files"], [f"{job_id}/persisted.pdf", "old.pdf"])

    async def test_upload_paths_are_discarded_and_unicode_names_round_trip(self):
        response = await self.convert(r"..\outside\샘플 문서.hwp", payload="unicode")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["original_filename"], "샘플 문서.hwp")
        self.assertEqual(result["pdf_filename"], "샘플 문서.pdf")
        await self.assert_download(result, "unicode")
        self.assertFalse((self.root / "outside").exists())

    async def test_unsupported_missing_invalid_and_oversized_uploads(self):
        self.assertEqual((await self.convert("document.txt")).status_code, 400)
        self.assertEqual((await self.convert("invalid:name.hwp")).status_code, 400)
        for filename in (None, ""):
            with self.assertRaises(HTTPException) as raised:
                await service.convert_one(UploadFile(filename=filename, file=BytesIO(b"")))
            self.assertEqual(raised.exception.status_code, 400)
        large = UploadFile(filename="large.hwp", file=BytesIO(b"x" * (50 * 1024 * 1024 + 1)))
        with self.assertRaises(HTTPException) as raised:
            await service.convert_one(large)
        self.assertEqual(raised.exception.status_code, 413)
        self.assertEqual(list(self.input.iterdir()), [])
        self.assertEqual(list(self.output.iterdir()), [])

    async def test_both_subprocess_pipes_are_drained(self):
        self.assertEqual((await self.convert(noisy=True)).status_code, 200)

    async def test_health_and_stats_truthfully_disable_automatic_restart(self):
        for endpoint in ("/health", "/stats"):
            result = (await self.client.get(endpoint)).json()
            self.assertFalse(result["automatic_restart_enabled"])
            self.assertIsNone(result["next_restart_at"])
        health = (await self.client.get("/health")).json()
        self.assertIsNone(health["restart_interval_hours"])
        self.assertEqual(health["conversion_concurrency"], 1)


if __name__ == "__main__":
    unittest.main()
