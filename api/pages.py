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
