""" Telegram ID администратора """
admin = 52495072

""" Логин в телеграмме менеджера """
manager_login = '@angry_shib'

""" Телеграмм ID канала """
public_id = '-1001548717098'

""" Название канала """
public_name = 'КАНАЛ'

""" Стандартный тариф для оплаты """
default_tariff = 1

""" Токен бота """
API_TOKEN = '1912430264:AAET1rcUJk6MVKnngPo5rqCEtkLAaQEKXTU'

""" Имя БД """
db = 'users'

""" Имена столбцов в БД """
varSql = ['id', 't_id', 'username', 'year_limit', 'month_limit', 'day_limit', 'secret']

""" Токен  QIWI. Получить можно получить здесь https://qiwi.com/api"""
api_access_token = 'Bearer a1f0add3fb5216adb908f73a764aa16c'

""" Bearer QIWI """
Bearer = 'Bearer eyJ2ZXJzaW9uIjoiUDJQIiwiZGF0YSI6eyJwYXlpbl9tZXJjaGFudF9zaXRlX3VpZCI6ImI3dndtdC0wMCIsInVzZXJfaWQiOiI3OTUxNTI4NjEwMCIsInNlY3JldCI6IjhjZTY4NzUwMmE4YjM0MDEyMjQ4Zjc0OTA4ODM3ZjUwY2EyZGUzZTM5ZDIxOGYxNzY0MmFjYjMyYzZkOGIzNDkifX0='

""" Номер QIWI Кошелька в формате +79991112233 """
my_login = '79515286100'

""" Сообщение если чел есть в канале, но кончилась подписка и при этом возникла ошибка генерирования ссылки оплаты """
in_chat_and_not_access_and_error = ('Ваша подписка на канал <b>{}</b> закончилась. Вам необходимо оплатить подписку\n' +
                                    'Однако в модуле оплаты произошла ошибка, мы разбираемся в проблеме.\n' +
                                    'Для оплаты обратись к {}').format(public_name, manager_login)

""" Сообщение если чел есть в канале, но кончилась подписка  """
in_chat_and_not_access = ('Ваша подписка на канал <b>{}</b> закончилась!' +
                          '\nПосле оплаты нажмите кнопку "Я оплатил"!'
                          '\nСсылка на оплату подписки:').format(public_name)

""" Сообщение если чел есть в канале и есть подписка """


def in_chat_and_access(link, limit):
    return ('Добро пожаловать!\nВаша подписка активирована и действительна до {}' +
            '\nСсылка на доступ: {}').format(limit, link['invite_link'])


""" Сообщение если чела никогда не было в паблике и нет подписки и при это есть ошибка генерирования ссылки оплаты """
not_in_chat_and_not_access_and_error = ('У вас нет подписки на <b>{}</b>. Вам необходимо оплатить подписку\n' +
                                        'Однако в модуле оплаты произошла ошибка, мы разбираемся в проблеме.\n' +
                                        'Для оплаты обратись к {}').format(public_name, manager_login)

""" Сообщение если чела никогда не было в паблике и нет подписки """
not_in_chat_and_not_access = ('У вас нет подписки на канал <b>{}</b>!' +
                              '\nПосле оплаты нажмите кнопку "Я оплатил"!' +
                              '\nСсылка на оплату подписки:').format(public_name)

""" Сообщение, если оплата еще не поступила """
no_payment = ('Оплата еще не поступила\n' +
              'При возникновении проблем с оплатой напишите администратору {}').format(manager_login)

""" Сообщение при ошибки оплаты """
error_payment = ('Произошла ошибка.\n' +
                 'При возникновении проблем с оплатой напишите администратору {}').format(manager_login)
