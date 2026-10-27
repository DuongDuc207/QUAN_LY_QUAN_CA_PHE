"""Dang ky tap trung cac module API (prefix chung /api/v1)."""


def register_blueprints(app):
    from api.auth.routes import auth_bp
    from api.menu.routes import menu_bp
    from api.orders.routes import orders_bp
    from api.pages import pages_bp
    from api.payments.routes import payments_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(pages_bp)
