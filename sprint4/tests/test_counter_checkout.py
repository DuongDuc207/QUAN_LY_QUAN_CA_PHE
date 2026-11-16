"""Counter checkout: confirmed payment must precede preparation and service."""

import datetime
import random
import uuid

import pyodbc
import pytest

from api.payments import service as payments
from app import create_app
from database.connection import get_connection
from tests import du_lieu_test as dl


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    assert client.post("/api/v1/auth/login", json={
        "email": dl.ADMIN_EMAIL, "password": dl.ADMIN_MK,
    }).status_code == 200
    return client


def order(client, mon_id=None, **kwargs):
    r = client.post("/api/v1/orders", json={
        "items": [{"mon_id": mon_id or dl.MON_ID, "so_luong": 1}],
        **kwargs,
    })
    assert r.status_code == 201, r.json
    return r.json["data"]


def payment(client, don, method="TIEN_MAT"):
    r = client.post("/api/v1/payments", json={
        "don_hang_id": don["DonHangID"], "phuong_thuc": method,
        "so_tien": float(don["ThanhTien"]),
    })
    assert r.status_code == 201, r.json
    return r.json["data"]["ThanhToanID"]


def detail(client, did):
    return client.get(f"/api/v1/orders/{did}").json["data"]


@pytest.mark.parametrize("current,next_state", [
    ("MOI", "CHO_PHA_CHE"), ("CHO_PHA_CHE", "DANG_PHA_CHE"),
    ("DANG_PHA_CHE", "HOAN_THANH"),
])
def test_unpaid_order_cannot_prepare_or_serve_even_for_legacy_states(client, current, next_state):
    don = order(client)
    did = don["DonHangID"]
    with get_connection() as conn:
        conn.cursor().execute("UPDATE dbo.DonHang SET TrangThai=? WHERE DonHangID=?", (current, did))
        conn.commit()
    response = client.patch(f"/api/v1/orders/{did}/status", json={"trang_thai": next_state})
    assert response.status_code == 409
    assert "thanh toan" in response.json["message"]
    assert detail(client, did)["TrangThai"] == current


@pytest.mark.parametrize("success", [None, False])
def test_pending_or_failed_payment_does_not_queue_order(client, success):
    don = order(client)
    pid = payment(client, don)
    if success is False:
        assert client.post(f"/api/v1/payments/{pid}/confirm", json={"thanh_cong": False}).status_code == 200
    assert detail(client, don["DonHangID"])["TrangThai"] == "MOI"
    assert client.patch(f"/api/v1/orders/{don['DonHangID']}/status", json={"trang_thai": "CHO_PHA_CHE"}).status_code == 409
    assert client.get(f"/api/v1/orders/{don['DonHangID']}/invoice").status_code == 404


@pytest.mark.parametrize("method,code", [("TIEN_MAT", None), ("CHUYEN_KHOAN", "transfer"), ("THE", "card")])
def test_paid_order_queues_then_prepares_then_serves(client, method, code):
    don = order(client)
    did = don["DonHangID"]
    pid = payment(client, don, method)
    r = client.post(f"/api/v1/payments/{pid}/confirm", json={"ma_giao_dich": f"pytest-counter-{pid}-{code}" if code else None})
    assert r.status_code == 200, r.json
    assert r.json["data"]["HoaDon"]["TrangThaiDon"] == "CHO_PHA_CHE"
    assert detail(client, did)["TrangThaiThanhToan"] == "THANH_CONG"
    assert client.patch(f"/api/v1/orders/{did}/status", json={"trang_thai": "HOAN_THANH"}).status_code == 409
    for state in ("DANG_PHA_CHE", "HOAN_THANH"):
        assert client.patch(f"/api/v1/orders/{did}/status", json={"trang_thai": state}).status_code == 200
    assert detail(client, did)["TrangThai"] == "HOAN_THANH"
    assert client.post(f"/api/v1/payments/{pid}/confirm", json={}).status_code == 409
    assert detail(client, did)["TrangThai"] == "HOAN_THANH"


def test_transfer_needs_confirmation_code_before_preparation(client):
    don = order(client)
    pid = payment(client, don, "CHUYEN_KHOAN")
    assert client.post(f"/api/v1/payments/{pid}/confirm", json={}).status_code == 400
    assert detail(client, don["DonHangID"])["TrangThai"] == "MOI"


@pytest.mark.parametrize("amount", [5000, 10000])
def test_refunded_order_cannot_start_preparation(client, amount):
    don = order(client)
    pid = payment(client, don)
    assert client.post(f"/api/v1/payments/{pid}/confirm", json={}).status_code == 200
    assert client.post(f"/api/v1/payments/{pid}/refund", json={"so_tien": amount, "ly_do": "Pytest counter refund"}).status_code == 200
    assert client.patch(f"/api/v1/orders/{don['DonHangID']}/status", json={"trang_thai": "DANG_PHA_CHE"}).status_code == 409


