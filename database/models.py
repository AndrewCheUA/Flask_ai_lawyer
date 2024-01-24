import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
from flask_login import UserMixin
import jwt
from time import time

from system import app
from database.connect import session


Base = sqlalchemy.orm.declarative_base()


class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(250), nullable=False)
    image_file = Column(String(40), nullable=False, default='default.jpg')
    created_at = Column('created_at', DateTime, default=func.now())
    is_active = Column(Boolean, default=False)
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")

    def get_reset_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm=app.config['ALGORITHM'])

    @staticmethod
    def verify_reset_token(token):
        try:
            user_id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=app.config['ALGORITHM'])['reset_password']
        except Exception as E:
            return print(E)
        return session.get(User, user_id)



class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column("title", String(length=250), nullable=False)
    date_posted = Column('created_at', DateTime, default=func.now())
    content = Column("description", String(length=900), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    user = relationship("User", back_populates="posts")

