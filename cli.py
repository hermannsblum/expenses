from expenses.data_connector import db_connect, db_disconnect,\
    load_config
from command_line.user_input import type_input, list_choice,\
    query_choice, bool_question, str_input, dt_input
from expenses.data_model import Expense, Currency, Category
from expenses.currencies import to_eur, statistics
from sqlalchemy.exc import DatabaseError
import datetime as dt
from os.path import exists


class App():

    def __init__(self):
        self.config = load_config()

        if 'db' not in self.config:
            file_valid = False
            while not file_valid:  # test if file exists
                db_name = str_input('datenbank', default='test') + '.db'
                file_valid = exists(db_name)
                if not file_valid:
                    print('File not found :(')
        else:
            db_name = self.config['db']

        success = False
        if 'password' in self.config:
            database = db_connect(db_name, password=self.config['password'])
            try:
                database.query(Currency).all()
                success = True
            except DatabaseError:
                success = False
                # now user can still input

        while not success:
            db_password = str_input('passwort', default='123456')
            database = db_connect(db_name, password=db_password)
            # try if password was correct
            try:
                database.query(Currency).all()
                success = True
            except DatabaseError:
                success = False

        # FINALLY
        self.db = database

    def end(self):
        db_disconnect(self.db)

    def main_menu(self):
        menu = ''
        while menu != 'exit':
            menu = list_choice(['track expense', 'last month',
                                'edit categories', 'exit'])
            if menu == 'exit':
                self.end()
            if menu == 'track expense':
                self.track_expense()
            if menu == 'last month':
                self.history()
                self.stats()
            if menu == 'edit categories':
                self.edit_categories()

    def track_expense(self):
        price = type_input('price', float)
        price = int(price * 100)

        currency = query_choice(self.db.query(Currency))

        cat = query_choice(self.db.query(Category))

        advanced = bool_question('advanced options?', default=False)
        # initialize with simple setup
        issued = dt.datetime.now()
        note = None
        end = None
        repeat = None
        if advanced:
            if bool_question('Not issued right now?', default=False):
                issued = dt_input('Date if issue')

            if bool_question('Do you want to add a note?', default=False):
                note = str_input('Note')

            if bool_question('long term expense?', default=False):
                end = dt_input('End if expense')

            if bool_question('repeat?', default=False):
                repeat = type_input('Repeat this expense every _ months', int,
                                    default=-1)
                if repeat == -1:
                    repeat = None

        eur = to_eur(price, currency.identifier, issued)
        print('That was an expense of {:.2f}€'.format(eur / 100.0))

        expense = Expense(issued=issued,
                          price=price,
                          in_eur=eur,
                          note=note,
                          end=end,
                          repeat_interval=repeat,
                          currency=currency,
                          category=cat)
        self.db.add(expense)
        self.db.commit()

        if bool_question('another expense?', default=True):
            self.track_expense()

    def history(self):
        for item in self.db.query(Expense):
            print(item)

    def stats(self):
        now = dt.datetime.now()
        month = type_input('month', int, default=now.month)
        (categories, repeaters) = statistics(self.db, now.year, month)

        print('\nStatistics for {}'.format(
            dt.datetime(now.year, month, 1).strftime('%B')))

        total = 0
        for key, amount in categories.items():
            total += amount
            amount_str = '{:.2f}'.format(amount / 100.0)
            print('{cat.name:>16}: {amount:>8} €'.format(
                cat=self.db.query(Category).get(key), amount=amount_str))
        print('{:>16}: {:>8} €'.format(
            'TOTAL', '{:.2f}'.format(total / 100.0)))

        print('\nwith these repeating expenses considered')
        for item in repeaters:
            print(item)

    def edit_categories(self):
        for item in self.db.query(Category):
            print(item.name)
        menu = list_choice(['add', 'edit', 'delete', 'back'])
        if menu == 'add':
            new = Category(name=str_input('Name'))
            self.db.add(new)
        elif menu == 'edit':
            edit = query_choice(self.db.query(Category))
            edit.name = str_input('New name')
        elif menu == 'delete':
            rm = query_choice(self.db.query(Category))
            self.db.delete(rm)
        self.db.commit()


if __name__ == '__main__':
    app = App()
    app.main_menu()
