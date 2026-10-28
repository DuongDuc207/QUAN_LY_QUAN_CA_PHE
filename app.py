import os

from bootstrap import ensure_runtime

ensure_runtime(allow_reexec=__name__ == "__main__")

from flask import Flask

from api.index import register_blueprints  # noqa: E402
from config.settings import SECRET_KEY  # noqa: E402


def create_app():
    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend/static",
    )
    app.secret_key = SECRET_KEY
    app.config["SESSION_COOKIE_NAME"] = "qlcp_sprint1_session"

    register_blueprints(app)

    @app.get("/")
    def index():
        from flask import redirect, url_for

        return redirect(url_for("pages.dashboard"))

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)
