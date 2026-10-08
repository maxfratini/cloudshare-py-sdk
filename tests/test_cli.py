import os
import tempfile

import pytest

from mxcloudshare import cli


class TestFlattenDict:

    def test_flattens_simple_dict(self):
        flat = cli._flatten_dict({"a": 1, "b": 2})
        assert flat == {"a": "1", "b": "2"}

    def test_flattens_nested_dict(self):
        flat = cli._flatten_dict({"a": 1, "b": {"c": 2, "d": {"e": 3}}})
        assert flat == {"a": "1", "b.c": "2", "b.d.e": "3"}

    def test_flattens_none_values(self):
        flat = cli._flatten_dict({"a": None, "b": 2})
        assert flat == {"a": "", "b": "2"}

    def test_flattens_custom_separator(self):
        flat = cli._flatten_dict({"a": {"b": 1}}, sep="_")
        assert flat == {"a_b": "1"}


class TestDictToRows:

    def test_converts_list_of_dicts(self):
        rows, cols = cli._dict_to_rows([{"id": "a", "name": "b"}, {"id": "c", "name": "d"}])
        assert cols == ["id", "name"]
        assert len(rows) == 2
        assert rows[0] == ["a", "b"]
        assert rows[1] == ["c", "d"]

    def test_converts_single_dict(self):
        rows, cols = cli._dict_to_rows({"id": "a", "name": "b"})
        assert cols == ["id", "name"]
        assert len(rows) == 1
        assert rows[0] == ["a", "b"]

    def test_handles_missing_keys(self):
        rows, cols = cli._dict_to_rows([{"id": "a"}, {"id": "c", "name": "d"}])
        assert cols == ["id", "name"]
        assert len(rows) == 2
        assert rows[0] == ["a", ""]
        assert rows[1] == ["c", "d"]


class TestShowResults:

    def test_returns_row_count(self):
        assert cli.show_results([{"id": "a"}, {"id": "b"}]) == 2

    def test_handles_single_dict(self):
        assert cli.show_results({"id": "a"}) == 1


class TestPrintAsTable:

    def test_renders_a_list_of_dicts_without_raising(self):
        cli.print_as_table([{"id": "a", "name": "b"}, {"id": "c", "name": "d"}])

    def test_renders_a_single_dict_without_raising(self):
        cli.print_as_table({"id": "a", "name": "b"})


