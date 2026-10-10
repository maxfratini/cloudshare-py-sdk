"""Tests for mxcloudshare.mxutils.mxLogging.

These check what a user actually sees (stderr, log file) through the logger objects the
CLI uses, not the handlers' internals: the previous implementation passed tests that
poked at an inner logger while ``mxlogger.info(...)`` printed nothing at all.
"""

from __future__ import annotations

import logging

import pytest

from mxcloudshare.mxutils import mxLogging
from mxcloudshare.mxutils.mxLogging import PRINT, getLogger, setup_mxLogger, valid_levels


@pytest.fixture(autouse=True)
def _reset_package_logger():
    """Give every test a pristine "mxcloudshare" logger and restore it afterwards."""
    logger = logging.getLogger(mxLogging.PACKAGE_LOGGER)
    saved = (logger.handlers[:], logger.level, logger.propagate)
    yield
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    logger.handlers[:], logger.level, logger.propagate = saved[0], saved[1], saved[2]
    # Child loggers that a test configured directly must not leak their level into the next test.
    sample = logging.getLogger("mxcloudshare.sample")
    sample.setLevel(logging.NOTSET)
    sample.propagate = True


class TestGetLogger:
    def test_returns_a_plain_stdlib_logger(self):
        assert type(getLogger("mxcloudshare.sample")) is logging.Logger

    def test_without_name_returns_the_package_logger(self):
        assert getLogger().name == "mxcloudshare"

    def test_valid_levels_maps_all_expected_names(self):
        for name in ("DEBUG", "PRINT", "INFO", "WARNING", "ERROR", "CRITICAL"):
            assert name in valid_levels
        assert valid_levels["PRINT"] == 25 == PRINT

    def test_print_level_has_a_name(self):
        assert logging.getLevelName(PRINT) == "PRINT"


class TestConsoleOutput:
    """Every call on a logger obtained from getLogger() must reach stderr when the level allows it."""

    def test_all_levels_reach_stderr_at_debug(self, capsys):
        setup_mxLogger(log_level="DEBUG")
        log = getLogger("mxcloudshare.sample")
        log.debug("m-debug")
        log.info("m-info")
        log.print("m-print")
        log.warning("m-warning")
        log.error("m-error")

        err = capsys.readouterr().err
        for level in ("debug", "info", "print", "warning", "error"):
            assert f"m-{level}" in err

    def test_stdout_stays_clean(self, capsys):
        setup_mxLogger(log_level="DEBUG")
        getLogger("mxcloudshare.sample").warning("to-stderr")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "to-stderr" in captured.err

    @pytest.mark.parametrize(
        "level, hidden, shown",
        [
            ("PRINT", ["m-debug", "m-info"], ["m-print", "m-warning"]),
            ("INFO", ["m-debug"], ["m-info", "m-print", "m-warning"]),
            ("WARNING", ["m-debug", "m-info", "m-print"], ["m-warning"]),
        ],
    )
    def test_level_gating(self, capsys, level, hidden, shown):
        setup_mxLogger(log_level=level)
        log = getLogger("mxcloudshare.sample")
        log.debug("m-debug")
        log.info("m-info")
        log.print("m-print")
        log.warning("m-warning")

        err = capsys.readouterr().err
        for text in hidden:
            assert text not in err
        for text in shown:
            assert text in err

    def test_print_is_bare_and_others_are_prefixed(self, capsys):
        setup_mxLogger(log_level="DEBUG")
        log = getLogger("mxcloudshare.sample")
        log.print("hello")
        log.warning("careful")
        lines = capsys.readouterr().err.splitlines()
        assert lines == ["hello", "WARNING: careful"]

    def test_markup_is_interpreted_only_for_print(self, capsys):
        setup_mxLogger(log_level="DEBUG")
        log = getLogger("mxcloudshare.sample")
        log.print("[bold]styled[/bold]")
        log.info("ids look like [EN123] or [bold]this[/bold]")
        lines = capsys.readouterr().err.splitlines()
        assert lines[0] == "styled"
        assert lines[1] == "INFO: ids look like [EN123] or [bold]this[/bold]"

    def test_long_lines_are_not_wrapped(self, capsys):
        setup_mxLogger(log_level="INFO")
        long = "x" * 300
        getLogger("mxcloudshare.sample").info(long)
        assert long in capsys.readouterr().err

    def test_lines_have_no_trailing_padding(self, capsys):
        setup_mxLogger(log_level="INFO")
        getLogger("mxcloudshare.sample").info("short")
        assert capsys.readouterr().err == "INFO: short\n"

    def test_exception_text_is_included(self, capsys):
        setup_mxLogger(log_level="INFO")
        try:
            raise ValueError("boom")
        except ValueError:
            getLogger("mxcloudshare.sample").exception("failed")
        err = capsys.readouterr().err
        assert "failed" in err
        assert "ValueError: boom" in err

    def test_other_modules_under_the_package_share_the_handlers(self, capsys):
        """requester.py uses logging.getLogger(__name__) directly."""
        setup_mxLogger(log_level="INFO")
        logging.getLogger("mxcloudshare.cloudshare.requester").info("from-requester")
        assert "from-requester" in capsys.readouterr().err


