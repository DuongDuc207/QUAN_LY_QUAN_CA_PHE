"""Routes module employees: nhan vien, ca lam viec, lich phan ca (Sprint 4)."""

from functools import wraps

from flask import Blueprint, request, session

from api.employees import service
from api.response import fail, ok

employees_bp = Blueprint("employees", __name__, url_prefix="/api/v1")


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


# 80. GET /employees - Danh sach nhan vien
@employees_bp.get("/employees")
@need_perm("employee.view")
def list_employees():
    data, err = service.danh_sach_nv(
        tu_khoa=request.args.get("q", ""),
        trang_thai=request.args.get("status", ""),
        page=request.args.get("page", 1),
        per_page=request.args.get("per_page", 20),
    )
    return _tra_ve(data, err)


# 81. POST /employees - Tao ho so nhan vien
@employees_bp.post("/employees")
@need_perm("employee.manage")
def create_employee():
    nv, err = service.tao_nv(request.get_json(silent=True))
    return _tra_ve(nv, err, "Tao ho so nhan vien thanh cong", 201)


# 82. GET /employees/<id> - Chi tiet nhan vien (kem lich sap toi)
@employees_bp.get("/employees/<int:nv_id>")
@need_perm("employee.view")
def get_employee(nv_id):
    nv, err = service.chi_tiet_nv(nv_id)
    return _tra_ve(nv, err)


# 83. PUT /employees/<id> - Cap nhat ho so
@employees_bp.put("/employees/<int:nv_id>")
@need_perm("employee.manage")
def update_employee(nv_id):
    nv, err = service.cap_nhat_nv(nv_id, request.get_json(silent=True))
    return _tra_ve(nv, err, "Cap nhat ho so nhan vien thanh cong")


# 84. PATCH /employees/<id>/status - Dang lam / tam nghi / nghi viec
@employees_bp.patch("/employees/<int:nv_id>/status")
@need_perm("employee.manage")
def change_employee_status(nv_id):
    data = request.get_json(silent=True) or {}
    nv, err = service.doi_trang_thai_nv(nv_id, data.get("trang_thai"))
    return _tra_ve(nv, err, "Cap nhat trang thai nhan vien thanh cong")


# 85. GET /shifts - Danh sach ca lam viec
@employees_bp.get("/shifts")
@need_perm("schedule.view")
def list_shifts():
    data, err = service.danh_sach_ca(request.args.get("status", ""))
    return _tra_ve(data, err)


# 86. POST /shifts - Tao ca lam viec
@employees_bp.post("/shifts")
@need_perm("employee.manage")
def create_shift():
    ca, err = service.tao_ca(request.get_json(silent=True))
    return _tra_ve(ca, err, "Tao ca lam viec thanh cong", 201)


# 87. PUT /shifts/<id> - Cap nhat ca lam viec
@employees_bp.put("/shifts/<int:ca_id>")
@need_perm("employee.manage")
def update_shift(ca_id):
    ca, err = service.cap_nhat_ca(ca_id, request.get_json(silent=True))
    return _tra_ve(ca, err, "Cap nhat ca lam viec thanh cong")


# 88. GET /workSchedules - Lich phan ca (khong co quyen xem nhan su: chi thay lich cua minh)
@employees_bp.get("/workSchedules")
@need_perm("schedule.view")
def list_work_schedules():
    xem_het = "employee.view" in (session.get("quyens") or [])
    data, err = service.danh_sach_lich(
        tu_ngay=request.args.get("tu_ngay", ""),
        den_ngay=request.args.get("den_ngay", ""),
        nhan_vien_id=request.args.get("nhan_vien_id", "") if xem_het else "",
        ca_id=request.args.get("ca_lam_viec_id", ""),
        trang_thai=request.args.get("status", ""),
        tai_khoan_id=None if xem_het else session["tai_khoan_id"],
    )
    return _tra_ve(data, err)


# 89. POST /workSchedules - Phan cong nhan vien vao ca
@employees_bp.post("/workSchedules")
@need_perm("employee.manage")
def create_work_schedule():
    lich, err = service.tao_lich(request.get_json(silent=True))
    return _tra_ve(lich, err, "Phan cong thanh cong", 201)


# 90. PUT /workSchedules/<id> - Cap nhat lich (doi ca/ngay, cham cong, huy)
@employees_bp.put("/workSchedules/<int:lich_id>")
@need_perm("employee.manage")
def update_work_schedule(lich_id):
    lich, err = service.cap_nhat_lich(lich_id, request.get_json(silent=True))
    return _tra_ve(lich, err, "Cap nhat lich lam viec thanh cong")
