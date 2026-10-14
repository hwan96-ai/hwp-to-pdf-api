import tempfile
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import convert_hwp
from worker_runtime import COM_CLEANUP_UNCERTAIN_EXIT_CODE


class HancomCleanupTests(unittest.TestCase):
    """COM mocks verify control flow only; these are not Hancom integration tests."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.input = Path(self.temporary.name) / "synthetic.hwp"
        self.input.write_bytes(b"synthetic-input")
        self.output = self.input.with_suffix(".pdf")
        self.hwp = MagicMock()
        self.hwp.Open.return_value = True
        self.hwp.HAction.Execute.return_value = True

    def tearDown(self):
        self.temporary.cleanup()

    def convert(self):
        with patch.object(convert_hwp, "register_dll"), patch.object(
            convert_hwp.win32com.client, "DispatchEx", return_value=self.hwp
        ), patch("builtins.print"):
            return convert_hwp.convert_hwp_to_pdf(str(self.input), str(self.output))

    def test_success_closes_automation_object(self):
        self.assertTrue(self.convert())
        self.hwp.Quit.assert_called_once()

    def test_open_failure_closes_automation_object(self):
        self.hwp.Open.return_value = False
        self.assertFalse(self.convert())
        self.hwp.Quit.assert_called_once()
        self.hwp.HAction.Execute.assert_not_called()

    def test_save_failure_closes_automation_object(self):
        self.hwp.HAction.Execute.return_value = False
        self.assertFalse(self.convert())
        self.hwp.Quit.assert_called_once()

    def test_exception_closes_automation_object(self):
        self.hwp.Open.side_effect = RuntimeError("Synthetic COM failure")
        self.assertFalse(self.convert())
        self.hwp.Quit.assert_called_once()

    def test_quit_failure_raises_cleanup_uncertainty_instead_of_success(self):
        self.hwp.Quit.side_effect = RuntimeError("Synthetic Quit failure")
        with self.assertRaises(convert_hwp.HancomCleanupError):
            self.convert()
        self.hwp.Quit.assert_called_once()

    def test_cli_uses_distinct_exit_status_for_quit_failure(self):
        self.hwp.Quit.side_effect = RuntimeError("Synthetic Quit failure")
        with patch.object(convert_hwp, "register_dll"), patch.object(
            convert_hwp.win32com.client, "DispatchEx", return_value=self.hwp
        ), patch("builtins.print"):
            status = convert_hwp.main([str(self.input), str(self.output)])
        self.assertEqual(status, COM_CLEANUP_UNCERTAIN_EXIT_CODE)
        self.hwp.Quit.assert_called_once()
