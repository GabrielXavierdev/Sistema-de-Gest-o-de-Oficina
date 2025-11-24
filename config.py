import os

class Config:
    """Configurações da aplicação Flask."""

    # Secret Key segura (evita warnings no Flask 3+)
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///autoar.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # removido no Flask-SQLAlchemy 3, mas manter não causa problema
