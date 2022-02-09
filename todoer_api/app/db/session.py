"""how to connect to the DB"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URI = "sqlite:///example.db"
# see how to connect to postgres
# https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    # required for sqlite
    connect_args={"check_same_thread": False},
)

# the main access point by ORM
# the Session establishes all conversations with the database and represents
# a “holding zone” for all the objects which you’ve loaded or associated with it during its lifespan.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
