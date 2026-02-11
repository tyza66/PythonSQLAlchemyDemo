# By tyza66
import os
from contextlib import contextmanager
from dataclasses import asdict

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy import String, Integer

# Ensure PyMySQL is installed before creating engine to give a clearer error
try:
    import pymysql  # type: ignore
except ImportError as exc:  # pragma: no cover - startup guard
    raise SystemExit("Missing dependency pymysql. Run: pip install -r requirements.txt") from exc

# 从.env文件加载数据库配置
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("mysql://"):
    # Normalize to pymysql driver if user omitted it
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL is required. Example: mysql+pymysql://user:pass@localhost:3306/dbname")

# 定义一个基础模型类
class Base(DeclarativeBase):
    pass           # 这里可以添加一些公共的字段或方法，所有模型类都将继承这些功能

# 继承Base类来定义用户模型，映射到数据库中的users表
class User(Base):
    __tablename__ = "users" # 表名

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    def __repr__(self) -> str:  # 定义对象的字符串表示，方便调试和日志输出 类似于Java中的toString方法
        return f"User(id={self.id}, name={self.name!r}, email={self.email!r})"


# 创建数据库引擎，echo=True启用SQL日志，future=True启用SQLAlchemy 2.0风格的行为
engine = create_engine(DATABASE_URL, echo=True, future=True)

# 定义一个上下文管理器来管理数据库会话，确保资源正确释放
@contextmanager
def session_scope():
    # 使用上下文管理器确保会话正确关闭，并在发生异常时回滚事务
    with Session(engine) as session:
        try:
            # 相当于在这里开始一个事务，yield后如果没有异常则提交，如果有异常则回滚
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

# 初始化数据库，创建所有表
def init_db():
    Base.metadata.create_all(engine)

# 定义CRUD操作函数，使用session_scope管理数据库会话
def create_user(name: str, email: str) -> User:
    with session_scope() as session:
        user = User(name=name, email=email)
        session.add(user)
        session.flush()  # populate id
        return user

# 查询所有用户，返回一个用户列表
def list_users() -> list[User]:
    with session_scope() as session:
        stmt = select(User)
        return list(session.scalars(stmt))

# 根据用户id更新用户的电子邮件地址，如果用户不存在则返回None
def update_user_email(user_id: int, new_email: str) -> User | None:
    with session_scope() as session:
        user = session.get(User, user_id)
        if not user:
            return None
        user.email = new_email
        session.add(user)
        return user

# 根据用户id删除用户，如果用户不存在则返回False，删除成功返回True
def delete_user(user_id: int) -> bool:
    with session_scope() as session:
        user = session.get(User, user_id)
        if not user:
            return False
        session.delete(user)
        return True


def main():
    init_db()

    print("创建两个用户")
    alice = create_user("Alice", "alice@example.com")
    bob = create_user("Bob", "bob@example.com")

    print("查询当前的用户列表")
    for u in list_users():
        print(asdict(u))

    print("通过id更新Bob的电子邮件地址")
    updated = update_user_email(bob.id, "bb@example.com")
    print("Updated:", asdict(updated) if updated else None)

    print("通过id删掉Alice")
    delete_user(alice.id)

    print("Users after delete:")
    for u in list_users():
        print(asdict(u))

if __name__ == "__main__":
    main()

