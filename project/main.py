import telebot
from func_file import search_city, search_hotels_by, \
  get_photo, info_hotel, search_hotel_info, get_location, \
  bestdeal_price, search_distance_price, writing_history, \
  date_transform, calculation_date
from telebot import types
from config import token
import random
from datetime import datetime
from datetime import date
from func_file import data
import json
from json import JSONDecodeError


bot = telebot.TeleBot(token)


@bot.message_handler(commands=['hello-world'])
def hello_world(message):
    bot.send_message(
        message.chat.id,
        f'Привет :)\nВведите /help для знакомства с командами'
    )


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f'Здравствуйте!\nСо списком всех возможных команд,'
        f' вы можете ознакомиться введя /help.'
    )


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(
        message.chat.id,
        f'● /lowprice — вывод самых дешёвых отелей в городе\n'
        f'● /highprice — вывод самых дорогих отелей в городе\n'
        f'● /bestdeal — вывод ближайших к центру города отелей'
        f' и наиболее подходящих по цене\n '
        f'● /history - вывод истории поиска отелей'
    )


@bot.message_handler(commands=['history'])
def get_history_messages(message):
    try:
        with open(f'{message.from_user.id}.json', 'r', encoding='utf-8') as outfile:
            history = json.load(outfile)
            for key, value in history.items():
                bot.send_message(message.from_user.id, f'{key} - {value}')
    except JSONDecodeError:
        bot.send_message(message.from_user.id, 'История отсутствует')
    except FileNotFoundError:
        bot.send_message(message.from_user.id, 'История отсутствует')


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def get_text_messages(message):
    text = message.text
    bot.send_message(message.from_user.id, "Введите город: ")
    if data.get(str(message.from_user.id)) is None:
        data[str(message.from_user.id)] = dict()
    data[str(message.from_user.id)][str(datetime.now())] = text
    writing_history(str(message.from_user.id))

    if text == '/lowprice':
        type_sort = 'lowprice'
        bot.register_next_step_handler(message, price_hotels_cheap, type_sort)

    elif text == '/highprice':
        type_sort = 'highprice'
        bot.register_next_step_handler(message, price_hotels_cheap, type_sort)

    elif text == '/bestdeal':
        type_sort = 'bestdeal'
        bot.register_next_step_handler(message, price_hotels_cheap, type_sort)


def price_hotels_cheap(message, *args):
    try:
        region_id = search_city(message.text)
        bot.reply_to(
            message,
            f'Введите количество отелей (цифрами) '
        )
        if args[0] == 'lowprice':
            bot.register_next_step_handler(
                message,
                date_start,
                region_id,
                *args
            )
        elif args[0] == 'highprice':
            bot.register_next_step_handler(
                message,
                date_start,
                region_id,
                *args
            )
        elif args[0] == 'bestdeal':
            bot.register_next_step_handler(
                message,
                date_start,
                region_id,
                *args
            )
    except Exception:
        bot.send_message(message.from_user.id, f'Город не найден')


def date_start(message, *args):
    try:
        hotels_count = int(message.text)
        bot.reply_to(message, 'Введите планируемую дату заезда: (дд-мм-гггг)')
        bot.register_next_step_handler(message, date_stop, *args, hotels_count)
    except Exception:
        bot.reply_to(message, f'Неверно указано кол-во отелей')


def date_stop(message, *args):
    try:
        start = date_transform(message.text)
        bot.reply_to(
            message,
            'Введите планируемую дату выезда : (дд-мм-гггг)'
        )
        bot.register_next_step_handler(message, calculation, *args, start)
    except TypeError:
        bot.reply_to(
            message,
            f'Неактульная дата заезда, укажите дату не ранее {date.today()}'
        )
    except Exception:
        bot.reply_to(message, f'Неверно указана дата приезда')


def calculation(message, *args):
    try:
        stop = date_transform(message.text)
        try:
            calc_dates = calculation_date(stop, args[3])
            if args[1] == 'bestdeal':
                price_range(message, *args, calc_dates)
            elif args[1] == 'lowprice':
                hotels_max_cheap(message, *args, calc_dates)
            else:
                hotels_max_high(message, *args, calc_dates)
        except ValueError:
            bot.reply_to(message, 'Неверно указан диапазон дат')
        except TypeError:
            bot.reply_to(
                message,
                f'Неактульная дата выезда, '
                f'укажите дату не ранее {date.today()}'
            )
    except Exception:
        bot.reply_to(message, f'Неверно указана дата выезда')


def price_range(message, *args):
    bot.reply_to(
        message,
        f'Введите диапазон цен через пробел в USD: "min max"'
    )
    bot.register_next_step_handler(message, deal_func, *args)


