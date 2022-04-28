import os


DATABASE_URL            = os.environ.get("DATABASE_URL", "sqlite:///data.db")
SECRET_KEY              = os.environ.get("SECRET_KEY", "secret")
REQUIRE_OTP             = os.getenv("REQUIRE_OTP", "0") in ("true", "yes", "on", "1")
TEMPLATES_AUTO_RELOAD   = True
BASE_URL                = os.getenv("BASE_URL", "https://example.com")
UPLOADS_FOLDER          = os.getenv("UPLOADS_FOLDER", "uploads")
