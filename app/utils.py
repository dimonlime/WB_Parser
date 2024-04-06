import json
import os
import pandas as pd
import requests
import dotenv
from datetime import datetime, timedelta

dotenv.load_dotenv()

urlOrder = os.getenv('URL_ORDER')
urlSale = os.getenv('URL_SALE')
urlStock = os.getenv('URL_STOCK')
urlIncome = os.getenv('URL_INCOME')
data_dollar_rate = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()

token = os.getenv('WB_TOKEN')

headers = {'Authorization': token}

dateFrom = '2024-03-25'
dateNow = datetime.now().date()

paramsOrder = {'dateFrom': dateFrom,
               'flag': 0,
               }
paramsSales = {'dateFrom': dateFrom}
paramsStock = {'dateFrom': dateFrom}
paramsIncome = {'dateFrom': dateFrom}
date_from_obj = datetime.strptime(dateFrom, '%Y-%m-%d').date()
date_to_obj = date_from_obj + timedelta(days=7)
dollar_rate = data_dollar_rate['Valute']['USD']['Value']


async def get_data(url, headers, params):
    res = requests.get(url=url, headers=headers, params=params)
    return res.json()


async def update_incomes():
    with open("json_files/orders_data.json", "r") as orders_data_file, \
            open("json_files/stock_data.json", "r") as stock_data_file, \
            open("json_files/income_data.json", "r") as income_data_file, \
            open('config.json', 'r') as config_json, \
            open("json_files/sales_data.json", "r") as sales_data_file:
        orders_data = json.load(orders_data_file)
        stock_data = json.load(stock_data_file)
        income_data = json.load(income_data_file)
        config = json.load(config_json)
        sales_data = json.load(sales_data_file)
    order = await process_orders_data(orders_data, date_from_obj, date_to_obj)
    stock = await proc_stock_data(stock_data, date_from_obj, date_to_obj)
    income = await get_incomes(income_data, stock, date_from_obj, date_to_obj)
    stock_income = await get_stock_with_income(stock, income)
    order, stock_income, income = await compare_and_add_keys(order, stock_income, income)
    order, income, stock_income = await sort_data(order, income, stock_income)
    config['Article_week_1'] = income
    order_w2 = await order_w2_2(order)
    percent_buy1 = await percent_buy(orders_data, sales_data, date_from_obj, date_to_obj, order)
    stock_with_income_w2_2, income_w2 = await stock_with_income_w2(order_w2, percent_buy1, stock_income)
    config['Article_week_2'] = income_w2

    with open('config.json', 'w', encoding='UTF-8') as config_json:
        json.dump(config, config_json, indent=4)


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
        json.dump(orders_data, orders, indent=4)
    with open("json_files/stock_data.json", "w") as stock:
        json.dump(stock_data, stock, indent=4)
    with open("json_files/income_data.json", "w") as income:
        json.dump(income_data, income, indent=4)
    with open("json_files/sales_data.json", "w") as sales:
        json.dump(sales_data, sales, indent=4)


async def process_orders_data(data, date_from, date_to):
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
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

    for key in order:
        order[key]['count'] //= 7

    for article in order:
        order[article]['incrise'] = int(round(order[article]['count'] * config['Settings']['increase_value_week_1']))

    return order


async def proc_stock_data(data, date_from, date_to):
    stock = {}
    for items in data:
        date = items['lastChangeDate']
        date_obj = datetime.strptime(date[:10], '%Y-%m-%d').date()

        if '-' in items['techSize']:
            article = items['supplierArticle'] + ' ' + items['techSize']
        else:
            article = items['supplierArticle'] + items['techSize']

        if article not in stock:
            stock[article] = {'toClient': items['inWayToClient'],
                              'fromClient': items['inWayFromClient'],
                              'fullQuantity': items['quantity'],
                              'quantityWithIncome': 0}
        else:
            stock[article]['toClient'] += items['inWayToClient']
            stock[article]['fromClient'] += items['inWayFromClient']
            stock[article]['quantityWithIncome'] += 0
            stock[article]['fullQuantity'] += items['quantity']

    return stock


async def get_stock_with_income(stock, income):
    for article, value in stock.items():
        if article in income:
            stock[article]['quantityWithIncome'] += income[article]['quantity'] + stock[article]['fromClient'] + \
                                                    stock[article]['fullQuantity']
        else:
            stock[article]['quantityWithIncome'] = stock[article]['fromClient'] + stock[article]['fullQuantity']

    return stock


