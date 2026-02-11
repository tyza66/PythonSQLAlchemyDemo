"""Flask app exposing CRUD endpoints for User model."""
import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from main import Base, User

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True, future=True)

app = Flask(__name__)

# Ensure tables exist
Base.metadata.create_all(engine)


def get_session():
    return Session(engine, expire_on_commit=False)


@app.get("/users")
def list_users():
    with get_session() as session:
        stmt = select(User)
        users = [u.to_dict() for u in session.scalars(stmt)]
        return jsonify(users)


@app.post("/users")
def create_user_api():
    data = request.get_json(force=True)
    name = data.get("name")
    email = data.get("email")
    if not name or not email:
        return jsonify({"error": "name and email required"}), 400
    with get_session() as session:
        user = User(name=name, email=email)
        session.add(user)
        session.commit()
        return jsonify(user.to_dict()), 201


@app.patch("/users/<int:user_id>")
def update_user_api(user_id: int):
    data = request.get_json(force=True)
    new_email = data.get("email")
    if not new_email:
        return jsonify({"error": "email required"}), 400
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            return jsonify({"error": "not found"}), 404
        user.email = new_email
        session.add(user)
        session.commit()
        return jsonify(user.to_dict())


@app.delete("/users/<int:user_id>")
def delete_user_api(user_id: int):
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            return jsonify({"error": "not found"}), 404
        session.delete(user)
        session.commit()
        return ("", 204)


if __name__ == "__main__":
    app.run(debug=True)

