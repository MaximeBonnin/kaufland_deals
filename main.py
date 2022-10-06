from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Congratulations, it's a web app!"


import requests
from bs4 import BeautifulSoup
import pandas as pd

LISTS = {
    "WG": [
        "Klopapier",
        "Toilettenpapier",
        "Olivenöl",
        "Küchenrolle",
        "Mehl",
        "Reis",
        "Bier",
        "Zwiebel",
        "Aperol",
        "Bitterol",
        "Gewürz",
        "Müllsack",
        "Müllsäcke",
        "Backpapier"
    ],
    "Maxime": [
        "Avocado",
        "Barilla",
        "tortilla",
        "Mais",
        "Kaffee",
        "Schinkenwürfel",
        "Rinderhack",
        "Hünchen",
        "Küchenmesser",
        "Lichterkette",
        "Kokosmilch",
        "Karotten",
        "Kürbis"
    ],
    "Paula": [
        "Samba",
        "Passierte Tomaten",
        "Seitenbacher"
    ],
    "Malte": [
        "Gin",
        "Vodka",
        "Rum",
        "Limetten",
        "Zitronen"
    ]
}

class Item:
    def __init__(self, title, subtitle, price, dates, category, discount, quantity, basic_price):
        self.title = title.strip().capitalize()
        self.subtitle = subtitle.strip()
        self.price = price.strip().replace("  *", "").replace(".", "")
        self.price = int(self.price)/100
        self.discount = discount.replace("%", "").strip()
        self.discount = int(self.discount)
        self.date_start = dates[:10]
        self.date_end = dates[-10:]
        self.category = category
        self.quantity = quantity
        self.basic_price = basic_price
        self.on_list = False
        for issuer in LISTS:
            if self.title.lower() in [x.lower() for x in LISTS[issuer]] or self.subtitle.lower() in [x.lower() for x in LISTS[issuer]]:
                self.on_list = issuer

        self.dict = {
            "title": self.title,
            "subtitle": self.subtitle,
            "quantity": self.quantity,
            "price": self.price,
            "discount": self.discount,
            "basic_price": self.basic_price,
            "date_start": self.date_start,
            "date_end": self.date_end,
            "category": self.category,
            "on_list": self.on_list
        }

    def display(self):
        print(f"{self.date_start} bis {self.date_end}: {self.price}€ [{self.discount}%] | {self.title} [{self.subtitle}] | {self.category}")

def find_urls():
    base_url = "https://filiale.kaufland.de"

    # GET list of links for next week from site navigation
    req = requests.get(base_url + f"/angebote/naechste-woche.html")
    html = req.text
    soup = BeautifulSoup(html, "html.parser")

    list_ul = soup.find("ul", class_="m-accordion__list m-accordion__list--level-1")
    list_items = list_ul.find_all("li", class_="m-accordion__item m-accordion__item--level-2")
    list_items.append(list_ul.find("li", class_="m-accordion__item m-accordion__item--level-2 m-accordion__link--active"))

    list_of_links = []

    for list_item in list_items:
        a = list_item.find("a")
        link = base_url + a.get('href')
        list_of_links.append(link)

    # Get list of this weeks links from main menu
    req = requests.get(base_url + "/angebote/aktuelle-woche.html")
    html = req.text
    soup = BeautifulSoup(html, "html.parser")

    list_ul = soup.find("ul", class_="o-navigation-main__scroll-wrapper")
    list_items = list_ul.find_all("li")


    for list_item in list_items[:-1]:
        a = list_item.find("a")
        link = base_url + a.get('href')
        list_of_links.append(link)

    # list_of_links = list(dict.fromkeys(list_of_links))
    output_list = []
    [output_list.append(x) for x in list_of_links]
    print(f"List of length {len(list_of_links)} copied...")
    for l in list_of_links:
        output_list.append(l.replace("naechste", "aktuelle"))

    return output_list



def get_data(url):
    print(f"GET {url}")

    req = requests.get(url)
    html = req.text
    soup = BeautifulSoup(html, "html.parser")

    dates = soup.find("div", class_="o-richtext o-richtext--no-margin o-richtext--subheadline o-richtext--responsive").text.strip()
    # print(dates)
    dates = dates.replace("Gültig vom ", "")

    seperated_list = soup.find_all("div", class_="g-col o-overview-list__list-item")
    output_list = []

    for list_item in seperated_list:
        if list_item.find("div", class_="m-offer-tile-teaser m-offer-tile-teaser--mobile"):
            # print("AD")
            continue

        if list_item.find("h5"):
            title = list_item.find("h5").get_text()
        else:
            title = ""

        if list_item.find("h4"):
            subtitle = list_item.find("h4").get_text()
        else:
            subtitle = ""

        price = list_item.find("div", class_="a-pricetag__price").get_text()

        if list_item.find("div", class_="a-pricetag__discount"):
            discount = list_item.find("div", class_="a-pricetag__discount").get_text().strip()
            if discount in ["KNÜLLER", "PROBIERPREIS"]:
                discount = "0"
            elif discount == "1/2 PREIS":
                discount = "-50"
        else:
            discount = "0"

        category = url.replace("https://filiale.kaufland.de/angebote/", "").replace(".html", "").replace("naechste-woche.", "").replace("aktuelle-woche", "").replace("category=", "")

        if list_item.find("div", class_="m-offer-tile__quantity"):
            quantity = list_item.find("div", class_="m-offer-tile__quantity").text
        else:
            quantity = ""

        if list_item.find("div", class_="m-offer-tile__basic-price"):
            basic_price = list_item.find("div", class_="m-offer-tile__basic-price").text
        else:
            basic_price = ""

        new_item = Item(title, subtitle, price, dates, category, discount, quantity, basic_price)
        # new_item.display()
        output_list.append(new_item)

    return output_list


def create_dict(all_items):
    print("Creating dict...")
    output_dict = {
            "title": [],
            "subtitle": [],
            "quantity": [],
            "price": [],
            "basic_price": [],
            "discount": [],
            "date_start": [],
            "date_end": [],
            "category": [],
            "on_list": []
        }

    for item in all_items:
        for key, value in item.dict.items():
            output_dict[key].append(value)

    return output_dict


def main():
    print(f'Starting....')
    list_of_links = find_urls()

    all_items = []
    for link in list_of_links:
        list_of_items = get_data(link)
        all_items = all_items + list_of_items

    dict_of_items = create_dict(all_items)

    df = pd.DataFrame.from_dict(dict_of_items)
    df.to_excel("Kaufland_angebote.xlsx")
    print(f"Total items: {len(all_items)}")


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8080, debug=True)
    main()
