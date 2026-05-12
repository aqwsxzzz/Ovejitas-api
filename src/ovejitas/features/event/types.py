from enum import StrEnum


class EventType(StrEnum):
    PRODUCTION = "production"
    EXPENSE = "expense"
    INCOME = "income"
    OBSERVATION = "observation"
    REPRODUCTIVE = "reproductive"
    ACQUISITION = "acquisition"
    MORTALITY = "mortality"


class Unit(StrEnum):
    G = "g"
    KG = "kg"
    LB = "lb"
    T = "t"
    ML = "ml"
    L = "l"
    GAL = "gal"
    UNIT = "unit"
    DOZEN = "dozen"
    HEAD = "head"
