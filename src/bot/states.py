from aiogram.fsm.state import StatesGroup, State


class Introduction(StatesGroup):
    """
    State required for user registration
    """
    Intro = State()
    Name = State()
    Rules = State()
    Email = State()
    Category = State()
    Location = State()
    NotificationTime = State()
    TrialPeriod = State()
    FirstSession = State()


class Change(StatesGroup):
    """
    State required to change the notification time
    """
    ChangeNotification = State()


class FormingReport(StatesGroup):
    """
    State necessary for the formation of the report
    """
    IdQuestion = State()
    TextReport = State()


class SessionUser(StatesGroup):
    """
    State in session
    """
    Active = State()


class UserState(StatesGroup):
    """
    User states depending on the license
    """
    SubscriberActive = State()
    SubscriberInactive = State()
    TrialPeriodActive = State()
    TrialPeriodInactive = State()
    Unregister = State()


class Processing(StatesGroup):
    Active = State()
