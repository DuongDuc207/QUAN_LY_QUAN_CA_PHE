"""Prepare this sprint's isolated Python environment for direct CLI runs."""

import importlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import venv


def _missing_dependencies():
    return [name for name in ("dotenv", "flask", "pyodbc")
            if importlib.util.find_spec(name) is None]


def ensure_runtime(allow_reexec=False):
    root = Path(__file__).resolve().parent
    env_dir = root / ".venv"
    python = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    if allow_reexec:
        try:
            if Path(sys.prefix).resolve() != env_dir.resolve():
                if not python.is_file():
                    print(f"[{root.name}] Tao moi truong Python rieng: {env_dir}", flush=True)
                    venv.EnvBuilder(with_pip=True).create(str(env_dir))
                # Use only this sprint's environment, even if global packages exist.
                raise SystemExit(subprocess.call(
                    [str(python), str(Path(sys.argv[0]).resolve()), *sys.argv[1:]]
                ))

            if _missing_dependencies():
                print(f"[{root.name}] Cai thu vien tu requirements.txt...", flush=True)
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install",
                    "-r", str(root / "requirements.txt"),
                ])
                importlib.invalidate_caches()
        except (OSError, subprocess.CalledProcessError) as error:
            raise SystemExit(
                f"Khong the chuan bi moi truong cho {root.name}: {error}\n"
                "Kiem tra Python, ket noi mang va thu chay lai: py app.py"
            ) from error

    missing = _missing_dependencies()
    if missing:
        raise SystemExit(
            "Thieu thu vien Python: " + ", ".join(missing) + "\n"
            f"Trong thu muc {root.name}, chay:\n"
            "  py app.py\n"
            "Hoac cai thu cong:\n"
            "  py -m venv .venv\n"
            "  .venv\\Scripts\\python.exe -m pip install -r requirements.txt\n"
            "  .venv\\Scripts\\python.exe app.py"
        )

