from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

pay_check = InlineKeyboardButton('Я оплатил', callback_data='pay_check')
pay_buttons = InlineKeyboardMarkup(row_width=1).add(pay_check)