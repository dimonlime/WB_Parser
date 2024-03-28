import json
import os
import pandas as pd
import requests
import dotenv
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, Border
from openpyxl.styles.borders import Border, Side

dotenv.load_dotenv()

urlOrder = os.getenv('URL_ORDER')
urlSale = os.getenv('URL_SALE')
urlStock = os.getenv('URL_STOCK')
urlIncome = os.getenv('URL_INCOME')

token = os.getenv('WB_TOKEN')

headers = {'Authorization': token}

dateFrom = '2024-03-11'

paramsOrder = {'dateFrom': dateFrom,
               'flag': 0,
               }
paramsSales = {'dateFrom': dateFrom}
paramsStock = {'dateFrom': dateFrom}
paramsIncome = {'dateFrom': dateFrom}
date_from_obj = datetime.strptime(dateFrom, '%Y-%m-%d').date()
date_to_obj = date_from_obj + timedelta(days=7)


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
    sales_data = await get_data(urlSale, headers, paramsSales)
    with open("json_files/orders_data.json", "w") as orders:
        json.dump(orders_data, orders)
    with open("json_files/stock_data.json", "w") as stock:
        json.dump(stock_data, stock)
    with open("json_files/income_data.json", "w") as income:
        json.dump(income_data, income)
    with open("json_files/sales_data.json", "w") as sales:
        json.dump(sales_data, sales)


async def process_orders_data(data, date_from, date_to):
    order = {}
    for items in data:
        date = items['date']
        date_obj = datetime.strptime(date[:10], '%Y-%m-%d').date()

        if (date_from <= date_obj < date_to):
            if '-' in items['techSize']:
                article = items['supplierArticle'] + ' ' + items['techSize']
            else:
                article = items['supplierArticle'] + items['techSize']
            if article in order:
                order[article]['count'] += 1
            else:
                order[article] = {'count': 1}

    # print(json.dumps(order, indent=4))

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


async def get_incomes(data, stock, dateFrom, dateTo):
    income = {}
    for items in data:
        date = items['date']
        date_obj = datetime.strptime(date[:10], '%Y-%m-%d').date()

        if (dateFrom <= date_obj < dateTo):
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


async def percent_buy(data_orders, data_sales, date_from, date_to):
    orders_buy_percent = {}

    # Подсчитываем заказы в заданном диапазоне дат
    for item in data_orders:
        date = item['date']
        date_obj = datetime.strptime(date[:10], '%Y-%m-%d').date()

        if date_from <= date_obj < date_to:
            if '-' in item['techSize']:
                article = item['supplierArticle'] + ' ' + item['techSize']
            else:
                article = item['supplierArticle'] + item['techSize']

            if article in orders_buy_percent:
                orders_buy_percent[article]['count_orders'] += 1
            else:
                orders_buy_percent[article] = {'count_orders': 1, 'count_sales': 0, 'percent': 0}

    # Подсчитываем продажи для каждого артикула
    for sale in data_sales:
        date = sale['date']
        date_obj = datetime.strptime(date[:10], '%Y-%m-%d').date()

        if date_from <= date_obj < date_to:
            if '-' in sale['techSize']:
                article = sale['supplierArticle'] + ' ' + sale['techSize']
            else:
                article = sale['supplierArticle'] + sale['techSize']

            if article in orders_buy_percent:
                orders_buy_percent[article]['count_sales'] += 1

    # Рассчитываем процент купленных заказов
    for article, counts in orders_buy_percent.items():
        if counts['count_orders'] > 0:
            counts['percent'] = round((counts['count_sales'] / counts['count_orders']), 2)

    return orders_buy_percent


async def initialize():
    with open("json_files/orders_data.json", "r") as orders_data_file, \
            open("json_files/stock_data.json", "r") as stock_data_file, \
            open("json_files/income_data.json", "r") as income_data_file, \
            open("json_files/sales_data.json", "r") as sales_data_file:
        orders_data = json.load(orders_data_file)
        stock_data = json.load(stock_data_file)
        income_data = json.load(income_data_file)
        sales_data = json.load(sales_data_file)

    order = await process_orders_data(orders_data, date_from_obj, date_to_obj)
    stock = await proc_stock_data(stock_data)
    income = await get_incomes(income_data, stock, date_from_obj, date_to_obj)

    stock_income = await get_stock_with_income(stock, income)
    order, income, stock_income = await sort_data(order, income, stock_income)
    order_w2 = await order_w2_2(order)
    percent_buy1 = await percent_buy(orders_data, sales_data, date_from_obj, date_to_obj)

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
    df5 = pd.DataFrame(percent_buy1).T
    sheet_percent_buy = 'Таблица выкупа артикулов'
    df5 = df5.rename(columns={'count_orders': 'Количество заказов за 7д',
                              'count_sales': 'Количество продаж за 7д',
                              'percent': 'Процент выкупа'})

    with pd.ExcelWriter('data.xlsx', engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name=sheet_name, startcol=1, startrow=1, index_label='Артикул')
        df2.to_excel(writer, sheet_name=sheet_nameLeftOvers, startcol=1, startrow=1, index_label='Артикул')
        df3.to_excel(writer, sheet_name=sheet_nameLeftOvers, startcol=8, startrow=1, index_label='Артикул')
        df4.to_excel(writer, sheet_name=sheet_orders_w2, startcol=1, startrow=1, index_label='Артикул')
        df5.to_excel(writer, sheet_name=sheet_percent_buy, startcol=1, startrow=1, index_label='Артикул')
        workbook = writer.book
        worksheet1 = writer.sheets[sheet_name]
        worksheet2 = writer.sheets[sheet_nameLeftOvers]
        worksheet3 = writer.sheets[sheet_orders_w2]
        worksheet4 = writer.sheets[sheet_percent_buy]

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
            worksheet4.column_dimensions[column].width = width

    # print(json.dumps(order, indent=3))
    # print(json.dumps(order_w2, indent=3))
