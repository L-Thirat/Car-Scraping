from flask import Flask , jsonify, request
import urllib, json, csv
import os
app = Flask(__name__)
filename = os.path.dirname(os.path.abspath(__file__))+"/csv_scrapes.csv"
@app.route('/cars')
def home():
    model = request.args.get("model",None)
    make = request.args.get("make", None)
    data = get_json(model, make)
    if(data != None):
        return data
    return {"error":"Make sure you put csv_scrapes.csv inside folder"}

def get_json(model, make):
    data = {}
    try:
        with open(filename) as csvFile:
            csvReader = csv.DictReader(csvFile)
            for rows in csvReader:
                if(model == None and make == None):
                    id = rows['hyperlink']
                    data[id] = rows
                else:
                    if(model != None and make != None):
                        if rows['model'] == model and rows['manufacturer'] == make:
                            id = rows['hyperlink']
                            data[id] = rows
                    elif(model != None):
                        if rows['model'] == model:
                            id = rows['hyperlink']
                            data[id] = rows
                    else:
                        if rows['manufacturer'] == make:
                            id = rows['hyperlink']
                            data[id] = rows
        return json.dumps(data)
    except:
        return None


if __name__ == '__main__':
   app.run(host="0.0.0.0", port=5000, debug=True)
