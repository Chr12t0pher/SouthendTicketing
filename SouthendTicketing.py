import json
import datetime

from flask import Flask, render_template, jsonify
from flask_cache import Cache

import requests
import xmltodict


app = Flask(__name__)
app.cache = Cache(app, config={"CACHE_TYPE": "simple"})


@app.route("/")
@app.route("/<game>")
def home(game="HGIL15"):
    return render_template("template.html", game=game)


@app.route("/api/<game>")
@app.cache.cached(timeout=120)
def api(game):
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
        }
    }

    url = "https://ticketing.southend-united.co.uk/PagesPublic/ProductBrowse/VisualSeatSelection.aspx/GetSeating"

    output = {"east": {"main": [0, 0, 0, 0]},
                     "south": {"upper": [0, 0, 0, 0], "lower": [0, 0, 0, 0]},
                     "west": {"family": [0, 0, 0, 0], "main": [0, 0, 0, 0], "x": [0, 0, 0, 0]},
                     "total": [0, 0, 0, 0]}

    if game != "HCOL15":
        del(stands["west"]["x"])
        del(output["west"]["x"])

    for stand in stands:
        for area in stands[stand]:
            for block in stands[stand][area]:
                data = "{data: \"" + block + "\",\"productCode\":\"" + game + "\",\"stadiumCode\":\"RH\",\"campaignCode\":\"\",\"callId\":\"\"}"
                response = requests.post(
                    url,
                    data=data,
                    headers={'content-type': "application/json; charset=UTF-8"}
                )
                response.encoding = "unicode-escape"
                x = xmltodict.parse(json.loads(response.text)["d"])["seats"]["s"]
                output[stand][area][0] += sum(1 for d in x if d.get("@a") == ".")
                output[stand][area][1] += sum(1 for d in x if d.get("@a") == "A")
                output[stand][area][2] += sum(1 for d in x if d.get("@a") == "X")
            output[stand][area][3] = output[stand][area][1] + output[stand][area][2]
            for i in range(0, len(output["total"])):
                output["total"][i] += output[stand][area][i]

    output["time"] = datetime.datetime.utcnow().strftime("%H:%M:%S")

    return jsonify(output)

if __name__ == '__main__':
    app.run(debug=True)
