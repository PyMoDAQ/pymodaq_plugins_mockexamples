"""Start the .NET runtime and load a .NET assembly with ``pythonnet``, the way a plugin for a vendor assembly should.

Many manufacturers give a .NET assembly (``Vendor.Device.dll``) instead of a C library. ``pythonnet`` makes its
classes importable from Python once the runtime is running and the assembly is referenced. ``load_dotnet`` and
``load_assembly`` are meant to be copied in a plugin package. Like ``load_library`` for a C library, they say what
was tried when something is missing instead of the bare exception of ``pythonnet``.

``pythonnet`` is imported here and nowhere else at module level of the package, so that a plugin only needs it (and a
.NET runtime: the one of Windows, or ``dotnet`` / ``mono`` elsewhere) when it really talks to an assembly.
"""
import importlib
import os
import platform
from pathlib import Path
from typing import Optional, Sequence, Union


class DotNetNotAvailableError(RuntimeError):
    """``pythonnet`` is not installed or no .NET runtime could be started"""


class AssemblyNotFoundError(OSError):
    """No candidate could be loaded; the message lists every candidate and why it failed"""


def load_dotnet(runtime: Optional[str] = None):
    """Start the .NET runtime (once per process) and return the ``clr`` module of ``pythonnet``

    Parameters
    ----------
    runtime: 'netfx', 'coreclr' or 'mono', optional
        The runtime to start. By default ``netfx`` (the .NET Framework installed with Windows) on Windows and
        ``coreclr`` (.NET 6 and later, the ``dotnet`` command) elsewhere. An assembly built for .NET Framework 4.x
        usually loads on both; one built for .NET 6+ only on ``coreclr``. The runtime can be chosen only once.

    Raises
    ------
    DotNetNotAvailableError
        ``pythonnet`` is missing, or the runtime could not start (the message tells how to install one).
    """
    try:
        import pythonnet
    except ImportError as e:
        raise DotNetNotAvailableError('pythonnet is not installed: pip install pythonnet') from e
    runtime = runtime or os.environ.get('PYTHONNET_RUNTIME') or ('netfx' if platform.system() == 'Windows'
                                                                  else 'coreclr')
    try:
        pythonnet.load(runtime)
        import clr
    except Exception as e:  # clr_loader raises various exceptions when the runtime is not found
        raise DotNetNotAvailableError(
            f'Could not start the {runtime} runtime of .NET ({e}). Install it (on Windows the .NET Framework is '
            f'already there; elsewhere install .NET 6+ or mono) or choose another one.') from e
    return clr


def load_assembly(names: Union[str, Sequence[str]], path: Optional[Union[str, Path]] = None,
                  env_var: Optional[str] = None, namespace: Optional[str] = None):
    """Reference a .NET assembly and return the module of its namespace, when asked

    Parameters
    ----------
    names: str or list of str
        Names of the assembly (``Vendor.Device``, without ``.dll``) tried in order: the first that can be loaded is
        used. Several names are useful when the same classes live in different assemblies on different runtimes.
    path: str or Path, optional
        Full path to the ``.dll`` or to the folder that holds it (typically a setting of the plugin); tried first.
    env_var: str, optional
        Name of an environment variable holding such a path; tried second.
    namespace: str, optional
        If given, the module of this namespace (``import Vendor.Device``) is returned: its classes can then be
        used, the .NET exceptions of the assembly can be caught...

    Raises
    ------
    AssemblyNotFoundError
        Listing everything that was tried.
    """
    clr = load_dotnet()
    wanted = [names] if isinstance(names, str) else list(names)
    candidates = []
    for location in (path, os.environ.get(env_var) if env_var else None):
        if location:
            location = Path(location)
            candidates.extend([location / f'{name}.dll' for name in wanted] if location.is_dir() else [location])
    candidates.extend(wanted)

    failures = []
    for candidate in candidates:
        if isinstance(candidate, Path) and not candidate.is_file():
            failures.append(f'{candidate}: no such file')
            continue
        try:
            clr.AddReference(str(candidate))
        except Exception as e:
            failures.append(f'{candidate}: {e}')
            continue
        return importlib.import_module(namespace) if namespace else clr
    raise AssemblyNotFoundError('Could not load the .NET assembly. Tried:\n  ' + '\n  '.join(failures))
