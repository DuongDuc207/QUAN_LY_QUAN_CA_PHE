import os

import pytest
from dotenv import load_dotenv

os.environ.setdefault("FLASK_SECRET_KEY", "test-only-" + "0" * 64)

load_dotenv()

from tests import du_lieu_test  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def du_lieu_rieng_cho_test():
    du_lieu_test.tao()
    yield
    du_lieu_test.xoa()
