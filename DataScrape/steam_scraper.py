# https://store.steampowered.com/search/results/?query&start=50&count=50&dynamic_data=&sort_by=_ASC&tags=1702&snr=1_7_7_240_7&infinite=1

# https://store.steampowered.com/apphoverpublic/346110

import re
import csv

import requests
from bs4 import BeautifulSoup


def write_csv(data):
    with open('result_3_tags.csv', 'a', encoding="utf-8", newline='') as f:
        fields = [
            'title',
            'platforms',
            'reviews',
            'positives',
            'review_summary',
            'released',
            'price',
            'discount',
            'final_price',
            'main_tag',
            'url',
            'all_tags'
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writerow(data)


def get_html(url):
    response = requests.get(url)
    if not response.ok:
        print(f'Code: {response.status_code}, url: {url}')
    return response.text


def get_games(html):
    soup = BeautifulSoup(html, 'lxml')
    pattern = r'^https://store.steampowered.com/app/'
    games = soup.find_all('a', href=re.compile(pattern))
    return games


def get_hover_data(id):
    url = f'https://store.steampowered.com/apphoverpublic/{id}'
    html = get_html(url)
    soup = BeautifulSoup(html, 'lxml')

    try:
        title = soup.find('h4', class_='hover_title').text.strip()
    except:
        title = ''

    try:
        released = soup.find('div', class_='hover_release').span.text.split(':')[-1].strip()
    except:
        released = ''

    try:
        reviews_raw = soup.find('div', class_='hover_review_summary').text
    except:
        reviews = ''
    else:
        pattern = r'\d+'
        reviews = int(''.join(re.findall(pattern, reviews_raw)))

    try:
        tags_raw = soup.find_all('div', class_='app_tag')
    except:
        all_tags = ''
        main_tag = ''
    else:
        tags_text = [tag.text for tag in tags_raw]
        if tags_text:
            main_tag = tags_text[0]
            all_tags = ', '.join(tags_text[0:3])
        else:
            main_tag = ''
            all_tags = ''

    data = {
        'title': title,
        'released': released,
        'reviews': reviews,
        'main_tag': main_tag,
        'all_tags': all_tags
    }

    return data


def scrape_game_data(game):
    try:
        tooltip_raw = game.find('span', class_='search_review_summary').get('data-tooltip-html')
    except:
        review_summary = 'None'
        positives = 0
    else:
        # Mostly Positive<br>76% of the 246,393 user reviews for this game are positive.
        tr_splitted = tooltip_raw.split('<br>')
        review_summary = tr_splitted[0]
        positives_raw = tr_splitted[1]
        positives = int(positives_raw[:positives_raw.find('%')])

    try:
        platforms_raw = game.find('div', class_='search_name').p
    except:
        platforms = 'None'
    else:
        platforms_os = [platform.get_attribute_list('class')[-1].title() for platform in platforms_raw.find_all('span', class_='platform_img')]
        vr = platforms_raw.text.strip()

        if vr:
            platforms = ', '.join(platforms_os) + ', ' + vr
        else:
            platforms = ', '.join(platforms_os)

    try:
        price_raw = game.find('div', class_='search_price')
    except:
        price = 0
        final_price = 0
    else:
        price_text = price_raw.text.strip()  # $49.99$10.00
        pattern = r'\d{1,3}.\d{1,3}'
        prices = re.findall(pattern, price_text)
        if prices:
            if len(prices) > 1:
                price, final_price = prices
            else:
                price = prices[0]
                final_price = 0
        else:
            price = price_text
            final_price = 0

    try:
        discount_raw = game.find('div', class_='search_discount')
    except:
        discount = 0
    else:
        discount = discount_raw.text.strip().strip('%')

    try:
        url = game.get('href')
    except:
        url = ''

    data = {
        'review_summary': review_summary,
        'positives': positives,
        'platforms': platforms,
        'price': price,
        'final_price': final_price,
        'discount': discount,
        'url': url
    }

    id = game.get('data-ds-appid')
    data.update(get_hover_data(id))

    write_csv(data)


def main():
    all_games = []
    start = 0

    # added the cc=us parameter to get prices in USD.
    # Otherwise Steam uses your IP to determine the currency.
    url = f'https://store.steampowered.com/search/results/?query&start={start}&count=100&tags=9'

    while True:

        games = get_games(get_html(url))

        if games:
            all_games.extend(games)
            start += 100
            url = f'https://store.steampowered.com/search/results/?query&start={start}&count=100&tags=9'
        else:
            break

    for game in all_games:
        scrape_game_data(game)


# if __name__ == '__main__':
#     main()

main()