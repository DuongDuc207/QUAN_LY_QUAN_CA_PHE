import pytest
from config.settings import DB_NAME
from tests import du_lieu_test  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def du_lieu_rieng_cho_test():
    if not DB_NAME.startswith("QLCP_test_"):
        pytest.fail("Khong chay integration test tren CSDL that. Dung: "
                    ".venv\\Scripts\\python.exe tests/run_isolated.py")
    du_lieu_test.tao()
    yield
    du_lieu_test.xoa()
