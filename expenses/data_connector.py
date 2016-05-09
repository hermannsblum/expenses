# -*- coding: utf-8 -*-
"""Handling and Connection to data sources."""

from sqlalchemy import create_engine, MetaData
from expenses.data_model import Base, Currency, Category, Expense
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime
from os import path, makedirs, listdir, remove


def get_engine(name, password):
    """Get sqlite engine."""
    password_connector = ['', '']
    if password is not None:
        password_connector[0] = '+pysqlcipher'
        password_connector[1] = ':{}@/'.format(password)
    connector = 'sqlite{pw[0]}://{pw[1]}{name}'.format(
        pw=password_connector, name=name)

    return create_engine(connector, echo=False)


def db_create(name, password=None):
    """Fill empty database with data model and initial data."""
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
    """Close database connection."""
    db.commit()
    db.close()


def standard_data():
    """Standard data for the start of every new database."""
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


# define format strings
backup_timestring = '%Y-%m-%dT%H:%M:%SZ'
backup_filename = "backup_%Y%m%dT%H%M.expense"


def datetime_serializer(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        serial = obj.strftime(backup_timestring)
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
            parsed = datetime.strptime(obj, backup_timestring)
            return parsed
        except ValueError:
            return obj
    return obj


def write_backup(db, backup_directory):
    """Create a JSON serialized backup of all the data in the db."""
    def dump_object(item):
        """Return JSON dict of non-internal fields in object."""
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
                         datetime.today().strftime(backup_filename))

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


def remove_old_backups(backup_directory):
    """Remove old backups.

    Keep 5 newest backups of the day,
    newest backup of every day this month,
    newest backup of every month.
    """
    # read backup directory, only backups should be here
    backup_list = listdir(backup_directory)
    today = []
    this_month = []
    monthly = []
    for filename in backup_list:
        if not filename.endswith('.expense'):
            # not a backup
            continue

        now = datetime.now()
        try:
            time = datetime.strptime(filename, backup_filename)
            if time.date() == now.date():
                today.append(time)
            elif time.year == now.year and time.month == now.month:
                this_month.append(time)
            else:
                monthly.append(time)
        except ValueError:
            print("Could not delete this old backup, did not understand"
                  " the nameing format: %s" % filename)

    # keep maximum 5 per day
    today.sort(reverse=True)
    to_remove = today[5:]

    # keep maximum of 1 per day for the rest of the month
    duplicates = []
    for time in this_month:
        same_date = [backup for backup in this_month
                     if backup.date() == time.date()]
        same_date.sort(reverse=True)
        duplicates.extend(same_date[1:])
    to_remove.extend(set(duplicates))

    # for the rest, keep 1 per month
    duplicates = []
    for time in monthly:
        same_date = [backup for backup in this_month
                     if backup.month == time.month]
        same_date.sort(reverse=True)
        duplicates.extend(same_date[1:])
    to_remove.extend(set(duplicates))

    # now remove all files
    for time in to_remove:
        remove(path.join(backup_directory, time.strftime(backup_filename)))


def write_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f)
    f.close()


def load_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    f.close()
    return config
