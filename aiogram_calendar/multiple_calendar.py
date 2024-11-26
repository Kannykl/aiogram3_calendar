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
        with_next_button: bool = False,
    ) -> InlineKeyboardMarkup:
        """
        Creates an inline keyboard with the provided year and month
        Args:
            with_next_button: Добавлять кнопку сохранения
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

            if str(day) in selected_days:
                return select(day)

            return day

        # building a calendar keyboard
        kb = []
        kb.append(
            [
                InlineKeyboardButton(
                    text="Вы можете выбрать день недели или конкретную дату",
                    callback_data=self.ignore_callback,
                )
            ]
        )

        # Week Days
        week_days_labels_row = []
        selected_weekdays = self._get_selected_weekdays()
        for weekday in self._labels.days_of_week:
            week_days_labels_row.append(
                InlineKeyboardButton(
                    text=str(weekday),
                    callback_data=MultipleCalendarCallback(
                        act=(
                            SimpleCalAct.unselect_weekdays
                            if weekday in selected_weekdays
                            else SimpleCalAct.select_weekdays
                        ),
                        month=now_month,
                        year=now_year,
                        day=now_day,
                        weekday=weekday,
                    ).pack(),
                )
            )
        kb.append(week_days_labels_row)

        # Calendar rows - Days of month
        month_calendar = calendar.monthcalendar(year, month)
        for week in month_calendar:
            days_row = []
            for day in week:
                if day == 0:
                    days_row.append(InlineKeyboardButton(text=" ", callback_data=self.ignore_callback))
                    continue

                days_row.append(
                    InlineKeyboardButton(
                        text=str(select_day(self.selected_days)),
                        callback_data=MultipleCalendarCallback(
                            act=(SimpleCalAct.unselect_day if str(day) in self.selected_days else SimpleCalAct.day),
                            year=year,
                            month=month,
                            day=day,
                        ).pack(),
                    )
                )
            kb.append(days_row)

        cancel_row = [
            InlineKeyboardButton(
                text=self._labels.back_caption,
                callback_data=MultipleCalendarCallback(act=SimpleCalAct.cancel).pack(),
            ),
        ]
        if with_next_button:
            cancel_row.extend(
                [
                    InlineKeyboardButton(text=" ", callback_data=self.ignore_callback),
                    InlineKeyboardButton(
                        text=self._labels.save_caption,
                        callback_data=MultipleCalendarCallback(act=SimpleCalAct.save_days).pack(),
                    ),
                ]
            )
        kb.append(cancel_row)

        return InlineKeyboardMarkup(row_width=7, inline_keyboard=kb)

    async def _update_calendar(self, query: CallbackQuery):
        new_markup = await self.start_calendar()
        await query.message.edit_reply_markup(reply_markup=new_markup)

    async def process_weekdays_select(self, data, query) -> str:
        dates = self._get_weekday_dates(data.year, data.month, data.weekday)
        return ",".join(dates)

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
            day = await self.process_day_select(data, query)
            return True, f"add:{day}"

        if data.act == SimpleCalAct.unselect_day:
            day = await self.process_day_select(data, query)
            return True, f"remove:{day}"

        if data.act == SimpleCalAct.select_weekdays:
            dates = await self.process_weekdays_select(data, query)
            return True, f"add:{dates}"

        if data.act == SimpleCalAct.unselect_weekdays:
            dates = await self.process_weekdays_select(data, query)
            return True, f"remove:{dates}"

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

        return str(date.day)

    def _get_weekday_dates(self, year, month, weekday):
        weekday_map = {
            "пн": 0,
            "вт": 1,
            "ср": 2,
            "чт": 3,
            "пт": 4,
            "сб": 5,
            "вс": 6,
        }
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

    def _get_selected_weekdays(self):
        """
        Convert a date to its weekday name.

        Args:
            date_input: Can be either:
                - string in format 'YYYY-MM-DD' or 'DD.MM.YYYY'
                - list/tuple of integers [day, month, year]
                - datetime object

        Returns:
            str: Abbreviated weekday name in specified language
        """
        weekday_map_ru = {0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "вс"}
        selected_weekdays = set()
        now_year, now_month = datetime.now().year, datetime.now().month
        dates = [f"{now_year}-{now_month}-{day}" for day in self.selected_days]

        for date in dates:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            weekday = date_obj.weekday()
            day = weekday_map_ru[weekday]
            selected_weekdays.add(day)

        return selected_weekdays