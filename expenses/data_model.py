from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Unicode
from sqlalchemy.orm import relationship


Base = declarative_base()


class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    issued = Column(DateTime)
    end = Column(DateTime)
    repeat_interval = Column(Integer)
    price = Column(Integer)
    in_eur = Column(Integer)
    note = Column(String(50))
    currency_id = Column(Integer, ForeignKey('currencies.id'))
    currency = relationship('Currency')
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship('Category')

    def __str__(self):
        date_string = self.issued.strftime("%Y-%m-%d %H:%M")
        price_str = "{:.2f}".format(self.price / 100.0)
        return ('{time}: {price:>8} {s.currency.symbol}, {s.category.name}'
                '  |  {s.note}').format(
                    time=date_string, price=price_str, s=self)


class Currency(Base):
    __tablename__ = 'currencies'

    id = Column(Integer, primary_key=True)
    name = Column(String(10))
    identifier = Column(String(3))
    symbol = Column(Unicode(1))


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(30))