async def stock_with_income_w2(orders_w2, percent_buy, stock_with_income_w1):
    stock_with_income_w2 = {}
    income_w2 = {}
    for article in orders_w2:
        stock_with_income_w2[article] = {'toClient': orders_w2[article]['count'] * 7,
                                         'fromClient': 0,
                                         'fullQuantity': 0,
                                         'quantityWithIncome': 0}
        stock_with_income_w2[article]['fromClient'] = round(
            stock_with_income_w2[article]['toClient'] * percent_buy[article]['percent'], 0)
        income_w2[article] = {'quantity': 0}
        for items in stock_with_income_w1:
            if article == items:
                if stock_with_income_w1[items]['quantityWithIncome'] < orders_w2[article]['incrise'] * 7:
                    stock_with_income_w2[article]['fullQuantity'] = 0
                else:
                    stock_with_income_w2[article]['fullQuantity'] = stock_with_income_w1[items][
                                                                        'quantityWithIncome'] - (
                                                                                orders_w2[article]['incrise'] * 7)
        stock_with_income_w2[article]['quantityWithIncome'] = stock_with_income_w2[article]['fullQuantity'] + \
                                                              stock_with_income_w2[article]['fromClient'] + \
                                                              income_w2[article]['quantity']

    return stock_with_income_w2, income_w2


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

            income[article] = {'quantity': 0}

    for article in stock:
        if article not in income:
            income[article] = {'quantity': 0}

    return income


async def order_w2_2(order_w1):
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    order_w2 = {}
    for article in order_w1:
        if article not in order_w2:
            order_w2[article] = {'count': order_w1[article]['count'],
                                 'incrise': order_w1[article]['count'],
                                 'order7Days': 0, }

    for article in order_w2:
        order_w2[article]['incrise'] = int(
            round(order_w2[article]['incrise'] * config['Settings']['increase_value_week_2']))
        order_w2[article]['order7Days'] = order_w2[article]['incrise'] * 7

    return order_w2


async def percent_buy(data_orders, data_sales, date_from, date_to, order):
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

    for article in order:
        if article not in orders_buy_percent:
            orders_buy_percent[article] = {'count_orders': 0, 'count_sales': 0, 'percent': 0}

    return orders_buy_percent


async def general_indicators(dollar_rate):
    oper_cycle = {'production': 12,
                  'logistics': 7,
                  'fulfillment': 4}

    indicators = {'oper_cycle': oper_cycle['production'] + oper_cycle['logistics'] + oper_cycle['fulfillment'],
                  'comission': 0.1,
                  'dollar_rate': dollar_rate}

    return oper_cycle, indicators


async def formed_order(orders_w2, stock_with_income_w2, indicators):
    order = {}
    for article in orders_w2:
        # Создаем временный словарь для хранения обновленных данных
        temp_data = {}

        # Проверяем условие и присваиваем значение для binary_order
        if stock_with_income_w2[article]['quantityWithIncome'] < (
                orders_w2[article]['count'] * indicators['oper_cycle']):
            temp_data['binary_order'] = 1
        else:
            temp_data['binary_order'] = 0

        # Вычисляем count_to_koledino в зависимости от binary_order
        if temp_data['binary_order'] == 1:
            temp_data['count_to_koledino'] = (orders_w2[article]['incrise'] * indicators['oper_cycle']) - \
                                             stock_with_income_w2[article]['quantityWithIncome']
        else:
            temp_data['count_to_koledino'] = 0

        # Вычисляем значение для incrise и total
        temp_data['incrise'] = round(temp_data['count_to_koledino'] * 0.3, 0)
        temp_data['total'] = temp_data['count_to_koledino'] + temp_data['incrise']

        # Обновляем словарь order[article] с новыми значениями
        order[article] = temp_data

    return order


async def compare_and_add_keys(orders_w1, stock_income_w1, income_w1):
    # Перебираем ключи из первого словаря
    for article in orders_w1:
        # Если ключ отсутствует во втором словаре, добавляем его со значением None
        if article not in stock_income_w1:
            stock_income_w1[article] = {'toClient': 0,
                                        'fromClient': 0,
                                        'fullQuantity': 0,
                                        'quantityWithIncome': 0}
        # Если ключ отсутствует в третьем словаре, добавляем его со значением None
        if article not in income_w1:
            income_w1[article] = {'quantity': 0}

    # Перебираем ключи из второго словаря
    for article in stock_income_w1:
        # Если ключ отсутствует в первом словаре, добавляем его со значением None
        if article not in orders_w1:
            orders_w1[article] = {'count': 0,
                                  'incrise': 0}
        # Если ключ отсутствует в третьем словаре, добавляем его со значением None
        if article not in income_w1:
            income_w1[article] = {'quantity': 0}

    # Перебираем ключи из третьего словаря
    for article in income_w1:
        # Если ключ отсутствует в первом словаре, добавляем его со значением None
        if article not in orders_w1:
            orders_w1[article] = {'count': 0,
                                  'incrise': 0}
        # Если ключ отсутствует во втором словаре, добавляем его со значением None
        if article not in stock_income_w1:
            stock_income_w1[article] = {'toClient': 0,
                                        'fromClient': 0,
                                        'fullQuantity': 0,
                                        'quantityWithIncome': 0}

    return orders_w1, stock_income_w1, income_w1


