"""Routes module promotions: chuong trinh khuyen mai (Sprint 4)."""

from functools import wraps

from flask import Blueprint, request, session

from api.promotions import service
from api.response import fail, ok

promotions_bp = Blueprint("promotions", __name__, url_prefix="/api/v1")


def need_perm(*ten_quyen):
    """Can it nhat 1 trong cac quyen."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("tai_khoan_id"):
                return fail("Chua dang nhap", 401)
            quyens = session.get("quyens") or []
            if not any(q in quyens for q in ten_quyen):
                return fail("Khong co quyen thuc hien chuc nang nay", 403)
            return fn(*args, **kwargs)

        return wrapper

    return deco


def _tra_ve(data, err, message="Thanh cong", status=200):
    if err:
        return fail(err[0], err[1])
    return ok(data, message, status)


# 64. GET /promotions - Danh sach khuyen mai (tim, loc tinh trang, phan trang)
@promotions_bp.get("/promotions")
@need_perm("promotion.view")
def list_promotions():
    data, err = service.danh_sach(
        tu_khoa=request.args.get("q", ""),
        tinh_trang=request.args.get("status", ""),
        page=request.args.get("page", 1),
        per_page=request.args.get("per_page", 20),
    )
    return _tra_ve(data, err)


# 65. POST /promotions - Tao chuong trinh khuyen mai
@promotions_bp.post("/promotions")
@need_perm("promotion.manage")
def create_promotion():
    km, err = service.tao(request.get_json(silent=True))
    return _tra_ve(km, err, "Tao khuyen mai thanh cong", 201)


# 69. POST /promotions/validate - Kiem tra ma (dat truoc route co <id>)
@promotions_bp.post("/promotions/validate")
@need_perm("promotion.view", "order.manage")
def validate_promotion():
    data, err = service.kiem_tra_ma(request.get_json(silent=True))
    return _tra_ve(data, err, "Ma khuyen mai hop le")


# 66. GET /promotions/<id> - Chi tiet khuyen mai
@promotions_bp.get("/promotions/<int:km_id>")
@need_perm("promotion.view")
def get_promotion(km_id):
    km, err = service.chi_tiet(km_id)
    return _tra_ve(km, err)


# 67. PUT /promotions/<id> - Cap nhat khuyen mai
@promotions_bp.put("/promotions/<int:km_id>")
@need_perm("promotion.manage")
def update_promotion(km_id):
    km, err = service.cap_nhat(km_id, request.get_json(silent=True))
    return _tra_ve(km, err, "Cap nhat khuyen mai thanh cong")


# 68. PATCH /promotions/<id>/status - Bat / tat khuyen mai
@promotions_bp.patch("/promotions/<int:km_id>/status")
@need_perm("promotion.manage")
def change_promotion_status(km_id):
    data = request.get_json(silent=True) or {}
    km, err = service.doi_trang_thai(km_id, data.get("trang_thai"))
    return _tra_ve(km, err, "Cap nhat trang thai khuyen mai thanh cong")


# 70. GET /promotions/<id>/usage - Thong ke luot su dung
@promotions_bp.get("/promotions/<int:km_id>/usage")
@need_perm("promotion.view")
def promotion_usage(km_id):
    data, err = service.thong_ke_su_dung(
        km_id, request.args.get("page", 1), request.args.get("per_page", 20)
    )
    return _tra_ve(data, err)
