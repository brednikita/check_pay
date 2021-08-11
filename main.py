# Импортим библы
import asyncio
import logging
import random
from datetime import date

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.utils.exceptions import BotBlocked

import buttons
import core
import settings

""" Набор символов для генератора секретных ключей """
chars = 'abcdefghijklnopqrstuvwxyz1234567890'
""" Логгер """
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
""" Старт бота """
bot = Bot(token=settings.API_TOKEN)
""" Это для антифлуда """
storage = MemoryStorage()
""" Это тоже там для всего остального [x_x] """
dp = Dispatcher(bot, storage=storage)


def create_secret_key(t_id):
    """ Возвращает сгенерированный набор символов"""
    secret = ''
    for i in range(10):
        secret += random.choice(chars)
    core.setSQL(t_id, 'secret', secret)
    return secret


async def anti_flood(*args, **kwargs):
    """ Антифлуд """
    m = args[0]
    await m.answer("Слишком часто :)")


def check_limit(t_id, username):
    """ Возвращает дату до которой активна подписка """
    return date(core.getSQL(t_id, username, 'year_limit'), core.getSQL(t_id, username, 'month_limit'),
                core.getSQL(t_id, username, 'day_limit'))


def check_access(t_id, username):
    """ Уточняем какой сегодня день """
    now = date.today()

    """ Получаем дату до которой активна подписка """
    limit = check_limit(t_id, username)

    """ Проверяем есть ли у пользователя доступный лимит подписки """
    if limit > now:
        logging.info("У {} {} есть лимит".format(t_id, username))
        return True
    elif now > limit:
        logging.info("У {} {} нет лимита".format(t_id, username))
        return False
    elif now == limit:
        logging.info("У {} {} есть лимит".format(t_id, username))
        return True


def create_pay(t_id):
    """ Делаем секрет ключ """
    secret = create_secret_key(t_id)

    """ Генерируем ссылку на оплату """
    return core.qiwipay(secret, settings.default_tariff)


async def check_user(t_id, username):
    """ Функция возвращает текст, который соответствует условиям - есть ли чел в чате и есть ли у него подписка"""

    """ Для начала глянем есть ли чел в чате"""
    member = await bot.get_chat_member(user_id=t_id, chat_id=settings.public_id)

    """ Проверяем есть ли подписка у чела """
    access = check_access(t_id, username)

    """ Подготовим вывод кнопок """
    reply_markup = ''

    """ 1) участник паблика, нет подписки - удалить из паблика, отправить ссылку на оплату """
    """ 2) участник паблика, есть подписка - поцеловать в залупу и пожелать хорошего дня """
    """ 3) не участник паблика, нет подписки - отправить ссылку на подписку """
    """ 4) не участник паблика, есть подписка - отправить ссылку на паблик """
    if member.is_chat_member() and not access:

        """ Подготавливаем ссылку для оплаты """
        payment = create_pay(t_id)

        """ Кикаем из паблика """
        await bot.kick_chat_member(settings.public_id, t_id)

        """ Если есть ошибка, то сообщим об этом и перенаправим на менеджера """
        if payment == 'error':
            start_text = settings.in_chat_and_not_access_and_error
            reply_markup = ''
        else:
            """ Если нет, то отправляем ссылку на оплату """
            start_text = '{} {}'.format(settings.in_chat_and_not_access, payment)
            reply_markup = buttons.pay_buttons
    elif member.is_chat_member() and access:

        """ Генерируем ссылку на вступление в чат """
        link = await bot.create_chat_invite_link(settings.public_id)
        limit = check_limit(t_id, username)
        start_text = settings.in_chat_and_access(link, limit)
        reply_markup = ''
    elif not member.is_chat_member() and not access:

        """ Подготавливаем ссылку для оплаты """
        payment = create_pay(t_id)

        """ Если есть ошибка, то сообщим об этом и перенаправим на менеджера """
        if payment == 'error':
            start_text = settings.not_in_chat_and_not_access_and_error
            reply_markup = ''
        else:

            """ Если нет, то отправляем ссылку на оплату """
            start_text = '{} {}'.format(settings.not_in_chat_and_not_access, payment)
            reply_markup = buttons.pay_buttons
    elif not member.is_chat_member() and access:

        """ Генерируем ссылку на вступление в чат """
        link = await bot.create_chat_invite_link(settings.public_id)
        limit = check_limit(t_id, username)

        """ Если чел уже удалялся из кнала, то добавляем разбаниваем его """
        if member.status == 'kicked':
            await bot.unban_chat_member(settings.public_id, t_id, True)
        start_text = settings.in_chat_and_access(link, limit)
        reply_markup = ''
    return start_text, reply_markup


""" Обработчик команды /start """


@dp.message_handler(commands=['start'])
@dp.throttled(anti_flood, rate=3)
async def send_welcome(message: types.Message):
    """ Получаем необходимые данные юзера """
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    t_id = message.from_user.id

    """ Чтобы в логах было понятнее - делаем разделитель """
    logging.info("====== {} {} {} {} ======".format(t_id, username, first_name, last_name))
    logging.info('{} {} {} {} запустил бот.'.format(t_id, username, first_name, last_name))

    """
    Костль на проверку есть ли юзер в базе.
    Работает по принципу костыля из core.py getSQL,
    который загоняет юзера в БД, если по нему нет никаких данных
    """
    a = core.getSQL(t_id, username, 'id')

    start_text, reply_markup = await check_user(t_id, username)

    """ Отправляем приветствие """
    await message.reply(start_text, reply_markup=reply_markup, parse_mode='HTML')