def deal_func(message, *args):
    price = message.text.split(' ')
    if len(price) == 2 and int(price[0]) < int(price[1]):
        maximum_hotels, region_id, days = int(args[2]), args[0], args[4]
        min_price, max_price = int(price[0]), int(price[1])
        list_hotels = search_hotels_by(
            region_id=region_id,
            minn=min_price,
            maxx=max_price,
            sort_type='DISTANCE'
        )
        sort_price = bestdeal_price(
            list_hotels,
            maxx=max_price,
            minn=min_price
        )
        try:
            for sorted_hotels in range(0, maximum_hotels):
                hotel = search_distance_price(
                    list_price=sort_price,
                    hotel_list=list_hotels
                )
                hotel_name, hotel_id, hotel_price, destination = info_hotel(
                    hotel
                )
                price_days = round(hotel_price * days, 2)
                search = search_hotel_info(hotel_id)
                location = get_location(search)
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        'Получить фото',
                        callback_data=f'hotel_{hotel_id}'
                    )
                )
                text = bot.send_message(
                    message.from_user.id,
                    f'Название : {hotel_name}\n'
                    f'Цена за ночь в $: {hotel_price}\n'
                    f'Цена за  указанный промежуток в $: {price_days}\n'
                    f'Расстояние до центра в милях: {destination}'
                    f'\nАдрес : {location}', reply_markup=markup
                )
                data[str(message.from_user.id)][str(datetime.now())] = text.text
        except Exception:
            bot.send_message(
                message.from_user.id,
                'Список отелей по данным параметрам закончился'
            )
        finally:
            writing_history(str(message.from_user.id))

    else:
        bot.reply_to(message, f'Неверно введён диапазон цен')


def hotels_max_high(message, *args):
    try:
        region, max_count, days = args[0], args[2], args[4]
        list_hotels = list(reversed(search_hotels_by(
            region_id=region,
            minn=450)))
        for elem in range(0, max_count):
            hotel_name, hotel_id, hotel_price, destination = info_hotel(
                list_hotels[elem]
            )
            search = search_hotel_info(hotel_id)
            price_days = round(hotel_price * days, 2)
            location = get_location(search)
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    'Получить фото',
                    callback_data=f'hotel_{hotel_id}'
                )
            )
            text = bot.send_message(
                message.from_user.id,
                f'Название : {hotel_name}\nЦена за ночь в $: {hotel_price}\n'
                f'Цена за  указанный промежуток в $: {price_days}\n'
                f'Расстояние до центра в милях: {destination}'
                f'\nАдрес : {location}', reply_markup=markup
            )
            data[str(message.from_user.id)][str(datetime.now())] = text.text
    except Exception:
        bot.send_message(
            message.from_user.id,
            'Список самых дорогих отелей в городе закончился'
        )
    finally:
        writing_history(str(message.from_user.id))


def hotels_max_cheap(message, *args):
    region, max_count, days = args[0], args[2], args[4]
    list_hotels = search_hotels_by(region_id=region, count=max_count)
    for sorted_hotels in range(0, max_count):
        hotel_name, hotel_id, hotel_price, destination = info_hotel(
            list_hotels[sorted_hotels]
        )
        search = search_hotel_info(hotel_id)
        price_days = round(hotel_price * days, 2)
        location = get_location(search)
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                'Получить фото',
                callback_data=f'hotel_{hotel_id}'
            )
        )
        text = bot.send_message(
            message.from_user.id,
            f'Название : {hotel_name}\nЦена за ночь в $: {hotel_price}\n'
            f'Цена за  указанный промежуток в $: {price_days}\n'
            f'Расстояние до центра в милях: {destination}'
            f'\nАдрес : {location}', reply_markup=markup
        )
        data[str(message.from_user.id)][str(datetime.now())] = text.text
    writing_history(str(message.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data.startswith('hotel_'))
def hotel_photo(call):
    hotel_id = call.data.split('_')[-1]
    info = search_hotel_info(hotel_id)
    photo = get_photo(info)
    bot.send_photo(call.from_user.id, photo)


#
#
@bot.message_handler()
def hello(message):
    bot.send_message(
        message.chat.id,
        f'Привет :)\nВведите /help для знакомства с командами'
    )


@bot.message_handler(content_types=['photo'])
def reply_photo(message):
    random_text = ['Вау красивое фото :)', '11 / 10', 'Awesome']
    bot.send_message(message.from_user.id, random.choice(random_text))


if __name__ == '__main__':
    bot.polling(none_stop=True)
