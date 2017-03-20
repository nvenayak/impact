# coding=utf-8

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import create_engine

def bind_engine(db_path='sqlite:///default_impt.db',echo=False):
    engine = create_engine(db_path, echo=echo)
    return engine

def create_session():
    from sqlalchemy.orm import sessionmaker

    engine = bind_engine()

    session_maker = sessionmaker(bind=engine)
    return session_maker()