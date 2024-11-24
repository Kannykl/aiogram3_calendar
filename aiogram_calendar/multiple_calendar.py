import calendar
from datetime import datetime, timedelta

from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from .common import GenericCalendar
from .schemas import MultipleCalendarCallback, SimpleCalAct, select


class MultipleCalendar(GenericCalendar):

    ignore_callback = MultipleCalendarCallback(act=SimpleCalAct.ignore).pack()  # placeholder for no answer buttons

    async def start_calendar(
        self,
        year: int = datetime.now().year,
        month: int = datetime.now().month,
        day: int = datetime.now().day,
    ) -> InlineKeyboardMarkup:
        """
        Creates an inline keyboard with the provided year and month
        Args:
            year: year to start the calendar
            month: month to start the calendar
            day: day to start the calendar
            selected_days: list of selected days

        Returns:
            InlineKeyboardMarkup: InlineKeyboardMarkup with the calendar
        """

        today = datetime.now()
        now_month, now_year, now_day = today.month, today.year, today.day

        def select_day(picked_days):
            selected_days = picked_days or []
            if day in selected_days:
                return select(day)

            return day

        # building a calendar keyboard
        kb = []

        # Week Days
        week_days_labels_row = []
        for weekday in self._labels.days_of_week:
            week_days_labels_row.append(
                InlineKeyboardButton(
                    text=weekday,
                    callback_data=MultipleCalendarCallback(
                        act=SimpleCalAct.select_weekdays, month=now_month, year=now_year, day=now_day, weekday=weekday
                    ).pack(),
                )
            )
        kb.append(week_days_labels_row)

        # Calendar rows - Days of month
        month_calendar = calendar.monthcalendar(year, month)

        for week in month_calendar:
            days_row = []
            for day in week:
                if day == 0 or (month == now_month and year == now_year and day < now_day):
                    days_row.append(InlineKeyboardButton(text=" ", callback_data=self.ignore_callback))
                    continue

                days_row.append(
                    InlineKeyboardButton(
                        text=select_day(self.selected_days),
                        callback_data=MultipleCalendarCallback(
                            act=SimpleCalAct.day, year=year, month=month, day=day
                        ).pack(),
                    )
                )
            kb.append(days_row)

        cancel_row = [
            InlineKeyboardButton(
                text=self._labels.cancel_caption,
                callback_data=MultipleCalendarCallback(act=SimpleCalAct.cancel).pack(),
            ),
            InlineKeyboardButton(
                text=self._labels.save_caption,
                callback_data=MultipleCalendarCallback(act=SimpleCalAct.save_days).pack(),
            ),
            InlineKeyboardButton(text=" ", callback_data=self.ignore_callback),
        ]
        kb.append(cancel_row)

        return InlineKeyboardMarkup(row_width=7, inline_keyboard=kb)

    async def _update_calendar(self, query: CallbackQuery):
        new_markup = await self.start_calendar()
        await query.message.edit_reply_markup(reply_markup=new_markup)

    async def process_weekdays_select(self, data, query) -> list[str]:
        dates = self._get_weekday_dates(data.year, data.month, data.weekday)

        return dates

    async def process_selection(self, query: CallbackQuery, data: MultipleCalendarCallback) -> tuple:
        """
        Process the callback_query. This method generates a new calendar if forward or
        backward is pressed. This method should be called inside a CallbackQueryHandler.
        :param query: callback_query, as provided by the CallbackQueryHandler
        :param data: callback_data, dictionary, set by calendar_callback
        :return: Returns a tuple (Boolean,datetime), indicating if a date is selected
                    and returning the date if so.
        """
        return_data = (False, None)

        if data.act == SimpleCalAct.ignore:
            await query.answer(cache_time=60)
            return return_data

        if data.act == SimpleCalAct.day:
            return await self.process_day_select(data, query)

        if data.act == SimpleCalAct.select_weekdays:
            return True, await self.process_weekdays_select(data, query)

        return return_data

    async def process_day_select(self, data, query):
        """Checks selected date is in allowed range of dates"""
        date = datetime(int(data.year), int(data.month), int(data.day))

        if self.min_date and self.min_date > date:
            await query.answer(
                f'The date have to be later {self.min_date.strftime("%d/%m/%Y")}', show_alert=self.show_alerts
            )
            return False, None

        elif self.max_date and self.max_date < date:
            await query.answer(
                f'The date have to be before {self.max_date.strftime("%d/%m/%Y")}', show_alert=self.show_alerts
            )
            return False, None

        await query.message.delete_reply_markup()  # removing inline keyboard

        return True, [str(date.day)]

    def _get_weekday_dates(self, year, month, weekday):
        if isinstance(weekday, str):
            weekday_map = {day.lower(): num for num, day in enumerate(calendar.day_name)}
            weekday = weekday_map[weekday.lower()]

        # Get the first day of the month
        first_day = datetime(year, month, 1)

        # Find the first occurrence of the desired weekday
        days_ahead = weekday - first_day.weekday()
        if days_ahead < 0:
            days_ahead += 7

        first_occurrence = first_day + timedelta(days=days_ahead)

        # Get all occurrences
        dates = []
        current_date = first_occurrence

        while current_date.month == month:
            dates.append(str(current_date.day))
            current_date += timedelta(days=7)

        return dates
