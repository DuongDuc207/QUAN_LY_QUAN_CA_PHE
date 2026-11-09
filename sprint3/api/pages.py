import datetime
import decimal

from flask import Blueprint, render_template, session, redirect, url_for

pages_bp = Blueprint("pages", __name__)


def _current_user():
    return {
        "ho_ten": session.get("ho_ten"),
        "email": session.get("email"),
        "ten_vai_tro": session.get("ten_vai_tro"),
        "quyens": session.get("quyens", []),
    }


# ---------- Bo loc hien thi cho template ----------
@pages_bp.app_template_filter("tien")
def dinh_dang_tien(value):
    """95000 -> "95.000 ₫"."""
    try:
        so = decimal.Decimal(value)
    except (decimal.InvalidOperation, TypeError, ValueError):
        return "—"
    return f"{so:,.0f}".replace(",", ".") + " ₫"


@pages_bp.app_template_filter("thoi_gian")
def dinh_dang_thoi_gian(value):
    if isinstance(value, datetime.datetime):
        return value.strftime("%H:%M %d/%m/%Y")
    return "—"


def _trang_can_quyen(template, active, quyen):
    """Chua dang nhap -> /login; thieu quyen -> ve trang chu (khong de gap loi tu choi)."""
    if not session.get("tai_khoan_id"):
        return redirect(url_for("pages.login_page"))
    if quyen not in (session.get("quyens") or []):
        return redirect(url_for("pages.dashboard"))
    return render_template(template, user=_current_user(), active=active)


@pages_bp.get("/login")
def login_page():
    if session.get("tai_khoan_id"):
        return redirect(url_for("pages.dashboard"))
    return render_template("login.html")


@pages_bp.get("/dashboard")
def dashboard():
    if not session.get("tai_khoan_id"):
        return redirect(url_for("pages.login_page"))
    return render_template("dashboard.html", user=_current_user(), active="dashboard")


@pages_bp.get("/accounts")
def accounts_page():
    if not session.get("tai_khoan_id"):
        return redirect(url_for("pages.login_page"))
    return render_template("accounts/list.html", user=_current_user(), active="accounts")


@pages_bp.get("/roles")
def roles_page():
    if not session.get("tai_khoan_id"):
        return redirect(url_for("pages.login_page"))
    return render_template("roles/list.html", user=_current_user(), active="roles")


@pages_bp.get("/menu")
def menu_page():
    if not session.get("tai_khoan_id"):
        return redirect(url_for("pages.login_page"))
    return render_template("menu/list.html", user=_current_user(), active="menu")


@pages_bp.get("/pos")
def pos_page():
    if not session.get("tai_khoan_id"):
        return redirect(url_for("pages.login_page"))
    # Khong co quyen ban hang thi ve trang chu, khong de gap loi tu choi.
    if "order.manage" not in (session.get("quyens") or []):
        return redirect(url_for("pages.dashboard"))
    return render_template("orders/pos.html", user=_current_user(), active="pos")


@pages_bp.get("/orders")
def orders_page():
    if not session.get("tai_khoan_id"):
        return redirect(url_for("pages.login_page"))
    if "order.view" not in (session.get("quyens") or []):
        return redirect(url_for("pages.dashboard"))
    return render_template("orders/list.html", user=_current_user(), active="orders")


# ---------- Sprint 3: kho, cong thuc, nha cung cap, nhap hang ----------
@pages_bp.get("/inventory")
def inventory_page():
    return _trang_can_quyen("inventory/list.html", "inventory", "inventory.view")


@pages_bp.get("/recipes")
def recipes_page():
    return _trang_can_quyen("inventory/recipes.html", "recipes", "inventory.view")


@pages_bp.get("/suppliers")
def suppliers_page():
    return _trang_can_quyen("suppliers/list.html", "suppliers", "supplier.view")


@pages_bp.get("/purchases")
def purchases_page():
    return _trang_can_quyen("suppliers/purchases.html", "purchases", "supplier.view")
