# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, MetaData
from expenses.data_model import Base, Currency, Category
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime


def get_engine(name, password):
    password_connector = ['', '']
    if password is not None:
        password_connector[0] = '+pysqlcipher'
        password_connector[1] = ':{}@/'.format(password)
    connector = 'sqlite{pw[0]}://{pw[1]}{name}'.format(
        pw=password_connector, name=name)

    return create_engine(connector, echo=False)


def db_create(name, password=None):
    engine = get_engine(name, password)

    # create data model
    Base.metadata.create_all(engine)

    # initiate session and add all standard data
    Session = sessionmaker(bind=engine)
    db = Session()

    db.add_all(standard_data())
    db.commit()
    db.close()


def db_connect(name, password=None):
    engine = get_engine(name, password)

    Session = sessionmaker(bind=engine)
    db = Session()

    return db


def db_disconnect(db):
    db.commit()
    db.close()


def standard_data():
    """
    standard data that should not be missing in any instance of the database
    """

    currencies = [Currency(name='Euro', symbol=u'€',
                           identifier='EUR'),
                  Currency(name='Dollar',
                           symbol=str('$'),
                           identifier='USD'),
                  Currency(name='Franken',
                           symbol=str('Fr'),
                           identifier='CHF'),
                  Currency(name='Pfund', symbol=str('£'),
                           identifier='GBP')]

    categories = [Category(name='Sonstiges')]
    return currencies + categories


def write_backup(db):
    backup = ""

    backup += "Currencies\n"
    for item in db.query(Currency):
        backup += json.dumps(item.__dict__) + '\n'

    backup += "Categories\n"
    for item in db.query(Category):
        backup += json.dumps(item.__dict__) + '\n'

    backup += "Expenses\n"
    for item in db.query(Expense):
        backup += json.dumps(item.__dict__) + '\n'

    filename = "backup_{:%Y%m%d}.expense".format(datetime.today())
    f = open(filename, 'w')
    f.write(backup)
    f.close()


def load_backup(db, filename):
    # clear database
    meta = MetaData()
    trans = db.begin()
    for table in reversed(meta.sorted_tables):
        db.execute(table.delete())
    trans.commit()

    with open(filename, 'r') as f:
        for line in f:
            if line not in ["Currencies", "Expenses", "Categories"]:
                item = json.loads(line)
                db.add(**item)
    db.commit()


def write_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f)
    f.close()


def load_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    f.close()
    return config
