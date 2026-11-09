import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILES = [
    ROOT / "config" / "settings.py",
    *(ROOT / f"sprint{number}" / "config" / "settings.py" for number in range(1, 5)),
]
SETTINGS_FILES = [path for path in SETTINGS_FILES if path.is_file()]


def load_settings(path, secret_key):
    module_name = f"settings_check_{path.parent.parent.name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(os.environ, {"FLASK_SECRET_KEY": secret_key}):
        spec.loader.exec_module(module)
    return module


class SecretSettingsTests(unittest.TestCase):
    def test_requires_a_configured_secret_key_of_at_least_32_characters(self):
        for path in SETTINGS_FILES:
            for secret_key in ("", "short"):
                with self.subTest(settings=str(path), key_length=len(secret_key)):
                    with self.assertRaisesRegex(RuntimeError, "FLASK_SECRET_KEY"):
                        load_settings(path, secret_key)

    def test_accepts_a_configured_secret_key(self):
        secret_key = "a" * 64
        for path in SETTINGS_FILES:
            with self.subTest(settings=str(path)):
                settings = load_settings(path, secret_key)
                self.assertEqual(settings.SECRET_KEY, secret_key)


if __name__ == "__main__":
    unittest.main()
