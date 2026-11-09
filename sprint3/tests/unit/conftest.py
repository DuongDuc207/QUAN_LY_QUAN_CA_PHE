import pytest


@pytest.fixture(scope="session", autouse=True)
def du_lieu_rieng_cho_test():
    """Unit test khong can SQL Server hay du lieu mau."""
    yield
