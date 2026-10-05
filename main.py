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

# --file-version/--product-version take a Windows *resource* version: up to four
# integers joined by commas ("0,2,0,0"), not a PEP 440 string. The tempting
# {VERSION}/{FILE_VERSION}/{PRODUCT_VERSION} placeholders do NOT work here --
# those are runtime constants for embedding in compiled source, and Nuitka
# rejects them as option arguments. So derive the value ourselves. A
# nuitka-project-set must evaluate to a str/int/float/bool, hence the single
# expression producing the final string.
# nuitka-project-set: CS_WIN_VERSION = ",".join(str(n) for n in (tuple(int(p) for p in __import__("mxcloudshare").__version__.split(".") if p.isdigit()) + (0, 0, 0, 0))[:4])
#
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
#    nuitka-project: --file-version={CS_WIN_VERSION}
#    nuitka-project: --product-version={CS_WIN_VERSION}
#
# NB: --macos-create-app-bundle sets the compilation mode itself, so it cannot
# live here alongside --mode. Use `make dist-bundle` for the .app variant.

from mxcloudshare.cli import main

if __name__ == "__main__":
    main()