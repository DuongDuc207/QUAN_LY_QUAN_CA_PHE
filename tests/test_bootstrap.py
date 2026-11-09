"""Runtime setup must stay isolated and must not install packages on import."""

from contextlib import ExitStack
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.runtimes = []
        for number in range(1, 5):
            path = ROOT / f"sprint{number}" / "bootstrap.py"
            spec = importlib.util.spec_from_file_location(f"runtime{number}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.runtimes.append(module)

    def test_import_with_dependencies_does_not_prepare_environment(self):
        for runtime in self.runtimes:
            with self.subTest(sprint=runtime.__name__), ExitStack() as stack:
                stack.enter_context(patch.object(runtime, "_missing_dependencies", return_value=[]))
                install = stack.enter_context(patch.object(runtime.subprocess, "check_call"))
                launch = stack.enter_context(patch.object(runtime.subprocess, "call"))
                runtime.ensure_runtime()
                install.assert_not_called()
                launch.assert_not_called()

    def test_import_without_dependencies_gives_local_instructions(self):
        for runtime in self.runtimes:
            with self.subTest(sprint=runtime.__name__), ExitStack() as stack:
                stack.enter_context(patch.object(runtime, "_missing_dependencies", return_value=["dotenv"]))
                install = stack.enter_context(patch.object(runtime.subprocess, "check_call"))
                with self.assertRaises(SystemExit) as result:
                    runtime.ensure_runtime()
                self.assertIn(Path(runtime.__file__).parent.name, str(result.exception))
                self.assertIn("requirements.txt", str(result.exception))
                install.assert_not_called()

    def test_cli_uses_local_environment_and_preserves_arguments_and_exit_code(self):
        for runtime in self.runtimes:
            root = Path(runtime.__file__).parent
            with self.subTest(sprint=runtime.__name__), ExitStack() as stack:
                stack.enter_context(patch.object(runtime.sys, "prefix", str(ROOT)))
                stack.enter_context(patch.object(runtime.sys, "argv", [str(root / "tao_tai_khoan.py"), "--help"]))
                stack.enter_context(patch.object(runtime.Path, "is_file", return_value=True))
                launch = stack.enter_context(patch.object(runtime.subprocess, "call", return_value=7))
                builder = stack.enter_context(patch.object(runtime.venv, "EnvBuilder"))
                with self.assertRaises(SystemExit) as result:
                    runtime.ensure_runtime(allow_reexec=True)
                self.assertEqual(result.exception.code, 7)
                command = launch.call_args.args[0]
                self.assertTrue(Path(command[0]).is_relative_to(root / ".venv"))
                self.assertEqual(command[1:], [str(root / "tao_tai_khoan.py"), "--help"])
                builder.assert_not_called()

    def test_first_cli_run_creates_own_environment(self):
        for runtime in self.runtimes:
            root = Path(runtime.__file__).parent
            with self.subTest(sprint=runtime.__name__), ExitStack() as stack:
                stack.enter_context(patch.object(runtime.sys, "prefix", str(ROOT)))
                stack.enter_context(patch.object(runtime.Path, "is_file", return_value=False))
                stack.enter_context(patch.object(runtime.subprocess, "call", return_value=0))
                builder = stack.enter_context(patch.object(runtime.venv, "EnvBuilder"))
                with self.assertRaises(SystemExit) as result:
                    runtime.ensure_runtime(allow_reexec=True)
                self.assertEqual(result.exception.code, 0)
                builder.assert_called_once_with(with_pip=True)
                builder.return_value.create.assert_called_once_with(str(root / ".venv"))

    def test_local_runtime_installs_missing_dependencies_once(self):
        for runtime in self.runtimes:
            root = Path(runtime.__file__).parent
            with self.subTest(sprint=runtime.__name__), ExitStack() as stack:
                stack.enter_context(patch.object(runtime.sys, "prefix", str(root / ".venv")))
                stack.enter_context(patch.object(runtime, "_missing_dependencies", side_effect=[["dotenv"], []]))
                install = stack.enter_context(patch.object(runtime.subprocess, "check_call"))
                launch = stack.enter_context(patch.object(runtime.subprocess, "call"))
                runtime.ensure_runtime(allow_reexec=True)
                install.assert_called_once_with([
                    runtime.sys.executable, "-m", "pip", "install", "-r", str(root / "requirements.txt")
                ])
                launch.assert_not_called()

    def test_failed_install_stops_with_recovery_message(self):
        for runtime in self.runtimes:
            root = Path(runtime.__file__).parent
            with self.subTest(sprint=runtime.__name__), ExitStack() as stack:
                stack.enter_context(patch.object(runtime.sys, "prefix", str(root / ".venv")))
                stack.enter_context(patch.object(runtime, "_missing_dependencies", return_value=["dotenv"]))
                stack.enter_context(patch.object(runtime.subprocess, "check_call", side_effect=subprocess.CalledProcessError(1, "pip")))
                with self.assertRaises(SystemExit) as result:
                    runtime.ensure_runtime(allow_reexec=True)
                self.assertIn("py app.py", str(result.exception))


if __name__ == "__main__":
    unittest.main()