""" Обработчик нажатий кнопок """


@dp.callback_query_handler()
@dp.throttled(anti_flood, rate=1)
async def callback_query(callback_query: types.CallbackQuery):
    """ Получаем необходимые данные пользователя """
    query = callback_query.data
    username = callback_query.from_user.username
    t_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    last_name = callback_query.from_user.last_name

    """ Разделитель в логах """
    logging.info("====== {} {} {} {} ======".format(t_id, username, first_name, last_name))

    text = ''
    text_to_admin = ''

    """ Нажата кнопка 'Я оплатил' """
    if query == 'pay_check':

        """ Проверим есть ли записанный секретный ключ в БД для этого юзера """
        if core.getSQL(t_id, username, 'secret') != '':

            """ Если секретный ключ есть, значит поищем в истории QIWI платежи по этому ключу """
            payment = core.qiwicheck(t_id, username, first_name, last_name)

            """ Рапортуем юзеру и админу """
            if payment == settings.default_tariff:
                text_to_admin = ('✅ Username: @{}' +
                                 '\n✅ T_id: {}' +
                                 '\n✅ First name: {}' +
                                 '\n✅ Last name: {}' +
                                 '\n✅ Сумма: {} Руб' +
                                 '\n✅ Secret: {}').format(username, t_id, first_name, last_name, payment,
                                                          core.getSQL(t_id, username, 'secret'))

                """ И обнуляем его секретный ключ в БД """
                core.setSQL(t_id, 'secret', '')

                """ Накидываем лимит на месяц """
                core.setLimit(t_id, username, 1)

                """ Получаем текста, которые отправим юзеру """
                text, reply_markup = await check_user(t_id, username)

                """ Логируем """
                logging.info('{} {} прислал денег.'.format(t_id, username))

            elif payment == 'False':
                """ Если оплаты нет - сообщаем юзеру и админу """
                text = settings.no_payment
                text_to_admin = '{} проверяет оплату, но средства не появились на кошельке'.format(username)
                reply_markup = buttons.pay_buttons

                """ Логируем """
                logging.info(
                    '{} {} {} {} чекает оплату, но она еще не пришла.'.format(t_id, username, first_name, last_name))
            elif payment == 'error':
                """ А это на случай ошибки """
                text = settings.error_payment
                text_to_admin = '{} у не происходит запрос к qiwi api'.format(username)
                reply_markup = ''

        else:
            """
            Если секрет ключ пуст, то это значит, что подписку уже оплатили и она действует, 
            ибо секретный ключ удаляется только при положительном результате проверки оплаты.
            Значит подписку когда-то оплачивали и она уже не действует
            """
            text, reply_markup = await check_user(t_id, username)

        """ Проверим, что текс переменная текста не пустая и отправляем сообщение юзеру """
        if text != '':
            await bot.send_message(chat_id=callback_query.from_user.id,
                                   parse_mode="HTML",
                                   text=text, reply_markup=reply_markup)

        """ Проверим, что текс переменная текста не пустая и отправляем сообщение админу """
        if text_to_admin != '':
            await bot.send_message(settings.admin, text=text_to_admin, parse_mode='HTML')


""" Слушаем ошибки """


@dp.errors_handler()
async def message_not_modified_handler(update, error):
    await bot.send_message('52495072', text='❗️ В боте опять что-то сломалось... Ошибка: {}'.format(error))
    return True


async def kicker():
    """ Кикает из юзеров из канала, если нет подписки """

    """ Получим все записи из БД """
    rows = core.allSQL()

    """ Узнаем какой сегодня день """
    now = date.today()

    for row in rows:
        if row[1]:
            """ Узнаем какой лимит у чела row в БД """
            limit = date(row[3], row[4], row[5])

            """ Если лимита нет, то генерируем соответствуеющее сообщение """
            if now > limit and row[6] == '':
                text, reply_markup = await check_user(row[1], row[2])
                try:
                    await bot.send_message(row[1], text=text, reply_markup=reply_markup, parse_mode='HTML')
                except BotBlocked:
                    print('Этот пользователь {} заблокировал бот').format(row[2])


def repeat(coro, loop):
    """ Цикл для проверки юзеров на лимит """
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(10, repeat, coro, loop)


if __name__ == '__main__':
    """
    Тут я, пожалуй, скажу спасибо самому себе, а еще Диме Маслиеву и Крыму <3
    Кто знает, тот поймет, понимаете ли...
    Ну типа можно сказать наверное еще что-нибудь ._.
    Кайф имейте, господа. Счастья, радости, удачи, конфет по-слаще o_o
    """
    loop = asyncio.get_event_loop()
    loop.call_later(10, repeat, kicker, loop)
    executor.start_polling(dp, skip_updates=True)
