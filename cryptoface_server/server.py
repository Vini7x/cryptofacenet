from flask_restx import Resource, abort, Namespace
from flask import request, current_app
from werkzeug.utils import secure_filename
from cryptoface_server.recognize import global_rec
from cryptoface_server.db import Session, User, Embedding, Owner
from sqlalchemy.exc import SQLAlchemyError
import pathlib
import tempfile

api = Namespace("api", description="Recognition API")


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


@api.route("/owners")
class OwnerResource(Resource):
    def post(self):
        name = request.json.get("name", None)
        public_key = request.json.get("public_key")
        if name is None or public_key is None:
            abort(400, message="Missing data")

        session = Session()

        try:
            owner = Owner(
                name=name,
                public_key1=str(public_key[0]),
                public_key2=str(public_key[1]),
            )
            session.add(owner)
            session.commit()
            session.close()
            return name, 201
        except SQLAlchemyError as e:
            session.rollback()
            session.close()
            abort(400, message=f"Error inserting: {e}")

    def put(self):
        name = request.json.get("name", None)
        public_key = request.json.get("public_key")
        if name is None or public_key is None:
            abort(400, message="Missing data")

        session = Session()

        try:
            owner = session.query(Owner).filter(Owner.name == name).first()
            if owner is None:
                abort(404, message="Owner not found")

            owner.public_key1 = str(public_key[0])
            owner.public_key2 = str(public_key[1])
            session.commit()
            session.close()
            return name, 201
        except SQLAlchemyError as e:
            session.rollback()
            session.close()
            abort(400, message=f"Error updating: {e}")

    def delete(self):
        name = request.json.get("name", None)
        if name is None:
            abort(400, message="Missing name")

        session = Session()

        try:
            owner = session.query(Owner).filter(Owner.name == name).first()
            if owner is None:
                abort(404, message="Owner not found")

            session.delete(owner)
            session.commit()
            session.close()
            return "OK", 204
        except SQLAlchemyError as e:
            session.rollback()
            session.close()
            abort(400, message=f"Error deleting: {e}")


@api.route("/<owner_name>/users/<username>")
@api.param("owner_name", "The name of the owner")
class FaceResource(Resource):
    def put(self, owner_name, username):
        file = request.files.get("face", None)
        if file is None or file.filename == "":
            abort(400, message="Missing file")

        session = Session()

        owner = session.query(Owner).filter(Owner.name == owner_name).first()

        if owner is None:
            abort(404, message="Owner not found")

        public_key = (
            int(owner.public_key1),
            int(owner.public_key2),
        )

        with tempfile.TemporaryDirectory() as tempdir:
            if not file or not allowed_file(file.filename):
                abort(400, message="File not permitted")

            filename = pathlib.Path(secure_filename(file.filename))
            filepath = (tempdir / filename).as_posix()
            file.save(filepath)

            embeddings, emb_sum = global_rec.get_crypt_encodings(filepath, public_key)

            try:
                user_obj = (
                    session.query(User)
                    .filter(User.name == username, User.owner_id == owner.id)
                    .first()
                )
                insert = False
                if user_obj is None:
                    insert = True
                    user_obj = User(
                        name=username, embedding_sum=str(emb_sum), owner=owner
                    )
                user_obj.embeddings = [Embedding(value=str(emb)) for emb in embeddings]

                if insert:
                    session.add(user_obj)
                session.commit()
                session.close()
                return "OK", 201
            except SQLAlchemyError as e:
                session.rollback()
                session.close()
                abort(400, message=f"Error updating/inserting: {e}")

    def delete(self, owner_name, username):

        session = Session()

        owner = session.query(Owner).filter(Owner.name == owner_name).first()
        if owner is None:
            abort(404, message="Owner not found")

        user_obj = (
            session.query(User)
            .filter(User.name == username, User.owner_id == owner.id)
            .first()
        )
        if user_obj is None:
            abort(404, message="User not found")

        try:
            session.delete(user_obj)
            session.commit()
            session.close()
            return "OK", 204
        except SQLAlchemyError as e:
            session.rollback()
            session.close()
            abort(400, message=f"Error deleting: {e}")


@api.route("/<owner_name>/auth/<username>")
@api.param("owner_name", "The name of the owner")
class AuthenticateResource(Resource):
    def post(self, owner_name, username):
        file = request.files.get("face", None)
        if file is None or file.filename == "":
            abort(400, message="Missing file")

        session = Session()

        owner = session.query(Owner).filter(Owner.name == owner_name).first()

        if owner is None:
            abort(404, message="Owner not found")

        public_key = (
            int(owner.public_key1),
            int(owner.public_key2),
        )

        with tempfile.TemporaryDirectory() as tempdir:
            if not file or not allowed_file(file.filename):
                abort(400, message="File not permitted")

            filename = pathlib.Path(secure_filename(file.filename))
            filepath = (tempdir / filename).as_posix()
            file.save(filepath)

            embeddings, emb_sum = global_rec.get_crypt_encodings(filepath, public_key)

            user_obj = session.query(User).filter(User.name == username).first()
            if user_obj is None:
                abort(404, message="User not found")

            emb_list = [int(emb.value) for emb in user_obj.embeddings]

            distance = global_rec.compare(
                filepath, int(user_obj.embedding_sum), emb_list, public_key
            )
            session.close()

        return {"distance": distance.val}, 200


@api.route("/<owner_name>/recognition")
@api.param("owner_name", "The name of the owner")
class CompareResource(Resource):
    def post(self, owner_name):
        file = request.files.get("face", None)
        if file is None or file.filename == "":
            abort(400, message="Missing file")

        session = Session()

        owner = session.query(Owner).filter(Owner.name == owner_name).first()

        if owner is None:
            abort(404, message="Owner not found")

        public_key = (
            int(owner.public_key1),
            int(owner.public_key2),
        )

        with tempfile.TemporaryDirectory() as tempdir:
            if not file or not allowed_file(file.filename):
                abort(400, message="File not permitted")

            filename = pathlib.Path(secure_filename(file.filename))
            filepath = (tempdir / filename).as_posix()
            file.save(filepath)

            embeddings, emb_sum = global_rec.get_crypt_encodings(filepath, public_key)

            users = session.query(User).filter(User.owner_id == owner.id).all()

            distances = []
            for user_obj in users:
                emb_list = [int(emb.value) for emb in user_obj.embeddings]

                distance = global_rec.compare(
                    filepath, int(user_obj.embedding_sum), emb_list, public_key
                )
                distances.append({"name": user_obj.name, "distance": distance.val})

            session.close()

        return {"distances": distances}, 200
