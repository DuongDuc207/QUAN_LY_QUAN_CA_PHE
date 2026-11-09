import pytest
from dotenv import load_dotenv

load_dotenv()

from tests import du_lieu_test  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def du_lieu_rieng_cho_test():
    du_lieu_test.tao()
    yield
    du_lieu_test.xoa()
