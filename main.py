"""Launcher compiled by Nuitka.

Nuitka takes a script path as its main program (it cannot compile
``python -m mxcloudshare`` directly), so this thin shim is the entry point
that gets turned into a standalone binary. It is intentionally *not* part of
the wheel: the installed console script is ``mxcloudshare.cli:main``.

Build options live here as ``# nuitka-project`` comments because that is where
Nuitka reads them for a direct ``nuitka main.py`` invocation. (The
``[tool.nuitka]`` table in pyproject.toml is only consulted when Nuitka runs as
a package build backend, which we do not do.)

Run ``make dist`` for a standalone folder, ``make build-onefile`` for a single
executable. Nuitka does not cross-compile, so each target OS needs its own
runner -- see .github/workflows/build.yml.
"""

# nuitka-project: --mode=standalone
# nuitka-project: --output-dir=dist
# nuitka-project: --output-filename=mxcloudshare
# nuitka-project: --company-name=mxcloudshare
# nuitka-project: --product-name=mxCloudShare
# nuitka-project: --file-description=CloudShare automation tool
# nuitka-project: --include-package=mxcloudshare
# nuitka-project: --nofollow-import-to=pytest
# nuitka-project: --nofollow-import-to=_pytest
# nuitka-project: --nofollow-import-to=IPython
# nuitka-project: --nofollow-import-to=jupyter
# nuitka-project: --enable-plugin=no-qt
# nuitka-project: --assume-yes-for-downloads
# nuitka-project-if: {OS} == "Windows":
#    nuitka-project: --windows-console-mode=force
#    nuitka-project: --file-version={FILE_VERSION}
#    nuitka-project: --product-version={PRODUCT_VERSION}
#
# NB: --macos-create-app-bundle sets the compilation mode itself, so it cannot
# live here alongside --mode. Use `make dist-bundle` for the .app variant.

from mxcloudshare.cli import main

if __name__ == "__main__":
    main()