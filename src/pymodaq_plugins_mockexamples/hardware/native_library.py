"""Load a native (C) library with ``ctypes``, the way a plugin for a vendor DLL or shared object should.

``load_library`` is meant to be copied in a plugin package. It takes a list of names per platform, an optional path
(from a setting of the plugin) and an optional environment variable, and tells what was tried when nothing is found,
instead of the bare ``OSError`` of ``ctypes``.
"""
import ctypes
import ctypes.util
import os
import platform
from pathlib import Path
from typing import Mapping, Optional, Sequence, Union

Names = Union[str, Sequence[str], Mapping[str, Sequence[str]]]


class LibraryNotFoundError(OSError):
    """No candidate could be loaded; the message lists every candidate and why it failed"""


def candidate_names(names: Names, system: Optional[str] = None) -> list[str]:
    """The names to try on this platform

    ``names`` is a name, a list of names, or a dict from ``platform.system()`` ('Windows', 'Linux', 'Darwin') to the
    names to try on that platform.
    """
    if isinstance(names, str):
        return [names]
    if isinstance(names, Mapping):
        return list(names.get(system or platform.system(), []))
    return list(names)


def load_library(names: Names, path: Optional[Union[str, Path]] = None, env_var: Optional[str] = None,
                 convention: str = 'cdecl') -> ctypes.CDLL:
    """Load a native library

    Parameters
    ----------
    names: str, list of str or dict
        The file name (``avaspec.dll``, ``libusb-1.0.so``) or the name given to ``ctypes.util.find_library``
        (``c``, ``usb-1.0``), see ``candidate_names``.
    path: str or Path, optional
        Full path to the library or to the folder that holds it (typically a setting of the plugin); tried first.
    env_var: str, optional
        Name of an environment variable holding such a path; tried second.
    convention: 'cdecl' or 'stdcall'
        The calling convention of the library. ``stdcall`` is a Windows convention (many vendor DLLs use it, see the
        documentation of the SDK): ``ctypes.WinDLL`` is used there, and ``ctypes.CDLL`` on other systems.

    Raises
    ------
    LibraryNotFoundError
        Listing everything that was tried.
    """
    if convention not in ('cdecl', 'stdcall'):
        raise ValueError(f"convention should be 'cdecl' or 'stdcall', not {convention!r}")
    loader = ctypes.WinDLL if convention == 'stdcall' and hasattr(ctypes, 'WinDLL') else ctypes.CDLL
    wanted = candidate_names(names)

    candidates: list[str] = []
    for folder_or_file in (path, os.environ.get(env_var) if env_var else None):
        if folder_or_file:
            base = Path(folder_or_file)
            if base.is_dir():
                candidates.extend(str(base / name) for name in wanted)
            else:
                candidates.append(str(base))
    for name in wanted:
        candidates.append(name)
        found = ctypes.util.find_library(name)
        if found and found not in candidates:
            candidates.append(found)

    errors = []
    for candidate in candidates:
        try:
            return loader(candidate)
        except OSError as e:
            errors.append(f'{candidate}: {e}')
    raise LibraryNotFoundError(
        f'Could not load the library {wanted} on {platform.system()}. Tried:\n  ' + '\n  '.join(errors or ['(nothing)']) +
        '\nGive the full path in the settings of the plugin' +
        (f' or in the environment variable {env_var}.' if env_var else '.'))
