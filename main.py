from flask import Flask, render_template, request, redirect
import requests
from bs4 import BeautifulSoup
import pandas as pd

# python -m venv venv
# venv\Scripts\activate

app = Flask(__name__)

@app.route("/", methods=["POST", "GET"])
def index():
    df = pd.read_excel("Kaufland_angebote.xlsx")
    n_deals = len(df.index)

    # guard clause
    if request.method != "POST":
        return render_template("index.html",
                               n_deals=n_deals,
                               ek_liste="",
                               tables=[],
                               titles="")

    ek = request.form["ek"]
    subset = fetch_data_from_xlsx(ek)

    return render_template("index.html",
                           n_deals=n_deals,
                           ek_liste=ek,
                           tables=[subset.to_html(classes='data')],
                           titles=subset.columns.values)


@app.route("/update")
def update():
    main()
    return redirect("/")


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
        self.category = category.replace("/uebersicht.", "").replace("%C3%B6", "ö").replace("%C3%BC", "ü").strip()
        self.quantity = quantity.replace("\n", "").replace("\t", "").strip()
        self.basic_price = basic_price
        self.on_list = False

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
    base_url = "https://filiale.kaufland.de/angebote"
    categories = {
        "01": "Fleisch__Gefl%C3%BCgel__Wurst",
        "01a": "Frischer_Fisch",
        "02": "Obst__Gem%C3%BCse__Pflanzen",
        "03": "Molkereiprodukte__Fette",
        "04": "Tiefk%C3%BChlkost",
        "05": "Feinkost__Konserven",
        "06": "Grundnahrungsmittel",
        "07": "Kaffee__Tee__S%C3%BC%C3%9Fwaren__Knabberartikel",
        "08": "Getr%C3%A4nke__Spirituosen",
        "09": "Drogerie__Tiernahrung",
        "10": "Elektro__B%C3%BCro__Medien",
        "11": "Heim__Haus",
        "12": "Bekleidung__Auto__Freizeit__Spiel",
        "97": "Internetwerbung",
        "135": "Foodkn%C3%BCller",
        "197": "K%C3%BCche",
        "281": "XXL",
        "360": "H%C3%B6hle_der_L%C3%B6wen",
        "562": "Bio",
        "592": "Mustang",
        "637": "K_Card",
        "239": "Wochenstartwerbung",
        "445": "Samstagswerbung"
    }
    output_list = ["https://filiale.kaufland.de/angebote/naechste-woche.html", "https://filiale.kaufland.de/angebote/aktuelle-woche.html"]
    for woche in ["aktuelle", "naechste"]:
        for key, value in categories.items():
            url = f"{base_url}/{woche}-woche/uebersicht.category={key}_{value}.html"
            output_list.append(url)

    return output_list


def get_data(url):
    print(f"GET {url}")

    req = requests.get(url)
    html = req.text
    soup = BeautifulSoup(html, "html.parser")
    output_list = []

    try:

        dates = soup.find("div", class_="o-richtext o-richtext--no-margin o-richtext--subheadline o-richtext--responsive").text.strip()
        # print(dates)
        dates = dates.replace("Gültig vom ", "")

        seperated_list = soup.find_all("div", class_="g-col o-overview-list__list-item")

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
    except AttributeError as e:
        print(e)
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


def fetch_data_from_xlsx(deal_list):
    item_list = deal_list.split(", ")
    df = pd.read_excel("Kaufland_angebote.xlsx")

    all_item_names = df["title"].tolist() + df["subtitle"].tolist()
    found_items = []
    for x in all_item_names:
        for item in item_list:
            item = str(item)
            x = str(x)
            if item.lower() in x.lower():
                found_items.append(x)

    subset = df[(df["title"].isin(found_items) | df["subtitle"].isin(found_items))]
    subset = subset[[
            "title",
             "subtitle",
             "quantity",
             "price",
             "discount",
             "basic_price",
             "date_start",
             "date_end",
             "category"
        ]]
    subset = subset.rename(columns={
        "title": "Titel",
        "subtitle": "Untertitel",
        "quantity": "Menge",
        "price": "Preis (€)",
        "discount": "Reduziert (%)",
        "basic_price": "Grundpreis",
        "date_start": "Deal Anfang",
        "date_end": "Deal Ende",
        "category": "Kategorie",
    })
    return subset


def main():
    print(f'Starting....')
    list_of_links = find_urls()

    all_items = []
    for link in list_of_links:
        list_of_items = get_data(link)
        if list_of_items:
            all_items = all_items + list_of_items

    dict_of_items = create_dict(all_items)

    df = pd.DataFrame.from_dict(dict_of_items)
    df.to_excel("Kaufland_angebote.xlsx")
    print(f"Total items: {len(all_items)}")



if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8080, debug=True)
    # app.run()
