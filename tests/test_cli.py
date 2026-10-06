import os
import tempfile

import pytest
from rich.table import Table

from mxcloudshare import cli


class TestDfToTable:

    def test_adds_one_column_per_dataframe_column(self):
        df = cli.pd.DataFrame([{"id": "a", "name": "b"}])
        table = cli.df_to_table(df, Table())

        assert [c.header for c in table.columns] == ["id", "name"]

    def test_adds_a_row_per_dataframe_row(self):
        df = cli.pd.DataFrame([{"id": "a"}, {"id": "b"}])
        table = cli.df_to_table(df, Table())

        assert table.row_count == 2

    def test_show_index_prepends_a_row_number_column(self):
        df = cli.pd.DataFrame([{"id": "a"}, {"id": "b"}])
        table = cli.df_to_table(df, Table(), show_index=True, index_name="n")

        assert [c.header for c in table.columns] == ["n", "id"]
        assert table.row_count == 2

    def test_returns_the_table_it_was_given(self):
        df = cli.pd.DataFrame([{"id": "a"}])
        table = Table()
        assert cli.df_to_table(df, table) is table


class TestPrintAsTable:

    def test_renders_a_list_of_dicts_without_raising(self):
        cli.print_as_table([{"id": "a", "name": "b"}, {"id": "c", "name": "d"}])

    def test_renders_a_single_dict_without_raising(self):
        cli.print_as_table({"id": "a", "name": "b"})

    def test_show_results_returns_the_row_count(self):
        assert cli.show_results([{"id": "a"}, {"id": "b"}]) == 2


class TestInitializeApp:

    def test_tolerates_none_common_opts(self):
        # cyclopts passes None when none of the common options were supplied;
        # this used to raise AttributeError on None.logfile.
        with pytest.raises(SystemExit):
            cli.initializeApp(None)

    def test_uses_supplied_common_opts(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CLOUDSHARE_API_ID", "id-from-env")
        monkeypatch.setenv("CLOUDSHARE_API_KEY", "key-from-env")

        cli.initializeApp(cli.mxCommonOpts(tablewidth=123, outformat="table"))

        assert cli.globalconf["tablewidth"] == 123
        assert cli.globalconf["outputformat"] == "table"
        assert cli.globalconf["API_ID"] == "id-from-env"


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