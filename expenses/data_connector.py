# -*- coding: utf-8 -*-
"""Handling and Connection to data sources."""

from sqlalchemy import create_engine, MetaData
from expenses.data_model import Base, Currency, Category, Expense
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime
from os import path, makedirs
from contextlib import closing


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
    """Open a connection to the database."""
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


def datetime_serializer(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        serial = obj.strftime('%Y-%m-%dT%H:%M:%SZ')
        return serial
    raise TypeError("Type not serializable")


def datetime_parser(obj):
    """JSON parser for datetime strings."""
    if isinstance(obj, dict):
        # walk over items
        return {x: datetime_parser(obj[x]) for x in obj.keys()}
    if isinstance(obj, str):
        # this may be a date object
        # try to parse, if not return object
        try:
            parsed = datetime.strptime(obj, '%Y-%m-%dT%H:%M:%SZ')
            return parsed
        except ValueError:
            return obj


def write_backup(db, backup_directory):
    """Create a JSON serialized backup of all the data in the db."""
    def dump_object(item):
        allowed_types = [str, int, datetime, None]
        fields = [x for x in dir(item)
                  if (not x.startswith('_') and
                      x != 'metadata' and
                      type(getattr(item, x)) in allowed_types)]
        item_dict = {field: getattr(item, field) for field in fields}
        return json.dumps(item_dict, default=datetime_serializer)

    backup = ""

    backup += "Currencies\n"
    for item in db.query(Currency):
        backup += dump_object(item) + '\n'

    backup += "Categories\n"
    for item in db.query(Category):
        backup += dump_object(item) + '\n'

    backup += "Expenses\n"
    for item in db.query(Expense):
        backup += dump_object(item) + '\n'

    filename = path.join(backup_directory,
                         "backup_{:%Y%m%d}.expense".format(datetime.today()))

    # create backup directory if necessary
    if not path.exists(backup_directory):
        makedirs(backup_directory)

    f = open(filename, 'w')
    f.write(backup)
    f.close()


def load_backup(db, filename, backup_directory):
    """Clear database and recreate from backup."""
    db.commit()

    # clear database
    meta = MetaData()
    for table in reversed(meta.sorted_tables):
        db.execute(table.delete())

    db.query(Expense).delete()
    db.query(Currency).delete()
    db.query(Category).delete()

    db.commit()
    db.flush()

    # check if database is empty
    for item in db.query(Expense):
        print(item)

    # now open backup
    filename = path.join(backup_directory, filename)

    # load data
    with open(filename, 'r') as f:
        current_class = None
        for line in f:
            if line == "Currencies\n":
                current_class = Currency
            elif line == "Expenses\n":
                current_class = Expense
            elif line == "Categories\n":
                current_class = Category
            else:
                new_object = current_class(**json.loads(line,
                                           object_hook=datetime_parser))
                db.add(new_object)
    db.flush()


def write_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f)
    f.close()


def load_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    f.close()
    return config
