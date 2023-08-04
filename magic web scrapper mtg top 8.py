import sys
import requests
from bs4 import BeautifulSoup
import re
import math

base_url = "http://mtgtop8.com"
path = "/search?"

def get_deck_data(url):
    response = requests.get(url)
    deck_data = {}

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        w_title_div = soup.find('div', class_='w_title')

        if w_title_div:
            title_text = w_title_div.get_text(strip=True)
            match = re.search(r'(\d+) decks matching', title_text)
            if match:
                num_decks = int(match.group(1))
                num_pages = max(math.ceil(num_decks / 10), 1)  # Set num_pages to at least 1
                print("Number of decks:", num_decks)
                print("Number of pages:", num_pages)

                for page in range(1, num_pages + 1):
                    search_url = base_url + path + "format=" + format_needed + "&current_page=" + str(page) + "&deck_titre=" + deck_titre
                    response = requests.get(search_url)

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        tables = soup.find_all('table', class_='Stable')

                        if len(tables) >= 2:
                            table_html = tables[1]

                            rows = table_html.find_all('tr')

                            for row in rows:
                                link_tag = row.find('a')
                                if link_tag:
                                    href = link_tag['href']
                                    name = link_tag.get_text()

                                    if name in deck_data:
                                        deck_data[name]['links'].append(href)
                                    else:
                                        deck_data[name] = {'links': [href], 'prices': [], 'avg_price': None}

                                    deck_url = base_url + "/" + href
                                    try:
                                        deck_response = requests.get(deck_url)
                                        if deck_response.status_code == 200:
                                            deck_soup = BeautifulSoup(deck_response.content, 'html.parser')
                                            price_span = deck_soup.find('span', class_='O14')  # Use span instead of div
                                            if price_span:
                                                price_text = price_span.get_text(strip=True)
                                                if price_text.isdigit():  # Check if price_text contains only digits
                                                    deck_data[name]['prices'].append(float(price_text))
                                                else:
                                                    print("Invalid price format:", price_text)

                                        else:
                                            print("Request failed for deck URL:", deck_url)
                                    except requests.exceptions.ConnectionError as e:
                                        print("Connection Error for deck URL:", deck_url)
                                        print("Error:", e)

                        else:
                            print("Second table with class 'Stable' not found on page {}.".format(page))
                    else:
                        print("Request failed with status code {} on page {}.".format(response.status_code, page))
    else:
        print("Request failed with status code:", response.status_code)

    # Calculate average prices for each name's links
    for name, data in deck_data.items():
        avg_price = sum(data['prices']) / len(data['prices']) if data['prices'] else None
        data['avg_price'] = avg_price

    return deck_data

if len(sys.argv) != 3:
    print("Usage: python script.py <format_needed> <deck_titre>")
    sys.exit(1)

format_needed = sys.argv[1]
deck_titre = sys.argv[2]

first_page_url = base_url + path + "format=" + format_needed + "&current_page=1" + "&deck_titre=" + deck_titre
deck_data = get_deck_data(first_page_url)

# Generate an HTML table for extracted deck names, links, prices, and average price
html_table = u"<table border='1'><tr><th>Deck Name</th><th>Links</th><th>Prices</th><th>Avg Price</th></tr>"
for name, data in deck_data.items():
    links_html = u"<br>".join("<a href='{}' target='_blank'>{}</a>".format(base_url + "/" + link, link) for link in data['links'])
    prices = u"<br>".join("${:.2f}".format(price) for price in data['prices'])
    avg_price = "${:.2f}".format(data['avg_price']) if data['avg_price'] is not None else "N/A"
    html_table += u"<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(name, links_html, prices, avg_price)
html_table += u"</table>"

# Print the HTML table
print("HTML Table:")
print(html_table.encode('utf-8'))
