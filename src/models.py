from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Date, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship, backref

from database import Base


class License(Base):
    __tablename__ = "license"

    license_id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    type = Column(Integer)
    duration = Column(Integer)
    name = Column(String(150))


class Utm(Base):
    __tablename__ = "utm"

    utm_id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    utm = Column(String)
    registered = Column(Boolean)
    date_time = Column(DateTime)


class Data(Base):
    __tablename__ = "data"

    data_id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    date_registered = Column(Date)
    date_last_activity = Column(Date)
    last_session = Column(Date)
    count_session = Column(Integer)
    full_name = Column(String)
    email = Column(String)
    notification = Column(String)
    category = Column(String)
    time_zone = Column(String)


class Session(Base):
    __tablename__ = "session"

    session_id = Column(BigInteger, primary_key=True)
    statistic_id = Column(BigInteger, ForeignKey("statistic.statistic_id"), nullable=False)
    date_session = Column(Date)
    duration = Column(Integer)
    score = Column(Integer)
    status = Column(Integer)
    transcript = Column(String)


class Statistic(Base):
    __tablename__ = "statistic"

    statistic_id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    summary = Column(JSON)
    incorrect = Column(JSON)
    sessions = relationship(Session, backref=backref("statistic", lazy=False))


class User(Base):
    __tablename__ = "user_t"

    user_id = Column(BigInteger, primary_key=True)
    license_id = Column(Integer, ForeignKey("license.license_id"))
    license = relationship(License, backref=backref('user_t', uselist=False, lazy=False))
    utm_id = Column(Integer, ForeignKey("utm.utm_id"))
    utm = relationship(Utm, backref=backref('user_t', uselist=False, lazy=False))
    data_id = Column(Integer, ForeignKey("data.data_id"))
    data = relationship(Data, backref=backref('user_t', uselist=False, lazy=False))
    statistic_id = Column(Integer, ForeignKey("statistic.statistic_id"))
    statistic = relationship(Statistic, backref=backref('user_t', uselist=False, lazy=False))


class Report(Base):
    __tablename__ = "report"

    report_id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("question.question_id"), nullable=False)
    text = Column(String)


class Question(Base):
    __tablename__ = "question"

    question_id = Column(Integer, primary_key=True)
    type = Column(Integer)
    section = Column(Integer)
    element = Column(Integer)
    link = Column(String)
    question_text = Column(String)
    answer_user = Column(String)
    reports = relationship(Report, backref=backref("question", lazy=False))


class Order(Base):
    __tablename__ = "order"

    order_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("user_t.user_id"), nullable=False)
    result = Column(Boolean)
