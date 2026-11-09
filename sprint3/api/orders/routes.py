"""Routes module orders: don hang va mon trong don (Sprint 2)."""

from functools import wraps

from flask import Blueprint, request, session

from api.orders import service
from api.response import fail, ok

orders_bp = Blueprint("orders", __name__, url_prefix="/api/v1")


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


# 22. GET /orders - Danh sach don hang (loc, phan trang)
@orders_bp.get("/orders")
@need_perm("order.view")
def list_orders():
    data, err = service.danh_sach_don(
        trang_thai=request.args.get("status", "").strip().upper(),
        tu_khoa=request.args.get("q", "").strip(),
        ngay=request.args.get("date", "").strip(),
        thanh_toan=request.args.get("paid", "").strip().lower(),
        page=request.args.get("page", 1),
        per_page=request.args.get("per_page", 20),
    )
    return _tra_ve(data, err)


# 23. POST /orders - Tao don hang (it nhat 1 mon)
@orders_bp.post("/orders")
@need_perm("order.manage")
def create_order():
    data = request.get_json(silent=True) or {}
    don, err = service.tao_don(session["tai_khoan_id"], data.get("items"), data.get("ghi_chu"))
    return _tra_ve(don, err, "Tao don hang thanh cong", 201)


# 24. GET /orders/<id> - Chi tiet don hang
@orders_bp.get("/orders/<int:don_hang_id>")
@need_perm("order.view")
def get_order(don_hang_id):
    don = service.chi_tiet_don(don_hang_id)
    if not don:
        return fail("Don hang khong ton tai", 404)
    return ok(don)


# 25. PUT /orders/<id>/items - Thay ca danh sach mon
@orders_bp.put("/orders/<int:don_hang_id>/items")
@need_perm("order.manage")
def replace_order_items(don_hang_id):
    data = request.get_json(silent=True) or {}
    don, err = service.cap_nhat_danh_sach_mon(don_hang_id, data.get("items"))
    return _tra_ve(don, err, "Cap nhat mon trong don thanh cong")


# 26. PATCH /orders/<id>/status - Chuyen buoc xu ly
@orders_bp.patch("/orders/<int:don_hang_id>/status")
@need_perm("order.manage")
def change_order_status(don_hang_id):
    data = request.get_json(silent=True) or {}
    don, err = service.doi_trang_thai_don(don_hang_id, data.get("trang_thai"))
    return _tra_ve(don, err, "Cap nhat trang thai don thanh cong")


# 27. POST /orders/<id>/cancel - Huy don + ly do (hoan tien neu da thu)
@orders_bp.post("/orders/<int:don_hang_id>/cancel")
@need_perm("order.cancel")
def cancel_order(don_hang_id):
    data = request.get_json(silent=True) or {}
    don, err = service.huy_don(
        don_hang_id,
        data.get("ly_do"),
        hoan_tien=bool(data.get("hoan_tien")),
        duoc_hoan_tien="payment.refund" in (session.get("quyens") or []),
    )
    return _tra_ve(don, err, "Huy don hang thanh cong")


# 28. GET /orders/<id>/items - Danh sach mon trong don
@orders_bp.get("/orders/<int:don_hang_id>/items")
@need_perm("order.view")
def list_order_items(don_hang_id):
    items, err = service.danh_sach_mon_cua_don(don_hang_id)
    return _tra_ve(items, err)


# 29. POST /orders/<id>/items - Them mon vao don
@orders_bp.post("/orders/<int:don_hang_id>/items")
@need_perm("order.manage")
def add_order_item(don_hang_id):
    data = request.get_json(silent=True) or {}
    don, err = service.them_mon_vao_don(don_hang_id, data)
    return _tra_ve(don, err, "Them mon vao don thanh cong", 201)


# 30. DELETE /orders/<id>/items/<chi_tiet_id> - Xoa mon khoi don
@orders_bp.delete("/orders/<int:don_hang_id>/items/<int:chi_tiet_id>")
@need_perm("order.manage")
def delete_order_item(don_hang_id, chi_tiet_id):
    don, err = service.xoa_mon_khoi_don(don_hang_id, chi_tiet_id)
    return _tra_ve(don, err, "Xoa mon khoi don thanh cong")
