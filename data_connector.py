from sqlalchemy import create_engine
from data_model import get_data_model
from sqlalchemy.orm import sessionmaker


def get_engine(name, passwort):
    passwort_connector = ['', '']
    if passwort is not None:
        passwort_connector[0] = '+pysqlcipher'
        passwort_connector[1] = ':{}@/'.format(passwort)
    connector = 'sqlite{pw[0]}://{pw[1]}{name}'.format(
        pw=passwort_connector, name=name)

    return create_engine(connector, echo=False)


def db_create(name, passwort=None):
    engine = get_engine(name, passwort)

    model = get_data_model()

    model.metadata.create_all(engine)


def db_connect(name, passwort=None):
    engine = get_engine(name, passwort)

    Session = sessionmaker(bind=engine)
    db = Session()

    return db
