"""Routes module payments: thanh toan, hoa don, hoan tien (Sprint 2)."""

from functools import wraps

from flask import Blueprint, render_template, request, session

from api.payments import service
from api.response import fail, ok

payments_bp = Blueprint("payments", __name__, url_prefix="/api/v1")


def need_perm(ten_quyen):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("tai_khoan_id"):
                return fail("Chua dang nhap", 401)
            if ten_quyen not in (session.get("quyens") or []):
                return fail("Khong co quyen thuc hien chuc nang nay", 403)
            return fn(*args, **kwargs)

        return wrapper

    return deco


def _tra_ve(data, err, message="Thanh cong", status=200):
    if err:
        return fail(err[0], err[1])
    return ok(data, message, status)


# 31. POST /payments - Tao giao dich (cho xac nhan)
@payments_bp.post("/payments")
@need_perm("payment.manage")
def create_payment():
    data = request.get_json(silent=True) or {}
    tt, err = service.tao_thanh_toan(
        data.get("don_hang_id"),
        data.get("phuong_thuc"),
        so_tien=data.get("so_tien"),
        ma_giao_dich=data.get("ma_giao_dich"),
    )
    return _tra_ve(tt, err, "Tao giao dich thanh toan thanh cong", 201)


# 32. GET /payments/<id> - Chi tiet thanh toan
@payments_bp.get("/payments/<int:thanh_toan_id>")
@need_perm("order.view")
def get_payment(thanh_toan_id):
    tt = service.chi_tiet_thanh_toan(thanh_toan_id)
    if not tt:
        return fail("Giao dich thanh toan khong ton tai", 404)
    return ok(tt)


# 33. GET /orders/<id>/payments - Lich su thanh toan cua don
@payments_bp.get("/orders/<int:don_hang_id>/payments")
@need_perm("order.view")
def list_order_payments(don_hang_id):
    data, err = service.lich_su_thanh_toan(don_hang_id)
    return _tra_ve(data, err)


# 34. POST /payments/<id>/confirm - Xac nhan ket qua (thanh cong -> lap hoa don)
@payments_bp.post("/payments/<int:thanh_toan_id>/confirm")
@need_perm("payment.manage")
def confirm_payment(thanh_toan_id):
    data = request.get_json(silent=True) or {}
    ket_qua, err = service.xac_nhan_thanh_toan(
        thanh_toan_id,
        thanh_cong=data.get("thanh_cong", True) is not False,
        ma_giao_dich=data.get("ma_giao_dich"),
    )
    return _tra_ve(ket_qua, err, "Xac nhan thanh toan thanh cong")


# 35. POST /payments/<id>/refund - Hoan tien (mot phan hoac toan bo)
@payments_bp.post("/payments/<int:thanh_toan_id>/refund")
@need_perm("payment.refund")
def refund_payment(thanh_toan_id):
    data = request.get_json(silent=True) or {}
    tt, err = service.hoan_tien(
        thanh_toan_id,
        data.get("so_tien"),
        data.get("ly_do"),
        ma_giao_dich_hoan=data.get("ma_giao_dich_hoan"),
    )
    return _tra_ve(tt, err, "Hoan tien thanh cong")


# 36. GET /invoices/<id> - Xem hoa don
@payments_bp.get("/invoices/<int:hoa_don_id>")
@need_perm("order.view")
def get_invoice(hoa_don_id):
    hd = service.chi_tiet_hoa_don(hoa_don_id)
    if not hd:
        return fail("Hoa don khong ton tai", 404)
    return ok(hd)


# 37. GET /orders/<id>/invoice - Hoa don cua don hang
@payments_bp.get("/orders/<int:don_hang_id>/invoice")
@need_perm("order.view")
def get_order_invoice(don_hang_id):
    hd, err = service.hoa_don_cua_don(don_hang_id)
    return _tra_ve(hd, err)


# 38. GET /invoices/<id>/print - Trang hoa don de in (HTML).
# Mo trong tab moi nen loi cung tra trang HTML than thien thay vi JSON.
@payments_bp.get("/invoices/<int:hoa_don_id>/print")
def print_invoice(hoa_don_id):
    if not session.get("tai_khoan_id"):
        return render_template("invoices/print.html", loi="Phiên làm việc đã kết thúc. Vui lòng đăng nhập lại."), 401
    if "order.view" not in (session.get("quyens") or []):
        return render_template("invoices/print.html", loi="Bạn không có quyền xem hoá đơn."), 403
    hd = service.chi_tiet_hoa_don(hoa_don_id)
    if not hd:
        return render_template("invoices/print.html", loi="Không tìm thấy hoá đơn."), 404
    return render_template("invoices/print.html", hd=hd)
