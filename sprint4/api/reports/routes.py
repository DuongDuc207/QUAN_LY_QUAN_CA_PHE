"""Routes module reports: bao cao va thong ke (Sprint 4). Tat ca can quyen report.view."""

from functools import wraps

from flask import Blueprint, request, session

from api.reports import service
from api.response import fail, ok

reports_bp = Blueprint("reports", __name__, url_prefix="/api/v1")


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


def _ngay():
    return request.args.get("tu_ngay", ""), request.args.get("den_ngay", "")


# 71. GET /reports/revenue - Doanh thu theo khoang thoi gian (group_by=day|month)
@reports_bp.get("/reports/revenue")
@need_perm("report.view")
def report_revenue():
    return _tra_ve(*service.doanh_thu(*_ngay(), request.args.get("group_by", "day")))


# 72. GET /reports/orders - So luong don hang
@reports_bp.get("/reports/orders")
@need_perm("report.view")
def report_orders():
    return _tra_ve(*service.don_hang(*_ngay()))


# 73. GET /reports/top-products - Mon ban chay (limit, mac dinh 10)
@reports_bp.get("/reports/top-products")
@need_perm("report.view")
def report_top_products():
    return _tra_ve(*service.mon_ban_chay(*_ngay(), request.args.get("limit", 10)))


# 74. GET /reports/payments - Giao dich thanh toan
@reports_bp.get("/reports/payments")
@need_perm("report.view")
def report_payments():
    return _tra_ve(*service.thanh_toan(*_ngay()))


# 75. GET /reports/refunds - Huy don va hoan tien
@reports_bp.get("/reports/refunds")
@need_perm("report.view")
def report_refunds():
    return _tra_ve(*service.huy_va_hoan(*_ngay()))


# 76. GET /reports/inventory - Ton kho
@reports_bp.get("/reports/inventory")
@need_perm("report.view")
def report_inventory():
    return _tra_ve(*service.ton_kho(*_ngay()))


# 77. GET /reports/purchases - Chi phi nhap hang
@reports_bp.get("/reports/purchases")
@need_perm("report.view")
def report_purchases():
    return _tra_ve(*service.nhap_hang(*_ngay()))


# 78. GET /reports/promotions - Hieu qua khuyen mai
@reports_bp.get("/reports/promotions")
@need_perm("report.view")
def report_promotions():
    return _tra_ve(*service.khuyen_mai(*_ngay()))


# 79. GET /reports/overview - Tong quan hoat dong kinh doanh
@reports_bp.get("/reports/overview")
@need_perm("report.view")
def report_overview():
    return _tra_ve(*service.tong_quan(*_ngay()))
