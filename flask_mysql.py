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

# 强制执行一下建表，如果没有表的话就直接创建，如果表已经存在则不会有任何影响
Base.metadata.create_all(engine)

# 获得会话的函数
def get_session():
    return Session(engine, expire_on_commit=False)


# 获取用户列表的API，返回一个JSON数组，每个元素是一个用户对象
@app.get("/users")
def list_users():
    with get_session() as session:
        stmt = select(User)
        users = [u.to_dict() for u in session.scalars(stmt)]
        return jsonify(users)


# 创建用户的API，接受一个JSON对象，包含name和email字段，返回新创建的用户对象
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


# 更新用户的API，接受一个JSON对象，包含email字段，返回更新后的用户对象，如果用户不存在则返回404错误
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


# 通过 id 删除用户的 API，如果用户不存在则返回 404 错误，删除成功返回 204 No Content 状态码
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

