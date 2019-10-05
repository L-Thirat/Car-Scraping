from flask import Flask , jsonify, request
import urllib, json
app = Flask(__name__)

@app.route('/')
def home():
    model = request.args.get("model","")
    make = request.args.get("make", "")
    if model:
        url = "https://www.usedcarsni.com/search_results.php?keywords=&make=2&model={0}&keywords=&sortby=12|0".format(model)
    elif make:
        url = "https://www.usedcarsni.com/search_results.php?keywords=&make=2&make={0}&keywords=&sortby=12|0".format(make)
    else:
        url = "http://localhost:5000/crawl.json?start_requests=true&spider_name=car_spider"
    response = urllib.urlopen(url)
    data = json.loads(response.read())
    return jsonify(data)

if __name__ == '__main__':
   app.run(host="0.0.0.0", port=5000, debug=True)