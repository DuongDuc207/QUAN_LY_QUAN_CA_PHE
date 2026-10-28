"""Routes module auth: dang nhap, phan quyen, quan ly tai khoan (Sprint 1, Nguoi 1)."""

from functools import wraps

from flask import Blueprint, request, session

from api.auth import service
from api.response import fail, ok

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1")


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


def _save_session(user):
    session["tai_khoan_id"] = user["TaiKhoanID"]
    session["ho_ten"] = user["HoTen"]
    session["email"] = user["Email"]
    session["ten_vai_tro"] = user.get("TenVaiTro")
    session["quyens"] = user.get("Quyens", [])


# 1. POST /auth/login - Dang nhap
@auth_bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    if not email or not password:
        return fail("Email va mat khau la bat buoc", 400)
    user, err = service.dang_nhap(email, password)
    if err:
        return fail(err, 401)
    _save_session(user)
    return ok(user, "Dang nhap thanh cong")


# 2. POST /auth/logout - Dang xuat
@auth_bp.post("/auth/logout")
def logout():
    session.clear()
    return ok(message="Dang xuat thanh cong")


# 3. GET /auth/me - Thong tin tai khoan hien tai
@auth_bp.get("/auth/me")
@login_required
def me():
    user = service.lay_thong_tin_hien_tai(session["tai_khoan_id"])
    if not user:
        session.clear()
        return fail("Tai khoan khong ton tai", 404)
    _save_session(user)  # refresh quyen moi nhat
    return ok(user)


# 4. GET /accounts - Danh sach tai khoan
@auth_bp.get("/accounts")
@need_perm("account.view")
def list_accounts():
    data = service.danh_sach_tai_khoan(
        tu_khoa=request.args.get("q", "").strip(),
        trang_thai=request.args.get("status", "").strip().upper(),
    )
    return ok(data)


# 5. POST /accounts - Tao tai khoan
@auth_bp.post("/accounts")
@need_perm("account.create")
def create_account():
    data = request.get_json(silent=True) or {}
    user, err = service.tao_tai_khoan(
        ho_ten=(data.get("ho_ten") or "").strip(),
        email=(data.get("email") or "").strip(),
        password=data.get("mat_khau") or "",
        vai_tro_id=data.get("vai_tro_id"),
        so_dien_thoai=(data.get("so_dien_thoai") or "").strip() or None,
    )
    if err:
        return fail(err, 400)
    return ok(user, "Tao tai khoan thanh cong", 201)


# 6. GET /accounts/<id> - Chi tiet tai khoan
@auth_bp.get("/accounts/<int:tai_khoan_id>")
@need_perm("account.view")
def get_account(tai_khoan_id):
    user = service.chi_tiet_tai_khoan(tai_khoan_id)
    if not user:
        return fail("Tai khoan khong ton tai", 404)
    return ok(user)


# 7. PUT /accounts/<id> - Cap nhat tai khoan
@auth_bp.put("/accounts/<int:tai_khoan_id>")
@need_perm("account.update")
def update_account(tai_khoan_id):
    data = request.get_json(silent=True) or {}
    user, err = service.cap_nhat_tai_khoan(
        tai_khoan_id,
        ho_ten=data.get("ho_ten"),
        vai_tro_id=data.get("vai_tro_id"),
        so_dien_thoai=data.get("so_dien_thoai"),
        mat_khau=data.get("mat_khau"),
    )
    if err:
        return fail(err, 400)
    return ok(user, "Cap nhat tai khoan thanh cong")


# 8. PATCH /accounts/<id>/status - Khoa/mo tai khoan
@auth_bp.patch("/accounts/<int:tai_khoan_id>/status")
@need_perm("account.lock")
def change_account_status(tai_khoan_id):
    data = request.get_json(silent=True) or {}
    trang_thai = (data.get("trang_thai") or "").strip().upper()
    user, err = service.doi_trang_thai_tai_khoan(
        tai_khoan_id, trang_thai, self_id=session.get("tai_khoan_id")
    )
    if err:
        return fail(err, 400)
    return ok(user, "Cap nhat trang thai thanh cong")


# 9. GET /roles - Danh sach vai tro
@auth_bp.get("/roles")
@need_perm("role.manage")
def list_roles():
    return ok(service.danh_sach_vai_tro())


# 10. GET /permissions - Danh sach quyen
@auth_bp.get("/permissions")
@need_perm("role.manage")
def list_permissions():
    return ok(service.danh_sach_quyen())


# 11. PUT /roles/<id>/permissions - Cap nhat quyen cua vai tro
@auth_bp.put("/roles/<int:vai_tro_id>/permissions")
@need_perm("role.manage")
def update_role_permissions(vai_tro_id):
    data = request.get_json(silent=True) or {}
    role, err = service.cap_nhat_quyen_cua_vai_tro(vai_tro_id, data.get("quyen_ids") or [])
    if err:
        return fail(err, 400)
    return ok(role, "Cap nhat quyen thanh cong")
