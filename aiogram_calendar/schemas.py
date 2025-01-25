from typing import Optional
from enum import Enum

from pydantic import BaseModel, conlist, Field

from aiogram.filters.callback_data import CallbackData


class SimpleCalAct(str, Enum):
    ignore = "IGNORE"
    select_weekdays = "SELECT_ALL_WEEKDAYS"
    unselect_weekdays = "UNSELECT_ALL_WEEKDAYS"
    unselect_day = "UNSELECT_DAY"
    save_days = "SAVE_DAYS"
    prev_y = "PREV-YEAR"
    next_y = "NEXT-YEAR"
    prev_m = "PREV-MONTH"
    next_m = "NEXT-MONTH"
    cancel = "CANCEL"
    today = "TODAY"
    day = "DAY"


class DialogCalAct(str, Enum):
    ignore = "IGNORE"
    set_y = "SET-YEAR"
    set_m = "SET-MONTH"
    prev_y = "PREV-YEAR"
    next_y = "NEXT-YEAR"
    cancel = "CANCEL"
    start = "START"
    day = "SET-DAY"


class CalendarCallback(CallbackData, prefix="calendar"):
    act: str
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    weekday: Optional[str] = None


class SimpleCalendarCallback(CalendarCallback, prefix="simple_calendar"):
    act: SimpleCalAct


class MultipleCalendarCallback(CalendarCallback, prefix="multiple_calendar"):
    act: SimpleCalAct


class DialogCalendarCallback(CalendarCallback, prefix="dialog_calendar"):
    act: DialogCalAct


class CalendarLabels(BaseModel):
    "Schema to pass labels for calendar. Can be used to put in different languages"
    days_of_week: conlist(str, max_length=7, min_length=7) = ["mo", "tu", "we", "th", "fr", "sa", "su"]
    months: conlist(str, max_length=12, min_length=12) = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    cancel_caption: str = Field(default="Отмена", description="Caption for Cancel button")
    back_caption: str = Field(default="Назад", description="Caption for Back button")
    today_caption: str = Field(default="Сегодня", description="Caption for Cancel button")
    save_caption: str = Field(default="Сохранить", description="Сохраняет выбранные даты")


HIGHLIGHT_FORMAT = "[{}]"
SELECT_DAY_FORMAT = "✅ {}"


def highlight(text):
    return HIGHLIGHT_FORMAT.format(text)


def select(text):
    return SELECT_DAY_FORMAT.format(text)


def superscript(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-=()"
    super_s = "ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿˢᵀᵁⱽᵂˣʸᶻᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖ۹ʳˢᵗᵘᵛʷˣʸᶻ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾"
    output = ""
    for i in text:
        output += super_s[normal.index(i)] if i in normal else i
    return output


def subscript(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-=()"
    sub_s = "ₐ₈CDₑբGₕᵢⱼₖₗₘₙₒₚQᵣₛₜᵤᵥwₓᵧZₐ♭꜀ᑯₑբ₉ₕᵢⱼₖₗₘₙₒₚ૧ᵣₛₜᵤᵥwₓᵧ₂₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎"
    output = ""
    for i in text:
        output += sub_s[normal.index(i)] if i in normal else i
    return output
