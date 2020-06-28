from flask import Flask
from flask_restx import Api
from cryptoface_server.server import api as resources
from cryptoface_server.db import create_db_n_session
from pathlib import Path
from sqlalchemy import create_engine


def create_server():
    app = Flask(__name__)
    api = Api(app)
    api.add_namespace(resources, path="/api")

    app.config.from_object("cryptoface_server.config.Config")

    db_path = app.config["DB_PATH"] / Path("server.db")
    Path(app.config["DB_PATH"]).mkdir(exist_ok=True, parents=True)
    print(db_path.as_posix())
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")

    create_db_n_session(engine)

    return app
