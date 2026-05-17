from enum import StrEnum


class EventType(StrEnum):
    PRODUCTION = "production"
    EXPENSE = "expense"
    INCOME = "income"
    OBSERVATION = "observation"
    REPRODUCTIVE = "reproductive"
    ACQUISITION = "acquisition"
    MORTALITY = "mortality"
    INVENTORY = "inventory"


class InventoryAdjustment(StrEnum):
    INCREMENT = "increment"
    DECREMENT = "decrement"
    RESET = "reset"


class AcquisitionMethod(StrEnum):
    """How an individual entered the herd. Stored on the acquisition event's
    payload; ``purchased`` is the only method that books a paired expense."""

    PURCHASED = "purchased"
    BORN = "born"
    OTHER = "other"


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