async def regional_distribution(orders_data, sale_data, date_from, date_to):
    regional_distribution = {}

    # Подсчитываем заказы в заданном диапазоне дат
    for item in orders_data:
        date = item['date']
        date_obj = datetime.strptime(date[:10], '%Y-%m-%d').date()

        if date_from <= date_obj < date_to:

            if item['oblastOkrugName'].capitalize() in regional_distribution:
                if item['countryName'].capitalize() == 'Россия':
                    regional_distribution[item['oblastOkrugName'].capitalize()]['count_orders'] += 1
            else:
                if item['countryName'].capitalize() == 'Россия':
                    regional_distribution[item['oblastOkrugName'].capitalize()] = {'count_orders': 1, 'count_sales': 0,
                                                                                   'country_name': item[
                                                                                       'countryName'].capitalize()}

    # Подсчитываем продажи для каждого артикула
    for sale in sale_data:
        date = sale['date']
        date_obj = datetime.strptime(date[:10], '%Y-%m-%d').date()

        if date_from <= date_obj < date_to:

            if sale['oblastOkrugName'].capitalize() in regional_distribution:
                if sale['countryName'].capitalize() == 'Россия':
                    regional_distribution[sale['oblastOkrugName'].capitalize()]['count_sales'] += 1

    for items in orders_data:
        if items['oblastOkrugName'].capitalize() not in regional_distribution:
            if items['countryName'].capitalize() == 'Россия':
                regional_distribution[items['oblastOkrugName'].capitalize()] = {'count_orders': 0, 'count_sales': 0,
                                                                                'country_name': items['countryName']}

    return regional_distribution


