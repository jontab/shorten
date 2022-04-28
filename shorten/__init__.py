from shorten.database import initialize
from shorten.blueprints import main


import os


import quart_auth
import quart


def create() -> quart.Quart:
    """
    Creates the application.

    1. Initializes authentication layer.
    2. Loads configuration from environment.
    3. Initializes database proxy.
    4. Registers available blueprints.
    """
    manager = quart_auth.AuthManager()

    app = quart.Quart(__name__)
    manager.init_app(app)

    os.environ.setdefault("SETTINGS", "settings.py")
    app.config.from_envvar("SETTINGS")

    initialize(app)

    app.register_blueprint(main.bp)

    return app
