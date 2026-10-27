"""Routes module inventory: nguyen lieu, ton kho, cong thuc pha che (Sprint 3)."""

from functools import wraps

from flask import Blueprint, request, session

from api.inventory import service
from api.response import fail, ok

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/v1")


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


def _body():
    """Than JSON la object; mang / chuoi / rong deu thanh {} de service tra 400 thay vi 500."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


# 39. GET /ingredients - Danh sach nguyen lieu (tim kiem, loc, phan trang)
@inventory_bp.get("/ingredients")
@need_perm("inventory.view")
def list_ingredients():
    data, err = service.danh_sach_nguyen_lieu(
        q=request.args.get("q", ""),
        status=request.args.get("status", ""),
        page=request.args.get("page", 1),
        per_page=request.args.get("per_page", 20),
    )
    return _tra_ve(data, err)


# 40. POST /ingredients - Them nguyen lieu (ton ban dau ghi qua so cai)
@inventory_bp.post("/ingredients")
@need_perm("inventory.manage")
def create_ingredient():
    data, err = service.tao_nguyen_lieu(session["tai_khoan_id"], _body())
    return _tra_ve(data, err, "Them nguyen lieu thanh cong", 201)


# 41. GET /ingredients/<id> - Chi tiet nguyen lieu
@inventory_bp.get("/ingredients/<int:nguyen_lieu_id>")
@need_perm("inventory.view")
def get_ingredient(nguyen_lieu_id):
    data, err = service.chi_tiet_nguyen_lieu(nguyen_lieu_id)
    return _tra_ve(data, err)


# 42. PUT /ingredients/<id> - Cap nhat nguyen lieu (khong doi ton)
@inventory_bp.put("/ingredients/<int:nguyen_lieu_id>")
@need_perm("inventory.manage")
def update_ingredient(nguyen_lieu_id):
    data, err = service.cap_nhat_nguyen_lieu(nguyen_lieu_id, _body())
    return _tra_ve(data, err, "Cap nhat nguyen lieu thanh cong")


# 43. PATCH /ingredients/<id>/status - Bat / ngung su dung
@inventory_bp.patch("/ingredients/<int:nguyen_lieu_id>/status")
@need_perm("inventory.manage")
def change_ingredient_status(nguyen_lieu_id):
    data, err = service.doi_trang_thai_nguyen_lieu(nguyen_lieu_id, _body())
    return _tra_ve(data, err, "Cap nhat trang thai nguyen lieu thanh cong")


# 44. GET /inventory - Danh sach ton kho
@inventory_bp.get("/inventory")
@need_perm("inventory.view")
def list_inventory():
    data, err = service.danh_sach_ton_kho(
        q=request.args.get("q", ""),
        tinh_trang=request.args.get("tinh_trang", ""),
        status=request.args.get("status", ""),
        page=request.args.get("page", 1),
        per_page=request.args.get("per_page", 20),
    )
    return _tra_ve(data, err)


# 45. GET /inventory/low-stock - Nguyen lieu het / sap het
@inventory_bp.get("/inventory/low-stock")
@need_perm("inventory.view")
def low_stock():
    data, err = service.danh_sach_sap_het()
    return _tra_ve(data, err)


# 46. GET /inventory/transactions - Lich su giao dich kho
@inventory_bp.get("/inventory/transactions")
@need_perm("inventory.view")
def inventory_transactions():
    data, err = service.lich_su_kho(
        nguyen_lieu_id=request.args.get("nguyen_lieu_id", ""),
        loai=request.args.get("loai", ""),
        tu_ngay=request.args.get("tu_ngay", ""),
        den_ngay=request.args.get("den_ngay", ""),
        page=request.args.get("page", 1),
        per_page=request.args.get("per_page", 20),
    )
    return _tra_ve(data, err)


# 47. POST /inventory/adjustments - Kiem ke / dieu chinh ton co ly do
@inventory_bp.post("/inventory/adjustments")
@need_perm("inventory.manage")
def adjust_inventory():
    data, err = service.dieu_chinh_ton_kho(session["tai_khoan_id"], _body())
    return _tra_ve(data, err, "Dieu chinh ton kho thanh cong", 201)


# 48. POST /inventory/issues - Xuat kho (hao hut, hu hong)
@inventory_bp.post("/inventory/issues")
@need_perm("inventory.manage")
def issue_inventory():
    data, err = service.xuat_kho(session["tai_khoan_id"], _body())
    return _tra_ve(data, err, "Xuat kho thanh cong", 201)


# 49. GET /inventory/ingredients/<id> - Ton kho 1 nguyen lieu + giao dich gan nhat
@inventory_bp.get("/inventory/ingredients/<int:nguyen_lieu_id>")
@need_perm("inventory.view")
def inventory_of_ingredient(nguyen_lieu_id):
    data, err = service.ton_kho_nguyen_lieu(nguyen_lieu_id)
    return _tra_ve(data, err)


# 50. GET /recipes/<mon_id> - Xem cong thuc
@inventory_bp.get("/recipes/<int:mon_id>")
@need_perm("inventory.view")
def get_recipe(mon_id):
    data, err = service.xem_cong_thuc(mon_id)
    return _tra_ve(data, err)


# 51. PUT /recipes/<mon_id> - Thay ca cong thuc
@inventory_bp.put("/recipes/<int:mon_id>")
@need_perm("inventory.manage")
def save_recipe(mon_id):
    data, err = service.luu_cong_thuc(session["tai_khoan_id"], mon_id, _body())
    return _tra_ve(data, err, "Luu cong thuc thanh cong")


# 52. GET /recipes/<mon_id>/history - Lich su thay doi cong thuc
@inventory_bp.get("/recipes/<int:mon_id>/history")
@need_perm("inventory.view")
def recipe_history(mon_id):
    data, err = service.lich_su_cong_thuc(
        mon_id,
        page=request.args.get("page", 1),
        per_page=request.args.get("per_page", 20),
    )
    return _tra_ve(data, err)


# 53. POST /inventory/consumptions - Tru kho theo cong thuc cua don
@inventory_bp.post("/inventory/consumptions")
@need_perm("order.manage")
def consume_for_order():
    data, err = service.tru_kho_theo_don(session["tai_khoan_id"], _body())
    return _tra_ve(data, err, "Tru kho theo don thanh cong", 201)
