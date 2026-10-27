"""Routes module suppliers: nha cung cap va phieu nhap hang (Sprint 3)."""

from functools import wraps

from flask import Blueprint, request, session

from api.response import fail, ok
from api.suppliers import service

suppliers_bp = Blueprint("suppliers", __name__, url_prefix="/api/v1")


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


# 54. GET /suppliers - Danh sach nha cung cap (tim, loc, phan trang)
@suppliers_bp.get("/suppliers")
@need_perm("supplier.view")
def list_suppliers():
    data, err = service.danh_sach_ncc(
        tu_khoa=request.args.get("q", ""),
        trang_thai=request.args.get("status", ""),
        page=request.args.get("page", 1),
        per_page=request.args.get("per_page", 20),
    )
    return _tra_ve(data, err)


# 55. POST /suppliers - Them nha cung cap
@suppliers_bp.post("/suppliers")
@need_perm("supplier.manage")
def create_supplier():
    ncc, err = service.tao_ncc(request.get_json(silent=True))
    return _tra_ve(ncc, err, "Them nha cung cap thanh cong", 201)


# 56. GET /suppliers/<id> - Chi tiet nha cung cap
@suppliers_bp.get("/suppliers/<int:ncc_id>")
@need_perm("supplier.view")
def get_supplier(ncc_id):
    ncc, err = service.chi_tiet_ncc(ncc_id)
    return _tra_ve(ncc, err)


# 57. PUT /suppliers/<id> - Cap nhat nha cung cap (ke ca ngung hop tac)
@suppliers_bp.put("/suppliers/<int:ncc_id>")
@need_perm("supplier.manage")
def update_supplier(ncc_id):
    ncc, err = service.cap_nhat_ncc(ncc_id, request.get_json(silent=True))
    return _tra_ve(ncc, err, "Cap nhat nha cung cap thanh cong")


# 58. GET /purchase-receipts - Danh sach phieu nhap
@suppliers_bp.get("/purchase-receipts")
@need_perm("supplier.view")
def list_purchase_receipts():
    data, err = service.danh_sach_phieu(
        trang_thai=request.args.get("status", ""),
        ncc_id=request.args.get("nha_cung_cap_id", ""),
        tu_khoa=request.args.get("q", ""),
        tu_ngay=request.args.get("tu_ngay", ""),
        den_ngay=request.args.get("den_ngay", ""),
        page=request.args.get("page", 1),
        per_page=request.args.get("per_page", 20),
    )
    return _tra_ve(data, err)


# 59. POST /purchase-receipts - Tao phieu nhap (trang thai NHAP, chua doi ton kho)
@suppliers_bp.post("/purchase-receipts")
@need_perm("supplier.manage")
def create_purchase_receipt():
    phieu, err = service.tao_phieu(session["tai_khoan_id"], request.get_json(silent=True))
    return _tra_ve(phieu, err, "Tao phieu nhap thanh cong", 201)


# 60. GET /purchase-receipts/<id> - Chi tiet phieu nhap
@suppliers_bp.get("/purchase-receipts/<int:phieu_id>")
@need_perm("supplier.view")
def get_purchase_receipt(phieu_id):
    phieu, err = service.chi_tiet_phieu(phieu_id)
    return _tra_ve(phieu, err)


# 61. PUT /purchase-receipts/<id> - Sua phieu nhap khi con o trang thai NHAP
@suppliers_bp.put("/purchase-receipts/<int:phieu_id>")
@need_perm("supplier.manage")
def update_purchase_receipt(phieu_id):
    phieu, err = service.cap_nhat_phieu(phieu_id, request.get_json(silent=True))
    return _tra_ve(phieu, err, "Cap nhat phieu nhap thanh cong")


# 62. POST /purchase-receipts/<id>/confirm - Xac nhan nhan hang, cong ton kho
@suppliers_bp.post("/purchase-receipts/<int:phieu_id>/confirm")
@need_perm("purchase.confirm")
def confirm_purchase_receipt(phieu_id):
    phieu, err = service.xac_nhan_phieu(phieu_id, session["tai_khoan_id"])
    return _tra_ve(phieu, err, "Xac nhan nhan hang thanh cong")


# 63. POST /purchase-receipts/<id>/cancel - Huy phieu (phieu da nhan: can purchase.confirm)
@suppliers_bp.post("/purchase-receipts/<int:phieu_id>/cancel")
@need_perm("supplier.manage")
def cancel_purchase_receipt(phieu_id):
    data = request.get_json(silent=True)
    data = data if isinstance(data, dict) else {}
    phieu, err = service.huy_phieu(
        phieu_id,
        session["tai_khoan_id"],
        data.get("ly_do"),
        duoc_huy_da_nhan="purchase.confirm" in (session.get("quyens") or []),
    )
    return _tra_ve(phieu, err, "Huy phieu nhap thanh cong")