async def initialize():
    with open('config.json', 'r') as config_json:
        config = json.load(config_json)
    with open("json_files/orders_data.json", "r") as orders_data_file, \
            open("json_files/stock_data.json", "r") as stock_data_file, \
            open("json_files/income_data.json", "r") as income_data_file, \
            open("json_files/sales_data.json", "r") as sales_data_file:
        orders_data = json.load(orders_data_file)
        stock_data = json.load(stock_data_file)
        income_data = json.load(income_data_file)
        sales_data = json.load(sales_data_file)

    order = await process_orders_data(orders_data, date_from_obj, date_to_obj)
    stock = await proc_stock_data(stock_data, date_from_obj, date_to_obj)
    income = config['Article_week_1']

    stock_income = await get_stock_with_income(stock, income)
    order, stock_income, income = await compare_and_add_keys(order, stock_income, income)
    order, income, stock_income = await sort_data(order, income, stock_income)
    income = config['Article_week_1']

    order_w2 = await order_w2_2(order)
    percent_buy1 = await percent_buy(orders_data, sales_data, date_from_obj, date_to_obj, order)

    stock_with_income_w2_2, income_w2 = await stock_with_income_w2(order_w2, percent_buy1, stock_income)
    income_w2 = config['Article_week_2']

    general_indicators1, indicators = await general_indicators(dollar_rate)
    formed_order1 = await formed_order(order_w2, stock_with_income_w2_2, indicators)

    df1 = pd.DataFrame(order).T
    sheet_name = 'Orders w1'
    df1 = df1.rename(columns={'count': 'Заказы',
                              'incrise': 'Ув 15%'})

    df2 = pd.DataFrame(stock_income).T
    sheet_nameLeftOversW1 = 'Leftovers, in transit, etc w1'
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

    df6 = pd.DataFrame(stock_with_income_w2_2).T
    sheet_nameLeftOversW2 = 'Leftovers, in transit, etc w2'
    df6 = df6.rename(columns={'toClient': 'В пути до клиента',
                              'fromClient': 'В пути от клиента',
                              'fullQuantity': 'Остатки на складе',
                              'quantityWithIncome': 'Остатки на складе с учетом поступлений'})

    df7 = pd.DataFrame(income_w2).T
    df7 = df7.rename(columns={'quantity': 'Поступления'})

    df5 = pd.DataFrame(percent_buy1).T
    sheet_percent_buy = 'Таблица выкупа артикулов'
    df5 = df5.rename(columns={'count_orders': 'Количество заказов за 7д',
                              'count_sales': 'Количество продаж за 7д',
                              'percent': 'Процент выкупа'})

    df8 = pd.DataFrame([general_indicators1], index=['Значение']).T
    df8 = df8.rename(index={'production': 'Производство',
                            'logistics': 'Логистика',
                            'fulfillment': 'Фулфилмент'})
    sheet_general_indicators = 'Общие показатели'

    df9 = pd.DataFrame([indicators], index=['Значение']).T
    df9 = df9.rename(index={'oper_cycle': 'Операционный цикл',
                            'comission': 'Комиссия подрядчика',
                            'dollar_rate': 'Курс доллара / рубль'})

    df10 = pd.DataFrame(formed_order1).T
    df10 = df10.rename(columns={'binary_order': 'Бинарный заказ',
                                'count_to_koledino': 'Сколько надо заказать направление Коледино',
                                'incrise': '30%',
                                'total': 'Итого'})
    sheet_formed_order = 'Сформированный заказ'
    sheet_w1 = 'Week 1'
    sheet_w2 = 'Week 2'
    sheet_general_indi = 'General'
    sheet_formed_order1 = 'Formed Order'
    df12 = pd.DataFrame()
    df0 = pd.DataFrame()
    df11 = pd.DataFrame()
    df13 = pd.DataFrame()

    with pd.ExcelWriter('data.xlsx', engine='openpyxl') as writer:
        df0.to_excel(writer, sheet_name=sheet_w1)

        df1.to_excel(writer, sheet_name=sheet_name, startcol=1, startrow=1, index_label='Артикул')

        df2.to_excel(writer, sheet_name=sheet_nameLeftOversW1, startcol=1, startrow=1, index_label='Артикул')
        df3.to_excel(writer, sheet_name=sheet_nameLeftOversW1, startcol=8, startrow=1, index_label='Артикул')

        df11.to_excel(writer, sheet_name=sheet_w2)
        df4.to_excel(writer, sheet_name=sheet_orders_w2, startcol=1, startrow=1, index_label='Артикул')
        df6.to_excel(writer, sheet_name=sheet_nameLeftOversW2, startcol=1, startrow=1, index_label='Артикул')
        df7.to_excel(writer, sheet_name=sheet_nameLeftOversW2, startcol=8, startrow=1, index_label='Артикул')

        df12.to_excel(writer, sheet_name=sheet_general_indi)
        df5.to_excel(writer, sheet_name=sheet_percent_buy, startcol=1, startrow=1, index_label='Артикул')

        df9.to_excel(writer, sheet_name=sheet_general_indicators, startcol=1, startrow=1, index_label='Показатель')
        df8.to_excel(writer, sheet_name=sheet_general_indicators, startcol=8, startrow=1, index_label='Показатель')

        df13.to_excel(writer, sheet_name=sheet_formed_order1)
        df10.to_excel(writer, sheet_name=sheet_formed_order, startcol=1, startrow=1, index_label='Артикул')
        workbook = writer.book

        worksheet0 = writer.sheets[sheet_w1]
        worksheet0.sheet_properties.tabColor = "00B050"
        worksheet1 = writer.sheets[sheet_name]
        worksheet2 = writer.sheets[sheet_nameLeftOversW1]

        worksheet8 = writer.sheets[sheet_w2]
        worksheet8.sheet_properties.tabColor = "00B050"
        worksheet3 = writer.sheets[sheet_orders_w2]
        worksheet5 = writer.sheets[sheet_nameLeftOversW2]

        worksheet9 = writer.sheets[sheet_general_indi]
        worksheet9.sheet_properties.tabColor = "00B050"
        worksheet4 = writer.sheets[sheet_percent_buy]
        worksheet6 = writer.sheets[sheet_general_indicators]

        worksheet10 = writer.sheets[sheet_formed_order1]
        worksheet10.sheet_properties.tabColor = "00B050"
        worksheet7 = writer.sheets[sheet_formed_order]

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
            worksheet5.column_dimensions[column].width = width
            worksheet4.column_dimensions[column].width = width
            worksheet6.column_dimensions[column].width = width
            worksheet7.column_dimensions[column].width = width
