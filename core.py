from datetime import date, datetime, timedelta

import json
import logging
import requests
import sqlite3

import settings

from dateutil.relativedelta import relativedelta

""" Настройка логгера """
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


def allSQL():
    """ Возвращает все записи из БД"""
    try:
        conn = sqlite3.connect('sqlite.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM {}".format(settings.db))
        result = cursor.fetchall()
    except sqlite3.DatabaseError as err:
        result = False
        logging.info("Ошибка в БД: {}".format(err))
    else:
        conn.commit()
    conn.close()
    return result


def getSQL(t_id, username, var):
    """ Возвращает конкретные данные из БЛ """
    """ Устанавливаем дефолтный лимит, если юзера нет в базе на -1 день от сегодняшней даты """
    now = date.today()
    default_limit = now - timedelta(days=1)

    try:
        """ Сразу обнуляем результат """
        result = ''

        """ Подключаемся к БД """
        conn = sqlite3.connect('sqlite.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM {}".format(settings.db))

        """ Получаем данные """
        rows = cursor.fetchall()

    except sqlite3.DatabaseError as err:
        """
        Если есть ошибка, то возвражаем результат - False
        Отрицание успеха, так сказать
        """
        result = 'False'
        logging.info("Ошибка в БД у {} {}: ".format(err, t_id, username))
    else:
        """ Если данные пполучены успешно, то парсим их """
        for row in rows:
            """ Проверяем каждую запись на приндлежность к юзеру """
            if row[1] == t_id:
                """ Если принадлежит, то в резултат отписываем значение нужного стобца и отправляем в ретюрн """
                result = row[settings.varSql.index(var)]
                break
            else:
                """ Если не приндалежит, то отправляем в результ False """
                result = 'False'

        """ 
        Ну и если в итоге у нас результат False, то это значит, что юзера в БД еще не было.
        Он пользуется ботом впервые и было бы заебись по этому случаю добавить его в БД!
        Это и есть тот костыль с a = core.getSQL(t_id, username, 'чтоугодно')
        """

        if result == 'False':
            addNewUser = "insert into {} values (NULL, {}, '{}', {},{},{},NULL) ".format(settings.db, t_id,
                                                                                         username, default_limit.year,
                                                                                         default_limit.month,
                                                                                         default_limit.day)

            print('{} {} еще нет в базе, добавляю...'.format(t_id, username))

            cursor.execute(addNewUser)
        conn.commit()
    conn.close()
    return result


def setSQL(t_id, var, text):
    """ Добавляет запись в БД """
    try:
        """ Обнуляем результат """
        result = ''

        """ Подключаемся к БД """
        conn = sqlite3.connect('sqlite.db')
        cursor = conn.cursor()

        """ Делаем запрос """
        cursor.execute('UPDATE {} SET {} = "{}" WHERE t_id = "{}"'.format(settings.db, var, text, t_id))
    except sqlite3.DatabaseError as err:
        """ Если случилась какая-то ошибка, то говорим об этом и в результ шлем False """
        result = False
        logging.info("Ошибка {} в БД у {}: ".format(err, t_id))
    else:
        """ Если все ок - закрываем БД """
        conn.commit()
        conn.close()

        """ Проверка, что запись сохранилась """
        if getSQL(t_id, '', var) == text:
            result = True
        else:
            """ Или не сохранилась """
            result = False

    """ Отправляем в ретюрн результ """
    return result


def qiwipay(secret, amount):
    """ Оплата через QIWI """
    try:
        """ Генерируем ссылку на оплату """
        logging.info('Генерирую ссылку на оплату для secret: {} на сумму {} Руб'.format(secret, amount))
        headers = {'content-type': 'application/json; charset=utf-8', 'accept': 'application/json',
                   'Authorization': '{}'.format(settings.Bearer)}

        """ Задаем лимит жизни заявки на оплату """
        time = '2028-03-02T08:44:07+03:00'

        """ Задаем параметры """
        parameters = {
            'amount': {
                'currency': 'RUB',
                'value': amount
            },
            'expirationDateTime': time,
            'comment': secret}

        """ Отправляем запрос """
        r = requests.put('https://api.qiwi.com/partner/bill/v1/bills/{}'.format(secret), json=parameters,
                         headers=headers)

        """ Смотрим что по статусу запроса """
        if r.status_code == 200:
            """ Парсим результат и заносим в результ ссылку на оплату, которую мы сгенерировали """
            responseGet = json.loads(r.text)
            result = responseGet['payUrl']
        else:
            """ А если ошибка произошла, ебанарот... то сообщим об этом всем вообще """
            logging.info("В модуле core.py в qiwipay произошла ошибка! Status_code: {}".format(r.status_code))
            return "error"
    except BaseException:
        """ Тоже реакция на ошибки, но на другие """
        logging.info("В модуле core.py в qiwipay произошла ошибка!")
        result = 'error'

    """ Отправляем результат в ретюрн """
    return result


def qiwicheck(t_id, username, first_name, last_name):
    """ Проверка оплаты QIWI """

    """ Задаем параметры """
    s = requests.Session()
    s.headers['authorization'] = settings.api_access_token
    parameters = {'rows': '10'}

    try:

        """ Отправляем запрос """
        h = s.get('https://edge.qiwi.com/payment-history/v2/persons/' + settings.my_login + '/payments',
                  params=parameters)

    except BaseException:
        return 'error'

    else:
        """ Парсим ответ """
        responseGet = json.loads(h.text)

        """ Выводим статус запроса """
        logging.info("Статус запроса в QIWI: {}".format(h.status_code))

        """ Сразу думаем, будто оплаты не было """
        request = 'False'

        """ Парсим полученные данные """
        for item in responseGet['data']:

            """ Если хоть у одного платежа в комментах есть секретный ключ юзера, то..."""
            if getSQL(t_id, username, 'secret') == item['comment']:

                """ Сообщаем, что есть транзакция """
                print("{} {} {} {} Есть транзакция - {} Руб.".format(t_id, username, first_name, last_name,
                                                                     item['sum']['amount']))
                return item['sum']['amount']
            else:
                """ Если секрет ключа нет, то говорим об этом """
                request = 'False'

        """ Передаем результат в ретюрн """
        return request


def setLimit(t_id, username, month):
    """ Устанавливает лимит пользователя """

    """ Сразу прикидываем какое будет число через месяц """
    limit = datetime.today() + relativedelta(months=+month)

    """ И прописываем лимит в БД """
    setSQL(t_id, "year_limit", limit.year)
    setSQL(t_id, "month_limit", limit.month)
    setSQL(t_id, "day_limit", limit.day)

    """ Сообщаем об этом """
    print("{} {} установлен лимит до: {}{}{}".format(t_id, username, limit.year, limit.month, limit.day))