class TestInitializeApp:

    def test_tolerates_none_common_opts(self):
        # cyclopts passes None when none of the common options were supplied;
        # this used to raise AttributeError on None.logfile.
        with pytest.raises(SystemExit):
            cli.initializeApp(None)

    def test_uses_supplied_common_opts(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLOUDSHARE_API_ID", "id-from-env")
        monkeypatch.setenv("CLOUDSHARE_API_KEY", "key-from-env")

        config = cli.initializeApp(cli.mxCommonOpts(tablewidth=123, outformat="table"))

        assert config.tablewidth == 123
        assert config.outputformat == "table"
        assert config.api_id == "id-from-env"
        assert config.api_key == "key-from-env"


class TestLoadKeys:

    @pytest.fixture(autouse=True)
    def _clean_env(self, monkeypatch):
        monkeypatch.delenv("CLOUDSHARE_API_ID", raising=False)
        monkeypatch.delenv("CLOUDSHARE_API_KEY", raising=False)
        monkeypatch.chdir(tempfile.mkdtemp())

    def test_reads_keys_from_the_passed_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as fh:
            fh.write("CLOUDSHARE_API_ID=from-file\nCLOUDSHARE_API_KEY=also-file\n")
            path = fh.name

        try:
            assert cli.loadKeys(path) == ("from-file", "also-file")
        finally:
            os.unlink(path)

    def test_falls_back_to_cloudshare_env_in_the_working_directory(self, monkeypatch):
        with open("cloudshare.env", "w") as fh:
            fh.write("CLOUDSHARE_API_ID=from-cwd\nCLOUDSHARE_API_KEY=also-cwd\n")
        monkeypatch.chdir(".")

        assert cli.loadKeys(None) == ("from-cwd", "also-cwd")

    def test_exits_when_no_keys_are_available(self):
        with pytest.raises(SystemExit) as exc:
            cli.loadKeys(None)

        assert exc.value.code == 1


class TestEnvExtend:
    def test_command_registered(self):
        assert "env-extend" in cli.cs_app._commands


class TestEnvRevert:
    def test_command_registered(self):
        assert "env-revert" in cli.cs_app._commands


class TestEnvPostpone:
    def test_command_registered(self):
        assert "env-postpone" in cli.cs_app._commands


class TestSnapshotTake:
    def test_command_registered(self):
        assert "snapshot-take" in cli.cs_app._commands


class TestSnapshotList:
    def test_command_registered(self):
        assert "snapshot-list" in cli.cs_app._commands


class TestSnapshotMarkDefault:
    def test_command_registered(self):
        assert "snapshot-mark-default" in cli.cs_app._commands


class TestVmReboot:
    def test_command_registered(self):
        assert "vm-reboot" in cli.cs_app._commands


class TestVmRevert:
    def test_command_registered(self):
        assert "vm-revert" in cli.cs_app._commands


class TestVmDelete:
    def test_command_registered(self):
        assert "vm-delete" in cli.cs_app._commands


class TestVmHardware:
    def test_command_registered(self):
        assert "vm-hardware" in cli.cs_app._commands


class TestVmRemoteAccess:
    def test_command_registered(self):
        assert "vm-remote-access" in cli.cs_app._commands


class TestApiCall:
    def test_command_registered(self):
        assert "api-call" in cli.cs_app._commands


class TestBlueprintListProjectId:
    def test_command_registered(self):
        assert "blueprint-list" in cli.cs_app._commands


class TestPolicyListProjectId:
    def test_command_registered(self):
        assert "policy-list" in cli.cs_app._commands


class TestClassSendInvitations:
    def test_command_registered(self):
        assert "class-sendinvitations" in cli.cs_app._commands


class TestClassSuspendAll:
    def test_command_registered(self):
        assert "class-suspend-all" in cli.cs_app._commands


class TestClassDeleteAll:
    def test_command_registered(self):
        assert "class-delete-all" in cli.cs_app._commands


class TestClassSponsoredLink:
    def test_command_registered(self):
        assert "class-sponsoredlink" in cli.cs_app._commands


class TestClassDetailed:
    def test_command_registered(self):
        assert "class-detailed" in cli.cs_app._commands


class TestClassCountries:
    def test_command_registered(self):
        assert "class-countries" in cli.cs_app._commands


class TestClassCustomFields:
    def test_command_registered(self):
        assert "class-custom-fields" in cli.cs_app._commands


class TestClassResumeStudent:
    def test_command_registered(self):
        assert "class-resume-student" in cli.cs_app._commands


class TestStudentList:
    def test_command_registered(self):
        assert "student-list" in cli.cs_app._commands


class TestStudentGet:
    def test_command_registered(self):
        assert "student-get" in cli.cs_app._commands


class TestStudentCreate:
    def test_command_registered(self):
        assert "student-create" in cli.cs_app._commands


class TestStudentUpdate:
    def test_command_registered(self):
        assert "student-update" in cli.cs_app._commands


class TestStudentDelete:
    def test_command_registered(self):
        assert "student-delete" in cli.cs_app._commands


class TestInstructorList:
    def test_command_registered(self):
        assert "instructor-list" in cli.cs_app._commands


class TestInstructorCreate:
    def test_command_registered(self):
        assert "instructor-create" in cli.cs_app._commands


class TestInstructorDelete:
    def test_command_registered(self):
        assert "instructor-delete" in cli.cs_app._commands


class TestWebhookList:
    def test_command_registered(self):
        assert "webhook-list" in cli.cs_app._commands


class TestWebhookGet:
    def test_command_registered(self):
        assert "webhook-get" in cli.cs_app._commands


class TestWebhookCreate:
    def test_command_registered(self):
        assert "webhook-create" in cli.cs_app._commands


class TestWebhookDelete:
    def test_command_registered(self):
        assert "webhook-delete" in cli.cs_app._commands


class TestPermalinkCreate:
    def test_command_registered(self):
        assert "permalink-create" in cli.cs_app._commands


class TestPermalinkGet:
    def test_command_registered(self):
        assert "permalink-get" in cli.cs_app._commands


class TestPing:
    def test_command_registered(self):
        assert "ping" in cli.cs_app._commands


class TestRegionList:
    def test_command_registered(self):
        assert "region-list" in cli.cs_app._commands


class TestTimezoneList:
    def test_command_registered(self):
        assert "timezone-list" in cli.cs_app._commands


class TestTeamList:
    def test_command_registered(self):
        assert "team-list" in cli.cs_app._commands


class TestTeamCreate:
    def test_command_registered(self):
        assert "team-create" in cli.cs_app._commands


class TestInviteProjectMember:
    def test_command_registered(self):
        assert "invite-project-member" in cli.cs_app._commands


class TestInviteToPoc:
    def test_command_registered(self):
        assert "invite-to-poc" in cli.cs_app._commands


class TestLoginUrl:
    def test_command_registered(self):
        assert "login-url" in cli.cs_app._commands


class TestClassGuidedJourney:
    def test_command_registered(self):
        assert "class-guided-journey" in cli.cs_app._commands


class TestStudentGuidedJourney:
    def test_command_registered(self):
        assert "student-guided-journey" in cli.cs_app._commands


class TestSharedEnvGet:
    def test_command_registered(self):
        assert "shared-env-get" in cli.cs_app._commands


class TestPublicCloudGet:
    def test_command_registered(self):
        assert "public-cloud-get" in cli.cs_app._commands


# ──────────────────────────────────────────
# P2-3: CSV output
# ──────────────────────────────────────────


class TestCsvOutput:
    def test_csv_uses_stdlib_and_quotes_all(self, capsys):
        data = [{"id": "a", "name": "hello,world"}, {"id": "b", "name": 'quote"here'}]
        config = cli.AppConfig(outputformat="csv")
        cli.print_results(data, config)
        captured = capsys.readouterr()
        output = captured.out
        # Should have proper CSV quoting with QUOTE_ALL
        assert '"id","name"' in output
        assert '"a","hello,world"' in output
        assert '"b","quote""here"' in output


# ──────────────────────────────────────────
# P2-4: _filter_fields helper
# ──────────────────────────────────────────


class TestFilterFields:
    def test_keeps_selected_fields(self):
        data = [{"id": "1", "name": "a", "other": "x"}]
        cli._filter_fields(data, ["id", "name"], False)
        assert data == [{"id": "1", "name": "a"}]

    def test_keeps_all_when_no_field_list(self):
        data = [{"id": "1", "name": "a"}]
        cli._filter_fields(data, [], False)
        assert data == [{"id": "1", "name": "a"}]

    def test_availfields_exits(self):
        with pytest.raises(SystemExit):
            cli._filter_fields([{"a": 1}], [], True)


# ──────────────────────────────────────────
# P3-2: --version flag
# ──────────────────────────────────────────


class TestVersionFlag:
    def test_version_is_configured(self):
        assert cli.cs_app.version is not None
        assert isinstance(cli.cs_app.version, str)
        assert len(cli.cs_app.version) > 0


# ──────────────────────────────────────────
# P3-3: --dry-run
# ──────────────────────────────────────────


class TestDryRunEnvSuspend:
    def test_has_dry_run_param(self):
        import inspect
        func = cli.cs_app._commands["env-suspend"].default_command
        params = inspect.signature(func).parameters
        assert "dry_run" in params


class TestDryRunEnvDelete:
    def test_has_dry_run_param(self):
        import inspect
        func = cli.cs_app._commands["env-delete"].default_command
        params = inspect.signature(func).parameters
        assert "dry_run" in params


class TestDryRunEnvResume:
    def test_has_dry_run_param(self):
        import inspect
        func = cli.cs_app._commands["env-resume"].default_command
        params = inspect.signature(func).parameters
        assert "dry_run" in params


class TestDryRunEnvExtend:
    def test_has_dry_run_param(self):
        import inspect
        func = cli.cs_app._commands["env-extend"].default_command
        params = inspect.signature(func).parameters
        assert "dry_run" in params


class TestDryRunEnvRevert:
    def test_has_dry_run_param(self):
        import inspect
        func = cli.cs_app._commands["env-revert"].default_command
        params = inspect.signature(func).parameters
        assert "dry_run" in params


class TestDryRunClassDeleteAll:
    def test_has_dry_run_param(self):
        import inspect
        func = cli.cs_app._commands["class-delete-all"].default_command
        params = inspect.signature(func).parameters
        assert "dry_run" in params


# ──────────────────────────────────────────
# P3-4: --json input parsing
# ──────────────────────────────────────────


class TestParseJsonInput:
    def test_parses_json_string(self):
        result = cli._parse_json_input('{"a": 1}')
        assert result == {"a": 1}

    def test_parses_json_from_file(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('{"bp": "x"}')
        result = cli._parse_json_input(f"@{f}")
        assert result == {"bp": "x"}

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError):
            cli._parse_json_input("{bad}")

    def test_env_create_accepts_json_param(self):
        import inspect
        func = cli.cs_app._commands["env-create"].default_command
        params = inspect.signature(func).parameters
        assert "json_input" in params

    def test_class_create_accepts_json_param(self):
        import inspect
        func = cli.cs_app._commands["class-create"].default_command
        params = inspect.signature(func).parameters
        assert "json_input" in params


# ──────────────────────────────────────────
# P3-6: Rich Progress bar in env_wait_condition
# ──────────────────────────────────────────


class TestEnvWaitCondition:
    """env_wait_condition must keep its signature backward compatible and not
    raise on mock data."""

    def test_signature_unchanged_positional(self):
        """All existing positional params still work without operation."""
        import inspect
        sig = inspect.signature(cli.env_wait_condition)
        # Original params plus one optional ``operation``
        assert "envId" in sig.parameters
        assert "checks" in sig.parameters
        assert "delay_secs" in sig.parameters
        assert "max_retry" in sig.parameters
        assert "operation" in sig.parameters

    def test_operation_param_defaults_to_none(self):
        """Backward compatible: operation=None means no progress bar."""
        import inspect
        param = inspect.signature(cli.env_wait_condition).parameters["operation"]
        assert param.default is None

    def test_called_without_operation_does_not_raise(self, monkeypatch):
        """Calling with old call signature works."""
        monkeypatch.setattr("mxcloudshare.mxcloudshare.get_vms", lambda eid: [{"name": "vm-1", "statusText": "Ready", "id": "v1"}])
        result = cli.env_wait_condition("env-1", [{"property": "statusText", "check_fn": lambda x: x == "Ready"}])
        assert result is True

    def test_called_with_operation_does_not_raise(self, monkeypatch):
        """Calling with operation string works."""
        monkeypatch.setattr("mxcloudshare.mxcloudshare.get_vms", lambda eid: [{"name": "vm-1", "statusText": "Running", "id": "v1"}])
        result = cli.env_wait_condition(
            "env-1",
            [{"property": "statusText", "check_fn": lambda x: x == "Running"}],
            operation="Testing env-1",
        )
        assert result is True

    def test_timeout_returns_false(self, monkeypatch):
        """When VMs never match, eventually times out and returns False."""
        monkeypatch.setattr("mxcloudshare.mxcloudshare.get_vms", lambda eid: [{"name": "vm-1", "statusText": "Working", "id": "v1"}])
        result = cli.env_wait_condition(
            "env-1",
            [{"property": "statusText", "check_fn": lambda x: x == "Ready"}],
            delay_secs=0, max_retry=2, operation="Timeout-test",
        )
        assert result is False