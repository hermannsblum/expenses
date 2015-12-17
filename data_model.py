from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship


def get_data_model():

    Base = declarative_base()

    class Expense(Base):
        __tablename__ = 'expenses'

        id = Column(Integer, primary_key=True)
        issued = Column(DateTime)
        price = Column(Integer)
        note = Column(String(50))
        currency_id = Column(Integer, ForeignKey('Currency.id'))
        currency = relationship('Currency')

    class Currency(Base):
        __tablename__ = 'currencies'

        id = Column(Integer, primary_key=True)
        name = Column(String(10))
        identifier = Column(String(3))

    return Base
