"""Tests for the legacy wrapper module (mxcloudshare.cloudshare.wrapper).

The wrapper module is retained as a backward-compatible public API surface but
is no longer used by the CLI or modern SDK path. These tests verify importability
and the pure-helpers that don't require API credentials.
"""

import inspect

from mxcloudshare.cloudshare import wrapper


class TestImport:
    """Verify the module imports without error."""

    def test_module_imports(self):
        assert wrapper is not None

    def test_memoize_decorator_exists(self):
        assert callable(wrapper.memoize)


class TestWithEnvPrefix:
    """with_env_prefix is a pure function — no API call needed."""

    def test_adds_en_prefix(self):
        assert wrapper.with_env_prefix("12345") == "EN12345"

    def test_keeps_existing_prefix(self):
        assert wrapper.with_env_prefix("EN12345") == "EN12345"

    def test_handles_empty_string(self):
        assert wrapper.with_env_prefix("") == "EN"

    def test_is_idempotent(self):
        doubled = wrapper.with_env_prefix(wrapper.with_env_prefix("abc"))
        assert doubled == "ENabc"


class TestBugfixApplied:
    """Verify the latent .cs_get() bug (PRG-002) has been fixed."""

    def test_create_env_uses_get_not_cs_get(self):
        """The old code used dct['itemsCart'][0].cs_get('snapshotId'),
        which is an AttributeError — dict has no cs_get method.
        The fix replaces it with .get('snapshotId').
        """
        source = inspect.getsource(wrapper.create_env_from_bp_using_names)
        # The fixed code should use .get() and must NOT use .cs_get()
        assert ".get(" in source
        assert ".cs_get(" not in source

    def test_create_env_snapshot_check_uses_new_dct(self):
        """The fix also corrected the variable reference from dct to new_dct."""
        source = inspect.getsource(wrapper.create_env_from_bp_using_names)
        assert "new_dct['itemsCart'][0].get('snapshotId')" in source


class TestPortedFunctions:
    """Verify functions ported from wrapper_cls are accessible."""

    def test_get_bp_by_id_exists(self):
        assert hasattr(wrapper, "get_bp_by_id")
        assert callable(wrapper.get_bp_by_id)

    def test_get_external_id_exists(self):
        assert hasattr(wrapper, "get_external_id")
        assert callable(wrapper.get_external_id)

    def test_get_internal_id_exists(self):
        assert hasattr(wrapper, "get_internal_id")
        assert callable(wrapper.get_internal_id)

    def test_get_vm_list_exists(self):
        assert hasattr(wrapper, "get_vm_list")
        assert callable(wrapper.get_vm_list)

    def test_delete_bp_exists(self):
        assert hasattr(wrapper, "delete_bp")
        assert callable(wrapper.delete_bp)

    def test_add_bp_id_to_project_exists(self):
        assert hasattr(wrapper, "add_bp_id_to_project")
        assert callable(wrapper.add_bp_id_to_project)

    def test_remove_bp_from_project_docstring_present(self):
        """Verify the enhanced version has the BP-prefix detection docs."""
        doc = wrapper.remove_bp_from_project.__doc__
        assert doc is not None
        assert "If bp_name starts with 'BP'" in doc


class TestLowLevelHelpers:
    """The request-level helpers should still be the original signatures."""

    def test_post_exists(self):
        assert callable(wrapper.post)

    def test_get_exists(self):
        assert callable(wrapper.get)

    def test_put_exists(self):
        assert callable(wrapper.put)

    def test_request_exists(self):
        assert callable(wrapper.request)