"""Routes module menu: danh muc va thuc don (Sprint 1, Nguoi 2)."""

from functools import wraps

from flask import Blueprint, request, session

from api.menu import service
from api.response import fail, ok

menu_bp = Blueprint("menu", __name__, url_prefix="/api/v1")


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("tai_khoan_id"):
            return fail("Chua dang nhap", 401)
        return fn(*args, **kwargs)

    return wrapper


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


# ---------- Danh muc ----------
# 12. GET /categories - Danh sach danh muc
@menu_bp.get("/categories")
@login_required
def list_categories():
    all_param = request.args.get("all", "").lower() in ("1", "true")
    return ok(service.danh_sach_danh_muc(chi_hien_thi=not all_param))


# 13. POST /categories - Them danh muc
@menu_bp.post("/categories")
@need_perm("menu.manage")
def create_category():
    data = request.get_json(silent=True) or {}
    dm, err = service.them_danh_muc(data.get("ten_danh_muc"), data.get("mo_ta"))
    if err:
        return fail(err, 400)
    return ok(dm, "Them danh muc thanh cong", 201)


# 14. PUT /categories/<id> - Sua danh muc
@menu_bp.put("/categories/<int:danh_muc_id>")
@need_perm("menu.manage")
def update_category(danh_muc_id):
    data = request.get_json(silent=True) or {}
    dm, err = service.sua_danh_muc(
        danh_muc_id,
        ten=data.get("ten_danh_muc"),
        mo_ta=data.get("mo_ta"),
        trang_thai=data.get("trang_thai"),
    )
    if err:
        status = 404 if "khong ton tai" in err.lower() else 400
        return fail(err, status)
    return ok(dm, "Cap nhat danh muc thanh cong")


# 15. DELETE /categories/<id> - Xoa danh muc (khi khong con mon)
@menu_bp.delete("/categories/<int:danh_muc_id>")
@need_perm("menu.manage")
def delete_category(danh_muc_id):
    dm, err = service.xoa_danh_muc(danh_muc_id)
    if err:
        status = 404 if "khong ton tai" in err.lower() else 400
        return fail(err, status)
    return ok(dm, "Xoa danh muc thanh cong")


# ---------- Mon ----------
# 16. GET /menu - Danh sach mon (loc, phan trang)
@menu_bp.get("/menu")
@login_required
def list_menu():
    data = service.danh_sach_mon(
        danh_muc_id=request.args.get("danh_muc_id", type=int),
        chi_dang_ban=request.args.get("dang_ban", "").lower() in ("1", "true"),
        tu_khoa=request.args.get("q", "").strip(),
        page=request.args.get("page", 1),
        per_page=request.args.get("per_page", 20),
    )
    return ok(data)


# 21. GET /menu/search - Tim kiem mon (khai bao truoc route <mon_id>)
@menu_bp.get("/menu/search")
@login_required
def search_menu():
    return ok(service.tim_kiem_mon(request.args.get("q", "")))


# 17. GET /menu/<id> - Chi tiet mon
@menu_bp.get("/menu/<int:mon_id>")
@login_required
def get_menu_item(mon_id):
    mon = service.chi_tiet_mon(mon_id)
    if not mon:
        return fail("Mon khong ton tai", 404)
    return ok(mon)


# 18. POST /menu - Them mon
@menu_bp.post("/menu")
@need_perm("menu.manage")
def create_menu_item():
    data = request.get_json(silent=True) or {}
    mon, err = service.them_mon(
        ten_mon=data.get("ten_mon"),
        danh_muc_id=data.get("danh_muc_id"),
        gia_ban=data.get("gia_ban"),
        mo_ta=data.get("mo_ta"),
        hinh_anh=data.get("hinh_anh"),
    )
    if err:
        return fail(err, 400)
    return ok(mon, "Them mon thanh cong", 201)


# 19. PUT /menu/<id> - Sua mon
@menu_bp.put("/menu/<int:mon_id>")
@need_perm("menu.manage")
def update_menu_item(mon_id):
    data = request.get_json(silent=True) or {}
    mon, err = service.sua_mon(
        mon_id,
        ten_mon=data.get("ten_mon"),
        danh_muc_id=data.get("danh_muc_id"),
        gia_ban=data.get("gia_ban"),
        mo_ta=data.get("mo_ta"),
        hinh_anh=data.get("hinh_anh"),
    )
    if err:
        status = 404 if "khong ton tai" in err.lower() else 400
        return fail(err, status)
    return ok(mon, "Cap nhat mon thanh cong")


# 20. PATCH /menu/<id>/status - Bat/ngung kinh doanh
@menu_bp.patch("/menu/<int:mon_id>/status")
@need_perm("menu.manage")
def change_menu_status(mon_id):
    data = request.get_json(silent=True) or {}
    if "dang_ban" not in data:
        return fail("Thieu truong dang_ban (true/false)", 400)
    mon, err = service.doi_trang_thai_mon(mon_id, bool(data.get("dang_ban")))
    if err:
        return fail(err, 404)
    return ok(mon, "Cap nhat trang thai mon thanh cong")