class TestPrintMethod:
    def test_print_emits_a_record_at_the_print_level(self, caplog):
        logger = getLogger("mxcloudshare.sample")
        logger.setLevel(logging.DEBUG)
        logger.propagate = True
        with caplog.at_level(logging.DEBUG, logger="mxcloudshare.sample"):
            logger.print("hello-from-print")
        assert [(r.levelno, r.getMessage()) for r in caplog.records] == [(PRINT, "hello-from-print")]

    def test_print_supports_percent_args(self, capsys):
        setup_mxLogger(log_level="PRINT")
        getLogger("mxcloudshare.sample").print("value=%s", 42)
        assert "value=42" in capsys.readouterr().err

    def test_print_reports_the_calling_location(self, caplog):
        logger = getLogger("mxcloudshare.sample")
        logger.setLevel(logging.DEBUG)
        logger.propagate = True
        with caplog.at_level(logging.DEBUG, logger="mxcloudshare.sample"):
            logger.print("where")
        assert caplog.records[0].funcName == "test_print_reports_the_calling_location"


class TestFileHandler:
    def test_no_file_handler_without_log_file(self):
        logger = setup_mxLogger(log_level="INFO")
        assert not [h for h in logger.handlers if isinstance(h, logging.FileHandler)]

    def test_file_receives_every_level_allowed_by_the_level(self, tmp_path):
        logfile = tmp_path / "t.log"
        setup_mxLogger(log_level="INFO", log_file=str(logfile))
        log = getLogger("mxcloudshare.sample")
        log.debug("not-in-file")
        log.info("info-in-file")
        log.print("print-in-file")
        log.warning("warning-in-file")

        content = logfile.read_text()
        assert "not-in-file" not in content
        for text in ("info-in-file", "print-in-file", "warning-in-file"):
            assert text in content

    def test_file_lines_carry_timestamp_name_and_level(self, tmp_path):
        logfile = tmp_path / "t.log"
        setup_mxLogger(log_level="INFO", log_file=str(logfile))
        getLogger("mxcloudshare.sample").warning("check-format")
        line = logfile.read_text().strip()
        assert " - mxcloudshare.sample - WARNING - check-format" in line

    def test_file_keeps_markup_text_verbatim(self, tmp_path):
        logfile = tmp_path / "t.log"
        setup_mxLogger(log_level="PRINT", log_file=str(logfile))
        getLogger("mxcloudshare.sample").print("[bold]raw[/bold]")
        assert "[bold]raw[/bold]" in logfile.read_text()

    def test_default_mode_appends(self, tmp_path):
        logfile = tmp_path / "t.log"
        logfile.write_text("existing\n")
        setup_mxLogger(log_level="INFO", log_file=str(logfile))
        getLogger("mxcloudshare.sample").info("new-line")
        content = logfile.read_text()
        assert "existing" in content and "new-line" in content

    def test_mode_w_truncates(self, tmp_path):
        logfile = tmp_path / "t.log"
        logfile.write_text("existing\n")
        setup_mxLogger(log_level="INFO", log_file=str(logfile), file_mode="w")
        getLogger("mxcloudshare.sample").info("new-line")
        content = logfile.read_text()
        assert "existing" not in content and "new-line" in content


class TestSetupIsIdempotent:
    """initializeApp() runs for every command, so setup must not stack handlers."""

    def test_repeated_setup_does_not_duplicate_output(self, capsys):
        for _ in range(3):
            setup_mxLogger(log_level="INFO")
        getLogger("mxcloudshare.sample").info("once")
        assert capsys.readouterr().err.count("once") == 1

    def test_second_setup_replaces_the_file_handler(self, tmp_path):
        first, second = tmp_path / "a.log", tmp_path / "b.log"
        setup_mxLogger(log_level="INFO", log_file=str(first))
        logger = setup_mxLogger(log_level="INFO", log_file=str(second))
        getLogger("mxcloudshare.sample").info("goes-to-second")
        assert [h.baseFilename for h in logger.handlers if isinstance(h, logging.FileHandler)] == [str(second)]
        assert "goes-to-second" in second.read_text()
        assert not first.exists() or "goes-to-second" not in first.read_text()

    def test_setup_can_drop_the_file_handler(self, tmp_path):
        setup_mxLogger(log_level="INFO", log_file=str(tmp_path / "a.log"))
        logger = setup_mxLogger(log_level="INFO")
        assert not [h for h in logger.handlers if isinstance(h, logging.FileHandler)]

    def test_handlers_added_by_others_are_left_alone(self):
        logger = logging.getLogger(mxLogging.PACKAGE_LOGGER)
        foreign = logging.NullHandler()
        logger.addHandler(foreign)
        setup_mxLogger(log_level="INFO")
        assert foreign in logger.handlers


class TestLevelNames:
    def test_invalid_level_falls_back_to_info(self):
        assert setup_mxLogger(log_level="NOT_A_REAL_LEVEL").level == logging.INFO

    def test_lowercase_level_is_handled(self):
        assert setup_mxLogger(log_level="debug").level == logging.DEBUG

    def test_none_level_falls_back_to_info(self):
        assert setup_mxLogger().level == logging.INFO

    def test_effective_level_of_child_follows_the_package_logger(self):
        setup_mxLogger(log_level="DEBUG")
        assert getLogger("mxcloudshare.sample").getEffectiveLevel() == logging.DEBUG
