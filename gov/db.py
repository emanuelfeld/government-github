from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from settings import DATABASE_URL

engine = create_engine(DATABASE_URL,
                       convert_unicode=True)

session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=False,
                                      bind=engine))
Base = declarative_base()
Base.query = session.query_property()


def init_db():
    import gov.models
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(bind=engine)
