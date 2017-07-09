from flask import render_template, jsonify, redirect, url_for
from bs4 import BeautifulSoup

import datetime
import requests
import xmltodict
import json

from app import app, db
from app.models import Games, Stats


@app.route("/")
@app.route("/<game_code>")
def home(game_code=""):
    games = Games.query.filter(Games.date >= datetime.date.today()).all()
    if not game_code:
        try:
            game_code = games[0].code
        except IndexError:
            pass
    game = Games.query.filter_by(code=game_code).first()
    return render_template("home.html", game_code=game_code, game=game, games=games)


@app.route("/api/<game_code>/latest")
@app.cache.cached(timeout=120)
def api_latest(game_code):
    game = Games.query.filter_by(code=game_code).first_or_404()

    stands = {
        "east": {
            "main": ["ES-EA", "ES-EB", "ES-EC", "ES-ED", "ES-EE"]
        },
        "south": {
            "upper": ["SU-SUF", "SU-SUG", "SU-SUHB", "SU-SUHY", "SU-SUI", "SU-SUJ"],
            "lower": ["SL-SLK", "SL-SLL", "SL-SLMB", "SL-SLMY", "SL-SLN", "SL-SLO"]
        },
        "west": {
            "family": ["WS-WP", "WS-WQ", "WS-WR"],
            "main": ["WS-WS", "WS-WT", "WS-WU", "WS-WV", "WS-WW"],
            "x": ["WS-WX"]
        },
        "north": {
            "yz": ["NS-NWW"]
        }
    }
    output = {
        "east": {"main": [0, 0]},
        "south": {"upper": [0, 0], "lower": [0, 0]},
        "west": {"family": [0, 0], "main": [0, 0], "x": [0, 0]},
        "north": {"yz": [0, 0]},
        "total": [0, 0]
    }

    if not game.east_stand: del stands["east"]; del output["east"]
    if not game.south_stand: del stands["south"]; del output["south"]
    if not game.x_block: del stands["west"]["x"]; del output["west"]["x"]
    if not game.yz_block: del stands["north"]["yz"]; del output["north"]["yz"]
    if not game.west_stand: del stands["west"]; del output["west"]

    for stand in stands:
        for area in stands[stand]:
            for block in stands[stand][area]:
                data = "{data: \"" + block + "\",\"productCode\":\"" + game.code + "\",\"stadiumCode\":\"RH\",\"campaignCode\":\"\",\"callId\":\"\"}"
                response = requests.post(
                    "https://ticketing.southend-united.co.uk/PagesPublic/ProductBrowse/VisualSeatSelection.aspx/GetSeating",
                    data=data,
                    headers={'content-type': "application/json; charset=UTF-8"},
                    verify=False
                )
                response.encoding = "unicode-escape"
                x = xmltodict.parse(json.loads(response.text)["d"])["seats"]["s"]
                total_sold = sum(1 for d in x if d.get("@a") == "." and "Segregation" not in d.get("@rsDesc"))
                total_available = sum(1 for d in x if d.get("@a") == "A") + sum(1 for d in x if d.get("@a") == "X")

                output[stand][area][0] += total_sold  # Total seats
                output[stand][area][1] += total_available  # Total available

                output["total"][0] += total_sold
                output["total"][1] += total_available

    output["time"] = datetime.datetime.utcnow().strftime("%H:%M:%S")

    new = Stats(
        game_id=Games.query.filter_by(code=game_code).first().id,
        time=datetime.datetime.utcnow(),
        total_sold=output["total"][0],
        total_available=output["total"][1]
    )
    db.session.add(new)
    db.session.commit()

    return jsonify(output)


@app.route("/api/<game_code>/historic")
def api_historic(game_code):
    stats = Stats.query.filter_by(game_id=Games.query.filter_by(code=game_code).first().id).order_by(Stats.time.desc()).all()
    return jsonify([[x.time, x.total_sold] for x in stats])


@app.route("/admin/load")
def admin_load():
    s = requests.Session()
    request = s.get("https://ticketing.southend-united.co.uk/PagesPublic/ProductBrowse/productHome.aspx")

    if "Automatically redirect to site." in request.text:
        print("It doesn't like bots, let's find the link...")
        link = request.text.split("<a href='")[1]
        link = link.split("'>click")[0]
        request = s.get(link)

    soup = BeautifulSoup(request.text, "html.parser")
    games = soup.find("div", {"id": "ticketing-products"}).parent

    for game in games.select("a .panel.ebiz-header.ebiz-product-type-H"):
        code = game["class"][2]
        team = game.select("li.ebiz-description")[0].text.replace("Southend Vs ", "").replace("Southend United Vs ", "")
        date = datetime.datetime.strptime(game.select("li.ebiz-date > span.ebiz-data")[0].text, "%A %d %B %Y")
        new = Games(team=team, code=code, date=date)
        db.session.add(new)
        db.session.commit()

    return redirect(url_for("home"))
