from datetime import datetime, timedelta
import requests
import json
import re
from config import headers


data = dict()


def writing_history(name_file: str = 'history_file') -> None:
		with open(f'{name_file}.json', 'w', encoding='utf-8') as outfile:
				json.dump(data[name_file], outfile, indent=4, ensure_ascii=False)


def search_city(id_city: str = "Goa", headers: dict = headers) -> str:
		url = "https://hotels4.p.rapidapi.com/locations/v3/search"
		querystring = {"q": id_city, "locale": "en_US", "langid": "1033", "siteid": "300000001"}
		response = requests.request("GET", url, headers=headers, params=querystring)
		id_reg = re.search(r'"index":"0","gaiaId":"\d*', response.text)
		return id_reg.group()[22:]


def search_hotels_by(region_id: str, count: int = 100, headers: dict = headers, sort_type: str = "PRICE_LOW_TO_HIGH", maxx: int = 9000, minn: int = 1) -> list:
		url = "https://hotels4.p.rapidapi.com/properties/v2/list"
		payload = {
				"currency": "USD",
				"eapid": 1,
				"locale": "en_US",
				"siteId": 300000001,
				"destination": {"regionId": region_id},
				"checkInDate": {
						"day": 10,
						"month": 10,
						"year": 2022
				},
				"checkOutDate": {
						"day": 11,
						"month": 10,
						"year": 2022
				},
				"rooms": [
						{
								"adults": 2,
								"children": [{"age": 5}, {"age": 7}]
						}
				],
				"resultsStartingIndex": 0,
				"resultsSize": count,
				"sort": sort_type,
				"filters": {"price": {
						"max": maxx,
						"min": minn
				}}
			}

		headers["content-type"] = "application/json"

		response = requests.request("POST", url, json=payload, headers=headers).text

		return json.loads(response)['data']['propertySearch']['properties']


def bestdeal_price(list_hotels: list, maxx: int, minn: int) -> list:
		new_list = list()
		for elem in list_hotels:
				text = re.findall(
					r"'currencyInfo': \{'__typename': 'Currency', 'code': 'USD', 'symbol': '\$'}, 'formatted': '\$\d*",
					str(elem))
				num = int(text[0][89:])
				if minn <= num <= maxx:
						new_list.append(num)
		correct_list = ['$' + str(elem) for elem in sorted(new_list)]
		return correct_list


def info_hotel(file: dict) -> tuple:
		name = file['name']
		price = file['price']['lead']['amount']
		distance = file['destinationInfo']['distanceFromDestination']['value']
		hotel_id = file['id']
		return name, hotel_id, price, str(distance)


def search_hotel_info(hotel_id: str, headers: dict = headers) -> list:
		url = "https://hotels4.p.rapidapi.com/properties/v2/detail"
		payload = {
			"currency": "USD",
			"eapid": 1,
			"locale": "en_US",
			"siteId": 300000001,
			"propertyId": hotel_id
		}

		headers["content-type"] = "application/json"

		response = requests.request("POST", url, json=payload, headers=headers).text

		return json.loads(response)['data']['propertyInfo']


def get_location(hotel: json) -> str:
		return hotel['summary']['location']['address']['addressLine']


def get_photo(hotel: json) -> str:
		return hotel['propertyGallery']['images'][0]['image']['url']


def search_distance_price(list_price: list, hotel_list: list) -> dict:
		for i, hotel in enumerate(hotel_list):
				if list_price[0] in str(hotel):
						list_price.pop(0), hotel_list.pop(i)
						return hotel


def date_transform(dates: str) -> datetime:
		date_string = dates.split()
		date_string = ''.join(date_string)
		if datetime.strptime(date_string, "%d-%m-%Y") >= datetime.now() - timedelta(days=1):
				return datetime.strptime(date_string, "%d-%m-%Y")
		else:
				raise TypeError


def calculation_date(date_1: datetime, date_2: datetime) -> int:
		days = date_1 - date_2
		string_days = str(days)
		if not string_days.startswith('-') and not string_days.startswith('0'):
				return int(string_days.split()[0])
		else:
				raise ValueError
