"""Tests for mxcloudshare.mxutils.mxLogging."""

from __future__ import annotations

import logging

import pytest

from mxcloudshare.mxutils.mxLogging import getLogger, mxLogger

# ---------------------------------------------------------------------------
# Module-level cleanup so tests with distinct logger names don't leak handlers
# between sessions.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_loggers():
    """Remove handlers from any logger a test creates so they don't accumulate."""
    yield
    for name in ("mxlog_tests", "mxlog_print", "mxlog_file", "mxlog_level"):
        logger = logging.getLogger(name)
        for h in logger.handlers[:]:
            logger.removeHandler(h)
            h.close()


# ---------------------------------------------------------------------------
# Helper: capture log records from a named logger without interfering with
# its configured level (unlike caplog.set_level which changes the logger's
# own level).
# ---------------------------------------------------------------------------


@pytest.fixture
def capture_log(mxlog_logger):
    """
    Return a list that receives every record emitted by *mxlog_logger*'s
    underlying ``logging.Logger`` at or above the logger's configured level.
    """
    logger = mxlog_logger.logger
    captured = []

    class _Capture(logging.Handler):
        def emit(self, record):
            captured.append(record)

    handler = _Capture(level=logging.DEBUG)
    logger.addHandler(handler)
    yield captured
    logger.removeHandler(handler)
    handler.close()


@pytest.fixture
def mxlog_logger():
    """Return a fresh mxLogger named ``mxlog_tests``."""
    return getLogger("mxlog_tests")


# ---------------------------------------------------------------------------
# Factory / basic structure
# ---------------------------------------------------------------------------


class TestGetLogger:
    """getLogger() factory and basic mxLogger structure."""

    def test_returns_an_mxlogger_instance(self):
        logger = getLogger("mxlog_tests")
        assert isinstance(logger, mxLogger)

    def test_logger_has_a_console_handler_by_default(self):
        logger = getLogger("mxlog_tests")
        handler_types = {type(h).__name__ for h in logger.logger.handlers}
        assert "mxLogHandler" in handler_types

    def test_logger_has_no_file_handler_without_log_file(self):
        logger = getLogger("mxlog_tests")
        file_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 0

    def test_valid_levels_maps_all_expected_names(self):
        expected = ("DEBUG", "PRINT", "INFO", "WARNING", "ERROR", "CRITICAL")
        for name in expected:
            assert name in mxLogger.valid_levels
        assert mxLogger.valid_levels["PRINT"] == 25


# ---------------------------------------------------------------------------
# Level gating — uses a capture handler so the logger's own level is not
# changed by the test infrastructure.
# ---------------------------------------------------------------------------


class TestLevelGating:
    """Log records at or above the configured level should propagate; lower ones should not."""

    def test_debug_is_silent_when_level_is_info(self, mxlog_logger, capture_log):
        mxlog_logger.setup_mxLogger(log_level="INFO")
        mxlog_logger.logger.debug("should-not-appear")
        assert len(capture_log) == 0

    def test_info_appears_when_level_is_info(self, mxlog_logger, capture_log):
        mxlog_logger.setup_mxLogger(log_level="INFO")
        mxlog_logger.logger.info("visible-info")
        assert len(capture_log) == 1
        assert capture_log[0].getMessage() == "visible-info"

    def test_warning_appears_when_level_is_warning(self, mxlog_logger, capture_log):
        mxlog_logger.setup_mxLogger(log_level="WARNING")
        mxlog_logger.logger.info("should-be-gated")
        mxlog_logger.logger.warning("visible-warning")
        assert len(capture_log) == 1
        assert capture_log[0].getMessage() == "visible-warning"

    def test_print_level_gates_between_info_and_warning(self, mxlog_logger, capture_log):
        """PRINT (25) is above INFO (20) and below WARNING (30)."""
        mxlog_logger.setup_mxLogger(log_level="INFO")
        mxlog_logger.logger.log(mxLogger.PRINT, "print-at-info")
        assert len(capture_log) == 1
        assert capture_log[0].levelno == mxLogger.PRINT
        assert capture_log[0].getMessage() == "print-at-info"

        capture_log.clear()

        mxlog_logger.setup_mxLogger(log_level="WARNING")
        mxlog_logger.logger.log(mxLogger.PRINT, "print-at-warning")
        assert len(capture_log) == 0


# ---------------------------------------------------------------------------
# Custom PRINT level via the .print() convenience method
# ---------------------------------------------------------------------------


