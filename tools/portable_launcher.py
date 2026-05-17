import ctypes
import os
import subprocess
import sys
from pathlib import Path


def show_error(message):
    try:
        ctypes.windll.user32.MessageBoxW(None, message, "Grok Video Studio", 0x10)
    except Exception:
        print(message)


def main():
    root = Path(sys.executable).resolve().parent
    app_dir = root / "app"
    app_file = app_dir / "main.py"
    runtime_dir = root / "runtime" / "python"
    pythonw = runtime_dir / "pythonw.exe"
    python = runtime_dir / "python.exe"
    launcher = pythonw if pythonw.exists() else python

    if not launcher.exists():
        show_error(f"未找到便携 Python 运行时：\n{launcher}")
        return 1
    if not app_file.exists():
        show_error(f"未找到应用入口文件：\n{app_file}")
        return 1

    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    subprocess.Popen([str(launcher), str(app_file)], cwd=str(app_dir), env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
