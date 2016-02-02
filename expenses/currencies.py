from requests import get
from expenses.data_model import Expense, Category
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


def amount_in_month(start_month, start_date, end_month, end_date,
                    end_of_month, total_amount):
    affected_month = end_of_month.year * 12 + end_of_month.month
    month_length = end_of_month.day
    amount = 0
    if start_month <= affected_month and end_month >= affected_month:
        # counts somehow into this month
        total_days = (end_date - start_date).days + 1
        in_month = 0

        if affected_month == start_month and affected_month == end_month:
            # time span lays totally in month
            in_month = total_days
        elif start_month < affected_month and end_month == affected_month:
            # begins before month, ends in month
            in_month = min(month_length, end_date.day)
        elif start_month == affected_month and end_month > affected_month:
            # begins in month, ends after month
            in_month = max(month_length - start_date.day, 0)
        else:
            assert start_month < affected_month and end_month > affected_month
            # begins and ends outside of month
            in_month = month_length

        # now calculate fractional amount
        amount = round(1.0 * in_month / total_days * total_amount)
    return amount


def fractional_expense(item, end_of_month, debug):
    if debug:
        print("processing {eur:.2f} from {start} to {end}".format(
            eur=item.in_eur / 100.0,
            start=item.issued.strftime('%Y-%m-%d'),
            end=item.end.strftime('%Y-%m-%d')))

    start_month = item.issued.year * 12 + item.issued.month
    end_month = item.end.year * 12 + item.end.month

    amount = amount_in_month(start_month, item.issued, end_month, item.end,
                             end_of_month, item.in_eur)
    if debug:
            print('counts for {}'.format(amount))
    return amount


def repeating_expense(item, end_of_month):
    step = item.repeat_interval

    affected_month = end_of_month.year * 12 + end_of_month.month
    start_month = item.issued.year * 12 + item.issued.month
    if item.end is not None:
        end_month = item.end.year * 12 + item.end.month
        end_date = item.end
    else:
        end_month = start_month
        end_date = item.issued

    # stuff to calculate fractional amount

    amount = 0
    while start_month <= affected_month:
        amount += amount_in_month(start_month, item.issued, end_month,
                                  end_date, end_of_month, item.in_eur)

        start_month += step
        end_month += step

    return amount


def statistics(db, year, month, debug=False):
    categories = {x.id: 0 for x in db.query(Category).all()}

    max_day = calendar.monthrange(year, month)[1]
    start_of_month = dt.datetime(year, month, 1)
    end_of_month = dt.datetime(year, month, max_day)
    # simple expenses
    for item in db.query(Expense).filter(
            Expense.end.is_(None), Expense.repeat_interval.is_(None),
            Expense.issued >= start_of_month,
            Expense.issued <= end_of_month):
        categories[item.category_id] += item.in_eur

    # long term expenses
    for item in db.query(Expense).filter(
            Expense.end.isnot(None), Expense.repeat_interval.is_(None),
            Expense.issued <= end_of_month,
            Expense.end >= start_of_month):
        amount = fractional_expense(item, end_of_month, debug)
        categories[item.category_id] += amount

    # repeating expenses
    repeaters = []
    for item in db.query(Expense).filter(Expense.repeat_interval.isnot(None)):
        amount = repeating_expense(item, end_of_month)
        categories[item.category_id] += amount
        if amount > 0:
            repeaters.append(item)

    return categories, repeaters
