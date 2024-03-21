import requests
import json
import datetime, time
from config.tokens import DADATA_API_KEY

def rq_dadata(user_query):
    url = 'http://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party'
    headers = {'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': f'Token {DADATA_API_KEY}'}
    body = json.dumps({'query': user_query, 'count': 11})

    response = requests.post(url = url, data = body, headers = headers)

    return response.json()


def get_text_items(data):
    items = []

    good_items = set(checking_for_same_inn(data))
    all_items = [(x['data']['inn'], x['data']['state']['registration_date']) for x in data['suggestions']]
    
    to_delete = [] 
    for i, item in enumerate(all_items):
        if item not in good_items:
            to_delete.append(i)
        else:
            good_items.remove(item)
    data['suggestions'] = [data['suggestions'][i] for i in range(len(data['suggestions'])) if i not in to_delete]

    if len(data['suggestions']) == 1:
        val = convert_to_text_main(data['suggestions'][0])
        items.append(val)
        return items

    elif len(data['suggestions']) > 1:
        for item in data['suggestions']:
            val = convert_to_text_sec(item)
            if val is not None:
                val += '\n'
                items.append(val)
    
    return items

def convert_to_text_main(data):
    value_list=[]
    value_text=''

    if data['data']['type'] == 'LEGAL':
        name_val=f"<b>{data['data']['name']['full_with_opf']}</b>\n"
        value_list.append(name_val)

        inn_val=f"ИНН: {data['data']['inn']}"
        value_list.append(inn_val)

        ogrn_val=f"ОГРН: {data['data']['ogrn']}"
        value_list.append(ogrn_val)

        today = datetime.date.fromtimestamp(time.time())
        reg_date = datetime.date.fromtimestamp((data['data']['state']['registration_date']/1000.0))
        age = int(today.strftime(format='%Y')) - int(reg_date.strftime(format='%Y'))

        age_and_date_val=f"Возраст: {age} лет (дата регистрации: {reg_date.strftime(format='%d.%m.%Y')})"
        value_list.append(age_and_date_val)

        if data['data']['management'] != None:
            management_val = f"Руководитель: {data['data']['management']['name']}\nДолжность руководителя: {data['data']['management']['post']}"
            value_list.append(management_val)

    elif data['data']['type'] == 'INDIVIDUAL':
        name_val=f"<b>{data['data']['name']['full']}</b>"
        value_list.append(name_val)

        inn_val=f"ИНН: {data['data']['inn']}"
        value_list.append(inn_val)
        ogrnip_val=f"ОГРНИП: {data['data']['ogrn']}"
        value_list.append(ogrnip_val)

    for i in value_list:
        value_text=value_text+i+'\n'

    return value_text


def convert_to_text_sec(data):
    value_list=[]
    value_text=''

    if data['data']['type'] == 'LEGAL':
        name_val=f"<b>{data['data']['name']['full_with_opf']}</b>"
        value_list.append(name_val)
        
        inn_val=f"ИНН: /{data['data']['inn']}"
        value_list.append(inn_val)

        ogrn_val=f"ОГРН: {data['data']['ogrn']}"
        value_list.append(ogrn_val)

    elif data['data']['type'] == 'INDIVIDUAL':
        name_val=f"<b>{data['data']['name']['full']}</b>"
        value_list.append(name_val)
        
        inn_val=f"ИНН: /{data['data']['inn']}"
        value_list.append(inn_val)

    for i in value_list:
        value_text=value_text+i+'\n'

    return value_text


def checking_for_same_inn(data):
    latest_dates = {}
    for suggestion in data['suggestions']:
        inn = suggestion['data']['inn']
        reg_date = suggestion['data']['state']['registration_date']
        if inn not in latest_dates or reg_date > latest_dates[inn]:
            latest_dates[inn] = reg_date

    result = [(inn, reg_date) for inn, reg_date in latest_dates.items()]

    result.sort(key=lambda x: x[0])
    
    return result


def get_all(user_query):

    resp = rq_dadata(user_query)
    messages = get_text_items(resp)

    if len(messages) == 1:
        return messages[0]
    elif len(messages) < 1:
        return 'Не было найдено ни одного совпадения, попробуйте снова с другим запросом'
    elif len(messages) <= 10:
        return ''.join(messages)
    elif len(messages) > 10:
        val = ''.join(messages[:-1]) + 'Бот выдает 10 наиболее подходящих вариантов. Если вы не нашли нужную информацию, значит запрос был не точным'
        return val
