from requests import get
from data_model import Expense, Category
import calendar
import datetime as dt

def to_eur(amount, identifier, date):
    if identifier == 'EUR':
        return amount
    date_string = date.strftime('%Y-%m-%d')
    r = get('https://api.fixer.io/{date}?symbols={symb}'.format(
        date=date_string, symb=identifier))
    rate = r.json()['rates'][identifier]
    return round(amount / rate)


def statistics(db, year, month, debug=False):
    categories = {x.id: 0 for x in db.query(Category).all()}
    for item in db.query(Expense):
        if item.end is None:
            if item.issued.month == month and item.issued.year == year:
                categories[item.category_id] += item.in_eur

        # now only expenses over several months
        else:
            if debug:
                print("processing {eur:.2f} from {start} to {end}".format(
                    eur=item.in_eur / 100.0,
                    start=item.issued.strftime('%Y-%m-%d'),
                    end=item.end.strftime('%Y-%m-%d')))

            max_day = calendar.monthrange(year, month)[1]
            start_of_month = dt.datetime(year, month, 1)
            end_of_month = dt.datetime(year, month, max_day)
            if item.issued <= end_of_month and item.end >= start_of_month:
                # counts somehow into this month
                total_days = (item.end - item.issued).days + 1
                in_month = 0

                if item.issued >= start_of_month and item.end <= end_of_month:
                    # time span lays totally in month
                    in_month = total_days
                elif item.issued < start_of_month:
                    # time span starts before month
                    if item.end <= end_of_month:
                        # time span ends in month
                        in_month = (item.end - start_of_month).days + 1
                    else:
                        # time span overlays month
                        in_month = max_day
                elif item.end > end_of_month and item.issued >= start_of_month:
                    # time span ends after month
                    in_month = (end_of_month - item.issued).days + 1

                # now add to dict
                amount = round(1.0 * in_month / total_days * item.in_eur)
                if debug:
                    print('counts for {} days, {}'.format(in_month, amount))

                categories[item.category_id] += amount
    return categories
