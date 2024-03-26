import json
import os
import pandas as pd
import requests
import dotenv
from openpyxl import Workbook
from openpyxl.styles import Font, Border
from openpyxl.styles.borders import Border, Side

dotenv.load_dotenv()

urlOrder = os.getenv('URL_ORDER')
urlSale = os.getenv('URL_SALE')
urlStock = os.getenv('URL_STOCK')
urlIncome = os.getenv('URL_INCOME')
urlOtchet = os.getenv('URL_OTCHET')

token = os.getenv('WB_TOKEN')

headers = {'Authorization': token}

paramsOrder = {'dateFrom': '2024-03-11',
               'flag': 0,
               }
paramsStock = {'dateFrom': '2024-03-11'}
paramsIncome = {'dateFrom': '2024-03-11'}
paramsOtchet = {'dateFrom': '2024-03-11', 'dateTo': '2024-03-18', 'rrdid': 0, 'limit': 100000}


async def get_data(url, headers, params):
    res = requests.get(url=url, headers=headers, params=params)
    return res.json()


async def sort_data(order, income, stochWithIncome):
    sorted_keys = sorted(order)
    order, income, stochWithIncome = ({k: d[k] for k in sorted_keys} for d in (order, income, stochWithIncome))
    return order, income, stochWithIncome


async def generate_json():
    orders_data = await get_data(urlOrder, headers, paramsOrder)
    stock_data = await get_data(urlStock, headers, paramsStock)
    income_data = await get_data(urlIncome, headers, paramsIncome)
    with open("json_files/orders_data.json", "w") as orders:
        json.dump(orders_data, orders)
    with open("json_files/stock_data.json", "w") as orders:
        json.dump(stock_data, orders)
    with open("json_files/income_data.json", "w") as orders:
        json.dump(income_data, orders)


async def process_orders_data(data):
    order = {}
    for items in data:
        if '-' in items['techSize']:
            article = items['supplierArticle'] + ' ' + items['techSize']
        else:
            article = items['supplierArticle'] + items['techSize']

        if article in order:
            order[article]['count'] += 1
        else:
            order[article] = {'count': 1}

    for key in order:
        order[key]['count'] //= 7

    for article in order:
        order[article]['incrise'] = int(round(order[article]['count'] * 1.15))

    return order


async def proc_stock_data(data):
    stock = {}
    for items in data:
        if '-' in items['techSize']:
            article = items['supplierArticle'] + ' ' + items['techSize']
        else:
            article = items['supplierArticle'] + items['techSize']

        if article not in stock:
            stock[article] = {'toClient': items['inWayToClient'],
                              'fromClient': items['inWayFromClient'],
                              'fullQuantity': items['quantityFull'],
                              'quantityWithIncome': 0}
        else:
            stock[article]['toClient'] += items['inWayToClient']
            stock[article]['fromClient'] += items['inWayFromClient']
            stock[article]['quantityWithIncome'] += 0
            stock[article]['fullQuantity'] += items['quantityFull']
    return stock


async def get_stock_with_income(stock, income):
    for article, value in stock.items():
        if article in income:
            stock[article]['quantityWithIncome'] += income[article]['quantity'] + stock[article]['fromClient'] + \
                                                    stock[article]['fullQuantity']
        else:
            stock[article]['quantityWithIncome'] = stock[article]['fromClient'] + stock[article]['fullQuantity']

    return stock


async def get_incomes(data, stock):
    income = {}
    for items in data:
        if '-' in items['techSize']:
            article = items['supplierArticle'] + ' ' + items['techSize']
        else:
            article = items['supplierArticle'] + items['techSize']
        quantity = items['quantity']

        income[article] = {'quantity': quantity}

    for article in stock:
        if article not in income:
            income[article] = {'quantity': 0}

    return income


async def order_w2_2(order_w1):
    order_w2 = {}
    for article in order_w1:
        if article not in order_w2:
            order_w2[article] = {'count': order_w1[article]['count'],
                                 'incrise': order_w1[article]['count'],
                                 'order7Days': 0, }

    for article in order_w2:
        order_w2[article]['incrise'] = int(round(order_w2[article]['incrise'] * 1.3))
        order_w2[article]['order7Days'] = order_w2[article]['incrise'] * 7

    return order_w2


async def initialize():
    with open("json_files/orders_data.json", "r") as orders_data_file, \
            open("json_files/stock_data.json", "r") as stock_data_file, \
            open("json_files/income_data.json", "r") as income_data_file:
        orders_data = json.load(orders_data_file)
        stock_data = json.load(stock_data_file)
        income_data = json.load(income_data_file)

    order = await process_orders_data(orders_data)
    stock = await proc_stock_data(stock_data)
    income = await get_incomes(income_data, stock)

    stock_income = await get_stock_with_income(stock, income)
    order, income, stock_income = await sort_data(order, income, stock_income)
    order_w2 = await order_w2_2(order)

    df1 = pd.DataFrame(order).T
    sheet_name = 'Orders w1'
    df1 = df1.rename(columns={'count': 'Заказы',
                              'incrise': 'Ув 15%'})

    df2 = pd.DataFrame(stock_income).T
    sheet_nameLeftOvers = 'Leftovers, in transit, etc w1'
    df2 = df2.rename(columns={'toClient': 'В пути до клиента',
                              'fromClient': 'В пути от клиента',
                              'fullQuantity': 'Остатки на складе',
                              'quantityWithIncome': 'Остатки на складе с учетом поступлений'})
    df3 = pd.DataFrame(income).T
    df3 = df3.rename(columns={'quantity': 'Поступления'})
    df4 = pd.DataFrame(order_w2).T
    sheet_orders_w2 = 'Orders w2'
    df4 = df4.rename(columns={'count': 'Заказы были',
                              'incrise': 'Ув 30%',
                              'order7Days': 'Заказы за 7 дней'})

    with pd.ExcelWriter('data.xlsx', engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name=sheet_name, startcol=1, startrow=1, index_label='Артикул')
        df2.to_excel(writer, sheet_name=sheet_nameLeftOvers, startcol=1, startrow=1, index_label='Артикул')
        df3.to_excel(writer, sheet_name=sheet_nameLeftOvers, startcol=8, startrow=1, index_label='Артикул')
        df4.to_excel(writer, sheet_name=sheet_orders_w2, startcol=1, startrow=1, index_label='Артикул')
        workbook = writer.book
        worksheet1 = writer.sheets[sheet_name]
        worksheet2 = writer.sheets[sheet_nameLeftOvers]
        worksheet3 = writer.sheets[sheet_orders_w2]

        worksheet1.column_dimensions['B'].width = 25
        columnWight = {'B': 25,
                       'C': 19,
                       'D': 19,
                       'E': 19,
                       'F': 40,
                       'I': 25,
                       'J': 15}

        for column, width in columnWight.items():
            worksheet2.column_dimensions[column].width = width
            worksheet3.column_dimensions[column].width = width

    print(json.dumps(order, indent=3))
    print(json.dumps(order_w2, indent=3))
