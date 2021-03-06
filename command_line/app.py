from data_connector import db_connect, db_disconnect
from user_input import list_input, type_input, list_choice,\
    query_choice, bool_question, str_input, dt_input
from data_model import Expense, Currency, Category
from currencies import to_eur, statistics
from sqlalchemy.exc import DatabaseError
import datetime as dt
from os.path import exists


class App():

    def __init__(self):
        file_valid = False
        while not file_valid:  # test if file exists
            db_name = str_input('datenbank', default='test') + '.db'
            file_valid = exists(db_name)
            if not file_valid:
                print('File not found :(')

        success = False
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

        cat = query_choice(self.db.query(Category))

        currency = query_choice(self.db.query(Currency))

        if bool_question('Not issued right now?', default=False):
            issued = dt_input('Date if issue')
        else:
            issued = dt.datetime.now()

        note = None
        if bool_question('Do you want to add a note?', default=False):
            note = str_input('Note')

        end = issued
        if bool_question('long term expense?', default=False):
            end = dt_input('End if expense')

        eur = to_eur(price, currency.identifier, issued)
        print('That was an expense of {:.2f}€'.format(eur / 100.0))

        expense = Expense(issued=issued,
                          price=price,
                          in_eur=eur,
                          note=note,
                          end=end,
                          currency=currency,
                          category=cat)
        self.db.add(expense)
        self.db.commit()

        if bool_question('another expense?', default=False):
            self.track_expense()

    def history(self):
        for item in self.db.query(Expense):
            print(item)

    def stats(self):
        now = dt.datetime.now()
        categories = statistics(self.db, now.year, now.month)

        print('\nStatistics for {}'.format(dt.datetime.today().strftime('%B')))
        for key, amount in categories.items():
            print('{cat.name}: {amount:.2f}€'.format(
                cat=self.db.query(Category).get(key), amount=amount / 100.0))
        print('')

    def edit_categories(self):
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
