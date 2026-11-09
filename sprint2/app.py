import datetime
import os

from bootstrap import ensure_runtime

ensure_runtime(allow_reexec=__name__ == "__main__")

from flask import Flask
from flask.json.provider import DefaultJSONProvider

from api.index import register_blueprints  # noqa: E402
from config.settings import SECRET_KEY  # noqa: E402


def _json_default(o):
    # Mac dinh Flask tra ngay gio dang "Thu, 22 Oct 2026 14:05:09 GMT" -> trinh duyet
    # hieu nham la gio GMT va cong them mui gio. Tra ISO (khong mui gio) = gio may chu.
    if isinstance(o, datetime.datetime):
        return o.isoformat(timespec="seconds")
    if isinstance(o, datetime.date):
        return o.isoformat()
    return DefaultJSONProvider.default(o)


class JSONProvider(DefaultJSONProvider):
    default = staticmethod(_json_default)


def create_app():
    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend/static",
    )
    app.secret_key = SECRET_KEY
    app.config["SESSION_COOKIE_NAME"] = "qlcp_sprint2_session"
    app.json = JSONProvider(app)

    register_blueprints(app)

    @app.get("/")
    def index():
        from flask import redirect, url_for

        return redirect(url_for("pages.dashboard"))

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "5002"))
    app.run(host="0.0.0.0", port=port, debug=True)
