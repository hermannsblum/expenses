from expenses.data_connector import db_create
from command_line.user_input import str_input


if __name__ == '__main__':

    db_name = str_input('database name', default='test')
    db_name += '.db'

    db_password = str_input('database password', default='123456')
    while len(db_password) < 6:
        print('Password too short, min. 6 characters')
        db_password = str_input('database password', default='123456')

    db_create(db_name, password=db_password)
