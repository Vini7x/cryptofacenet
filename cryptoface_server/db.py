from sqlalchemy import String, Integer, ForeignKey, Column, UniqueConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

Session = sessionmaker()


class Owner(Base):
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    public_key1 = Column(String, nullable=False)
    public_key2 = Column(String, nullable=False)

    users = relationship("User", backref="owner")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("name", "owner_id", name="unique_user"),)

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    name = Column(String, nullable=False, unique=True)
    embedding_sum = Column(String, nullable=False)

    embeddings = relationship("Embedding", backref="user")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    value = Column(String, nullable=False)


def create_db_n_session(engine):
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