def test_invoice_failure_rolls_back_payment_and_queue(client, monkeypatch):
    don = order(client)
    did = don["DonHangID"]
    pid = payment(client, don)
    original = payments._lap_hoa_don

    def broken(cur, don):
        original(cur, don)
        raise pyodbc.OperationalError("Test invoice failure")

    with monkeypatch.context() as m:
        m.setattr(payments, "_lap_hoa_don", broken)
        assert client.post(f"/api/v1/payments/{pid}/confirm", json={}).status_code == 503
    assert detail(client, did)["TrangThai"] == "MOI"
    assert client.get(f"/api/v1/payments/{pid}").json["data"]["TrangThai"] == "CHO_XAC_NHAN"
    assert client.get(f"/api/v1/orders/{did}/invoice").status_code == 404
    assert client.post(f"/api/v1/payments/{pid}/confirm", json={}).status_code == 200
    assert detail(client, did)["TrangThai"] == "CHO_PHA_CHE"


@pytest.mark.parametrize("discount", [False, True])
def test_zero_total_still_requires_cashier_confirmation(client, discount):
    if discount:
        now = datetime.datetime.now()
        r = client.post("/api/v1/promotions", json={
            "ma_khuyen_mai": "PYTESTFREE" + uuid.uuid4().hex[:8].upper(),
            "ten_khuyen_mai": "Pytest Free Checkout", "loai_giam_gia": "PHAN_TRAM",
            "gia_tri_giam": 100,
            "ngay_bat_dau": (now - datetime.timedelta(days=1)).isoformat(timespec="seconds"),
            "ngay_ket_thuc": (now + datetime.timedelta(days=1)).isoformat(timespec="seconds"),
        })
        assert r.status_code == 201, r.json
        don = order(client, ma_khuyen_mai=r.json["data"]["MaKhuyenMai"])
    else:
        r = client.post("/api/v1/menu", json={"ten_mon": "Pytest Free Checkout", "danh_muc_id": dl.DANH_MUC_ID, "gia_ban": 0})
        assert r.status_code == 201
        don = order(client, r.json["data"]["MonID"])
    pid = payment(client, don)
    assert detail(client, don["DonHangID"])["TrangThai"] == "MOI"
    r = client.post(f"/api/v1/payments/{pid}/confirm", json={})
    assert r.status_code == 200, r.json
    assert float(r.json["data"]["HoaDon"]["ThanhTien"]) == 0
    assert detail(client, don["DonHangID"])["TrangThai"] == "CHO_PHA_CHE"
    with client.session_transaction() as session:
        session["quyens"] = [q for q in session["quyens"] if q != "payment.refund"]
    assert client.post(f"/api/v1/orders/{don['DonHangID']}/cancel", json={"ly_do": "Pytest free order"}).status_code == 200


def test_cashier_has_no_pay_later_action_and_non_cashier_cannot_confirm(client):
    html = client.get("/pos").get_data(as_text=True)
    assert 'id="btn-create-pay"' in html
    assert 'id="btn-create"' not in html
    assert "Chỉ tạo đơn, thu sau" not in html
    don = order(client)
    pid = payment(client, don)
    with client.session_transaction() as session:
        session["quyens"] = ["order.manage", "order.view"]
    html = client.get("/pos").get_data(as_text=True)
    assert 'id="btn-create-pay"' not in html
    assert "Ghi nhận gọi món" in html
    assert client.post(f"/api/v1/payments/{pid}/confirm", json={}).status_code == 403
    assert client.patch(f"/api/v1/orders/{don['DonHangID']}/status", json={"trang_thai": "CHO_PHA_CHE"}).status_code == 409


def test_sample_orders_follow_counter_checkout(client):
    from types import SimpleNamespace
    from api.menu import service as menu
    from api.orders import service as orders
    from tao_du_lieu_mau import tao_don_hang

    account = client.get("/api/v1/auth/me").json["data"]
    generated = []
    tracker = SimpleNamespace(them=lambda table, key: generated.append((table, key)))
    tao_don_hang(random.Random(7), tracker, [account], [menu.chi_tiet_mon(dl.MON_ID)], [], 1)
    order_ids = [key for table, key in generated if table == "DonHang"]
    assert order_ids
    for did in order_ids:
        don = orders.chi_tiet_don(did)
        if don["TrangThai"] in ("CHO_PHA_CHE", "DANG_PHA_CHE"):
            assert don["TrangThaiThanhToan"] == "THANH_CONG"
        if don["TrangThai"] == "HOAN_THANH":
            assert don["TrangThaiThanhToan"] in ("THANH_CONG", "HOAN_MOT_PHAN", "DA_HOAN_TIEN")
