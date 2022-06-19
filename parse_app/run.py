import time

from bs4 import BeautifulSoup
import requests

import httplib2
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.errors import HttpError
import psycopg2

# Файл, полученный в Google Developer Console
CREDENTIALS_FILE = 'credentials.json'
# ID Google Sheets документа (можно взять из его URL)
spreadsheet_id = '1WyB2pG5o52cFtkvG-N5bKN1-pHL7st6sgDgi8hx1fMc'

# Авторизуемся и получаем service — экземпляр доступа к API
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = discovery.build('sheets', 'v4', http=httpAuth)

connection = psycopg2.connect(
    database='orders',
    user='admin',
    password='admin',
    host='db',
    port='5432',
)


def get_data_google_sheet(spreadsheet_id: str, range: str, major_dimension: str) -> dict:
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range,
        majorDimension=major_dimension,
    ).execute()

    return values


def insert_objects_in_db(id_entry: int, order_number: int, price_usd: int, delivery_time: str, dollar_rate: float) -> None:
    try:
        cursor.execute('''INSERT INTO ordersapp_orders (id, order_number, price_usd, delivery_time, price_rub)
                          VALUES (%s, %s, %s, %s, %s);''', (id_entry, order_number, price_usd, delivery_time,
                                                            price_usd * dollar_rate))
    except psycopg2.errors.UniqueViolation:
        pass
    connection.commit()


def update_objects_in_db(id_entry: int, order_number: int, price_usd: int, delivery_time: str, data_google_sheet: dict,
                         dollar_rate: float) -> None:
    # Если номер заказа из Google Sheet не сходится с PostgreSQL, то меняем на тот,
    # который в Google Sheet
    if order_number != int(data_google_sheet['values'][id_entry - 1][1]):
        cursor.execute('UPDATE ordersapp_orders SET order_number=%s WHERE id=%s;',
                       (int(data_google_sheet['values'][id_entry - 1][1]), id_entry))
    # Если цена в долларах из Google Sheet не сходится с PostgreSQL, то меняем на ту,
    # которая в Google Sheet и пересчитываем сумму в рублях и также заменяем
    if price_usd != int(data_google_sheet['values'][id_entry - 1][2]):
        cursor.execute('UPDATE ordersapp_orders SET price_usd=%s, price_rub=%s WHERE id=%s;',
                       (int(data_google_sheet['values'][id_entry - 1][2]),
                        int(data_google_sheet['values'][id_entry - 1][2]) * dollar_rate, id_entry))
    # Если дата заказа из Google Sheet не сходится с PostgreSQL, то меняем на ту,
    # которая в Google Sheet
    if delivery_time != data_google_sheet['values'][id_entry - 1][3]:
        cursor.execute('UPDATE ordersapp_orders SET delivery_time=%s WHERE id=%s;',
                       (data_google_sheet['values'][id_entry - 1][3], id_entry))
    connection.commit()


def delete_objects_in_db(id_entry: int, id_objects_google_sheet: set, id_objects_db: set) -> None:
    cursor.execute('DELETE FROM ordersapp_orders WHERE id=%s;', (id_entry[0],))
    id_objects_google_sheet.remove(id_entry[0])
    id_objects_db.remove(id_entry[0])


cursor = connection.cursor()
id_objects_postgresql = set()
id_objects_google = set()

url_parse = f'https://www.cbr.ru/scripts/XML_daily.asp'

# Делаем запрос к серверу и парсим разметку
headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0"}
response = requests.get(url_parse, headers=headers)
dom = BeautifulSoup(response.text, 'xml')

# Бесконечный цикл чтения файла и добавления из него в БД записей
while True:
    try:
        # Значение колонок в Google Sheet
        all_data = get_data_google_sheet(spreadsheet_id, 'A2:D', 'ROWS')
        # ID заказов в Google Sheet
        id_orders = get_data_google_sheet(spreadsheet_id, 'A2:A', 'ROWS')
        # Получаем курс доллара с сайта ЦБ, меняем запятую на точку, чтоб сразу привести к float
        dollar_exchange_rate = float(dom.find("Valute", {"ID": "R01235"}).find("Value").text.replace(',', '.'))

        # Добавление в БД значений или их изменение
        try:
            for row in all_data['values']:
                # Получаем текущую дату, разбиваем по '.',
                # порядок элементов меняем в обратную сторону и соединяем с символом '.'
                date_delivery = '.'.join(row[3].split('.')[::-1])
                # Если ещё нет строки зачений с таким ID добавлем
                if int(row[0]) not in id_objects_postgresql:
                    insert_objects_in_db(int(row[0]), int(row[1]), int(row[2]), date_delivery,
                                         dollar_exchange_rate)
                # Иначе проверяем, не произошло ли изменений
                else:
                    cursor.execute('SELECT id, order_number, price_usd, delivery_time FROM ordersapp_orders WHERE id=%s;',
                                   (int(row[0]),))
                    for row in cursor.fetchall():
                        # Получаем текущую дату, превращаем её в строку, разбиваем по '-',
                        # порядок элементов меняем в обратную сторону и соединяем с символом '.'
                        date_delivery = '.'.join(str(row[3]).split('-')[::-1])
                        update_objects_in_db(row[0], row[1], row[2], date_delivery, all_data, dollar_exchange_rate)
        # Если нет значений в таблице Google Sheet, прерываем цикл
        except KeyError:
            break

        # Добавление всех ID из Google Sheet в множество
        for order_id in id_orders['values']:
            id_objects_google.add(int(order_id[0]))
        # Получение всех ID в БД
        cursor.execute('SELECT id FROM ordersapp_orders')
        data_db = cursor.fetchall()
        # Если БД пустая, то очищаем множество
        if not data_db:
            id_objects_postgresql.clear()
        # Иначе перебор всех записей из БД
        else:
            for id_obj in data_db:
                # Если нет ID из БД в Google Sheet, то удаляем
                if id_obj[0] not in id_objects_google:
                    delete_objects_in_db(id_obj[0], id_objects_google, id_objects_postgresql)
                # Если нет ID в БД, то добавлем в множество
                elif id_obj[0] not in id_objects_postgresql:
                    id_objects_postgresql.add(id_obj[0])
        time.sleep(1)
    except HttpError:
        continue
