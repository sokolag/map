import os
from flask import Flask, jsonify, json
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy import text, Unicode
from sqlalchemy import cast, select, String
import json
import time
import geojson
import pandas as pd
import requests

os.environ["NLS_LANG"] = "Russian.AL32UTF8"

app = Flask(__name__)
CORS(app)


db_connect = create_engine("oracle+cx_oracle://pipe:vodokanal@172.16.50.20:1521/sebldb")
app.config['JSON_AS_ASCII'] = False

@app.route('/get_sectors')
def get_sectors():
    conn = db_connect.connect()  # connect to database
    query = conn.execute('''SELECT DISTINCT
         sp.value      AS sector
         FROM SDP_PARAM sp
         WHERE
           sp.NAME = 'SDP Water Supply Sector'
          ''')
    # for i in query.cursor.fetchall():
    #     print(i[0])
    r = jsonify({'sectors':  [i[0] for i in query.cursor.fetchall()]})
    return r

@app.route('/get_sdp')
def get_sdp():
    data = json.load(open('map_sdp_color.geojson', encoding='utf-8'))
    # print(data)
    r = jsonify(data)
    return r


@app.route('/get_time')
def get_time():
    def data2geojson_time(df):
        features = []
        df.apply(lambda X: features.append(
            geojson.Feature(geometry=geojson.Point((X['lon'], X['lat'])),
                            properties=dict(time=time.strftime("%Y-%m-%d %H:%M:%S")))), axis=1)
        return geojson.FeatureCollection(features)

    df_time = pd.DataFrame(columns=['lat', 'lon'])
    df_time.at[0, 'lat'] = 59.85
    df_time.at[0, 'lon'] = 30.30

    data = data2geojson_time(df_time)
    print(data)
    r = jsonify(data)

    return r

# response = requests.get('http://aladin-nb.alliance-electro.ru:8080/getData')
# data = response.json()
# df = pd.DataFrame(data)
# pump_stations = []



@app.route('/get_winccoa_data')
def get_winccoa_data():
    response = requests.get('http://aladin-nb.alliance-electro.ru:8080/getData')
    data = response.json()
    df = pd.DataFrame(data)
    pump_stations = []

    for i in range(len(df)):
        # print(df['Vodo_PNS'].loc[i]['INP'])
        df['Vodo_PNS'].loc[i]['INP']['MAIN']['PressureOut1'] = round(df['Vodo_PNS'].loc[i]['INP']['MAIN']['PressureOut1'], 2)
        d = dict.fromkeys(['lat', 'lon', 'prop'])
        prop_dict = {'name': df['dpName'].loc[i]}
        prop_dict.update(df['Vodo_PNS'].loc[i]['INP'])
        d['prop'] = prop_dict
        d['lat'] = df['Vodo_PNS'].loc[i]['lat']
        d['lon'] = df['Vodo_PNS'].loc[i]['lon']
        pump_stations.append(d)

    def data2geojson(list):
        features = []
        for X in list:
            features.append(geojson.Feature(geometry=geojson.Point((X['lat'], X['lon'])),
                                            properties=X['prop']['MAIN']))
        # with open('winccoa.geojson', 'w') as fp:
        #     geojson.dump(geojson.FeatureCollection(features), fp, sort_keys=True)
        return geojson.FeatureCollection(features)

    data = data2geojson(pump_stations)

    # data = json.load(open('winccoa.geojson', encoding='utf-8'))
    print(data)
    r = jsonify(data)
    return r

if __name__ == '__main__':
    app.run(port=12346, debug=True)