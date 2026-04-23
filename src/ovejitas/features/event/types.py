from enum import StrEnum


class EventType(StrEnum):
    PRODUCTION = "production"
    EXPENSE = "expense"
    INCOME = "income"
    OBSERVATION = "observation"
    REPRODUCTIVE = "reproductive"