class TestPrintMethod:
    """The .print() method sends a record at the PRINT level."""

    def test_print_sends_print_level(self, mxlog_logger, capture_log):
        mxlog_logger.print("hello-from-print")
        assert any(r.levelno == mxLogger.PRINT and r.getMessage() == "hello-from-print" for r in capture_log)


# ---------------------------------------------------------------------------
# File handler behaviour
# ---------------------------------------------------------------------------


class TestFileHandler:
    """File handler is added when log_file is provided."""

    def test_file_handler_added_when_log_file_is_given(self, tmp_path):
        logfile = tmp_path / "test.log"
        logger = getLogger("mxlog_file")
        logger.setup_mxLogger(log_level="INFO", log_file=str(logfile))

        file_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        assert file_handlers[0].baseFilename == str(logfile)

    def test_file_handler_formatter_includes_timestamp_name_level(self, tmp_path):
        logfile = tmp_path / "test.log"
        logger = getLogger("mxlog_file")
        logger.setup_mxLogger(log_level="INFO", log_file=str(logfile))

        file_handler = next(h for h in logger.logger.handlers if isinstance(h, logging.FileHandler))
        fmt = file_handler.formatter
        assert fmt is not None
        assert fmt._fmt == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def test_file_output_contains_expected_message(self, tmp_path):
        logfile = tmp_path / "test.log"
        logger = getLogger("mxlog_file")
        logger.setup_mxLogger(log_level="INFO", log_file=str(logfile))

        logger.logger.info("file-content-check")
        content = logfile.read_text()
        assert "file-content-check" in content

    def test_file_output_respects_log_level(self, tmp_path):
        logfile = tmp_path / "test.log"
        logger = getLogger("mxlog_file")
        logger.setup_mxLogger(log_level="WARNING", log_file=str(logfile))

        logger.logger.debug("should-not-be-in-file")
        logger.logger.warning("should-be-in-file")
        content = logfile.read_text()

        assert "should-not-be-in-file" not in content
        assert "should-be-in-file" in content

    def test_file_handler_mode_defaults_to_append(self, tmp_path):
        logfile = tmp_path / "test.log"
        logger = getLogger("mxlog_file")
        logger.setup_mxLogger(log_level="INFO", log_file=str(logfile))
        logger.logger.info("first-line")
        logger.logger.info("second-line")
        content = logfile.read_text()
        assert content.count("first-line") == 1
        assert content.count("second-line") == 1

    def test_file_mode_w_truncates(self, tmp_path):
        logfile = tmp_path / "test.log"
        logger = getLogger("mxlog_file")
        logger.setup_mxLogger(log_level="INFO", log_file=str(logfile), file_mode="w")
        logger.logger.info("first-line")

        # Re-create logger with w mode — should truncate
        logger2 = getLogger("mxlog_file")
        logger2.setup_mxLogger(log_level="INFO", log_file=str(logfile), file_mode="w")
        logger2.logger.info("second-only")
        content = logfile.read_text()
        assert "first-line" not in content
        assert "second-only" in content


# ---------------------------------------------------------------------------
# setup_mxLogger can reconfigure an existing logger
# ---------------------------------------------------------------------------


class TestSetupMxLogger:
    """Re-configuration via setup_mxLogger."""

    def test_can_change_log_level(self, mxlog_logger, capture_log):
        mxlog_logger.setup_mxLogger(log_level="DEBUG")
        mxlog_logger.logger.debug("debug-after-reconfig")
        assert any(r.getMessage() == "debug-after-reconfig" for r in capture_log)

    def test_can_add_file_handler_later(self, tmp_path):
        logfile = tmp_path / "late.log"
        logger = getLogger("mxlog_tests")
        logger.setup_mxLogger(log_level="INFO")  # no file
        file_handlers_before = [h for h in logger.logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers_before) == 0

        logger.setup_mxLogger(log_level="INFO", log_file=str(logfile))
        file_handlers_after = [h for h in logger.logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers_after) == 1


# ---------------------------------------------------------------------------
# Error / edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases and defensive behaviour."""

    def test_invalid_level_name_falls_back_to_info(self):
        logger = getLogger("mxlog_tests")
        logger.setup_mxLogger(log_level="NOT_A_REAL_LEVEL")
        assert logger.log_level == logging.INFO

    def test_logger_name_is_preserved(self):
        logger = getLogger("mxlog_tests")
        assert logger.logger.name == "mxlog_tests"

    def test_getLogger_without_name_returns_root_logger(self):
        logger = getLogger()
        assert logger.logger.name == "root"

    def test_lowercase_level_name_is_handled(self):
        logger = getLogger("mxlog_tests")
        logger.setup_mxLogger(log_level="debug")
        assert logger.log_level == logging.DEBUG