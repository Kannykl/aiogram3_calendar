import calendar
from datetime import datetime, timedelta

from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from .common import GenericCalendar
from .schemas import SimpleCalAct, SimpleCalendarCallback, highlight, superscript


class SimpleCalendar(GenericCalendar):

    ignore_callback = SimpleCalendarCallback(act=SimpleCalAct.ignore).pack()  # placeholder for no answer buttons

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

        Returns:
            InlineKeyboardMarkup: InlineKeyboardMarkup with the calendar
        """

        today = datetime.now()
        now_weekday = self._labels.days_of_week[today.weekday()]
        now_month, now_year, now_day = today.month, today.year, today.day

        def highlight_month():
            month_str = self._labels.months[month - 1]
            if now_month == month and now_year == year:
                return highlight(month_str)
            return month_str

        def highlight_weekday():
            if now_month == month and now_year == year and now_weekday == weekday:
                return highlight(weekday)
            return weekday

        def format_day_string():
            date_to_check = datetime(year, month, day)
            if self.min_date and date_to_check < self.min_date:
                return superscript(str(day))
            elif self.max_date and date_to_check > self.max_date:
                return superscript(str(day))
            return str(day)

        def highlight_day():
            day_string = format_day_string()
            if now_month == month and now_year == year and now_day == day:
                return highlight(day_string)
            return day_string

        # building a calendar keyboard
        kb = []

        # inline_kb = InlineKeyboardMarkup(row_width=7)
        # First row - Year
        first_row = []

        first_row.append(
            InlineKeyboardButton(
                text=str(year) if year != now_year else highlight(year), callback_data=self.ignore_callback
            )
        )

        first_row.append(InlineKeyboardButton(text=highlight_month(), callback_data=self.ignore_callback))
        kb.append(first_row)

        second_row = []
        if year == now_year and month == now_month:
            second_row.append(InlineKeyboardButton(text=" ", callback_data=self.ignore_callback))

        else:
            second_row.append(
                InlineKeyboardButton(
                    text="<",
                    callback_data=SimpleCalendarCallback(act=SimpleCalAct.prev_m, year=year, month=month, day=1).pack(),
                )
            )

        second_row.append(
            InlineKeyboardButton(
                text=">",
                callback_data=SimpleCalendarCallback(act=SimpleCalAct.next_m, year=year, month=month, day=1).pack(),
            )
        )
        kb.append(second_row)

        # Week Days
        week_days_labels_row = []
        for weekday in self._labels.days_of_week:
            week_days_labels_row.append(
                InlineKeyboardButton(text=highlight_weekday(), callback_data=self.ignore_callback)
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
                        text=highlight_day(),
                        callback_data=SimpleCalendarCallback(
                            act=SimpleCalAct.day, year=year, month=month, day=day
                        ).pack(),
                    )
                )
            kb.append(days_row)

        # nav today & cancel button
        cancel_row = []

        cancel_row.append(
            InlineKeyboardButton(
                text=self._labels.cancel_caption,
                callback_data=SimpleCalendarCallback(act=SimpleCalAct.cancel, year=year, month=month, day=day).pack(),
            )
        )
        cancel_row.append(InlineKeyboardButton(text=" ", callback_data=self.ignore_callback))
        cancel_row.append(
            InlineKeyboardButton(
                text=self._labels.today_caption,
                callback_data=SimpleCalendarCallback(act=SimpleCalAct.today, year=year, month=month, day=day).pack(),
            )
        )
        kb.append(cancel_row)
        return InlineKeyboardMarkup(row_width=7, inline_keyboard=kb)

    async def _update_calendar(self, query: CallbackQuery, with_date: datetime):
        await query.message.edit_reply_markup(
            reply_markup=await self.start_calendar(int(with_date.year), int(with_date.month))
        )

    async def process_selection(self, query: CallbackQuery, data: SimpleCalendarCallback) -> tuple:
        """
        Process the callback_query. This method generates a new calendar if forward or
        backward is pressed. This method should be called inside a CallbackQueryHandler.
        :param query: callback_query, as provided by the CallbackQueryHandler
        :param data: callback_data, dictionary, set by calendar_callback
        :return: Returns a tuple (Boolean,datetime), indicating if a date is selected
                    and returning the date if so.
        """
        return_data = (False, None)

        # processing empty buttons, answering with no action
        if data.act == SimpleCalAct.ignore:
            await query.answer(cache_time=60)
            return return_data

        temp_date = datetime(int(data.year), int(data.month), 1)

        # user picked a day button, return date
        if data.act == SimpleCalAct.day:
            return await self.process_day_select(data, query)

        # user navigates to previous year, editing message with new calendar
        if data.act == SimpleCalAct.prev_y:
            prev_date = datetime(int(data.year) - 1, int(data.month), 1)
            await self._update_calendar(query, prev_date)

        # user navigates to next year, editing message with new calendar
        if data.act == SimpleCalAct.next_y:
            next_date = datetime(int(data.year) + 1, int(data.month), 1)
            await self._update_calendar(query, next_date)

        # user navigates to previous month, editing message with new calendar
        if data.act == SimpleCalAct.prev_m:
            prev_date = temp_date - timedelta(days=1)
            await self._update_calendar(query, prev_date)

        # user navigates to next month, editing message with new calendar
        if data.act == SimpleCalAct.next_m:
            next_date = temp_date + timedelta(days=31)

            await self._update_calendar(query, next_date)

        if data.act == SimpleCalAct.today:
            next_date = datetime.now()

            if next_date.year != int(data.year) or next_date.month != int(data.month):
                await self._update_calendar(query, datetime.now())

            else:
                await query.answer(cache_time=60)

        if data.act == SimpleCalAct.cancel:
            await query.message.delete_reply_markup()

        return return_data
