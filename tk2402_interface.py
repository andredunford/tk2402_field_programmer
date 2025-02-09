import numpy as np
import json
import pandas as pd
import sqlite3

from flask import Flask, render_template, request, redirect

from tk2402_translate import TKTranslate
from tk2402_comms import TKComms
import tk2402_constants as tkconst


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


def get_chan_ids():
    db_conn = db_connect()
    chan_df = pd.read_sql_query("SELECT * FROM tk_channels ORDER BY CASE WHEN channel_id = 'None' THEN 1 ELSE 2 END, channel_id, freq_rx", con=db_conn, index_col='channel_id')
    channel_ids = chan_df.index.to_list()
    db_conn.close()

    return channel_ids, chan_df


def get_empty_data_dict():
    data_dict = {
        i: {'freq_rx': None, 'freq_tx': None, 'qt_rx': 0.0, 'qt_tx': 0.0,
            'power': 1, 'scan': 1, 'width': 0} for i in range(1, 17, 1)
    }

    return data_dict


@app.route('/', methods=['GET', 'POST'])
def kenwood_home():

    chan_ids, chan_df = get_chan_ids()
    chan_db = chan_df.to_json(orient="index")

    data_dict = get_empty_data_dict()
    for chan in data_dict:
        data_dict[chan]['channel_id'] = 'None'

    data = json.dumps(data_dict)

    return render_template('index.html', channel_ids=chan_ids, chan_db=chan_db, qt_freqs=tkconst.QT_MASK, data_dict=data)


@app.route('/send_channels', methods=['POST'])
def send_channels():
    """receive form data of channels, parse, and send via kenwood_comms"""

    form_data = request.form
    form_data = form_data.to_dict()

    chan_ids, chan_df = get_chan_ids()
    chan_db = chan_df.to_json(orient="index")

    form_floats = ('freq_rx', 'freq_tx', 'qt_rx', 'qt_tx')
    form_ints = ('power', 'scan', 'width')

    data_dict = get_empty_data_dict()
    for ind, key in enumerate(data_dict):
        if f'channel_id{ind + 1}' not in form_data:
            form_data[f'channel_id{ind + 1}'] = " "
        for subkey in form_floats:
            try:
                data_dict[ind + 1][subkey] = float(form_data['{}{}'.format(subkey, ind + 1)])
            except:
                data_dict[ind + 1][subkey] = 0.0
        for subkey in form_ints:
            data_dict[ind + 1][subkey] = int(form_data['{}{}'.format(subkey, ind + 1)])
        data_dict[ind + 1]['channel_id'] = form_data[f'channel_id{ind + 1}']

    trans = TKTranslate()
    channels_binary, channels_active = trans.dict_to_binary(data_dict)
    ki = TKComms()
    ki.tk_write(channels_active, channels_binary)
    data_dict = json.dumps(data_dict)

    return render_template('index.html', channel_ids=chan_ids, chan_db=chan_db, qt_freqs=tkconst.QT_MASK, data_dict=data_dict)


@app.route('/read_channels', methods=['POST'])
def read_channels():
    """read channel data from Kenwood Radio and return data to app interface"""

    chan_ids, chan_df = get_chan_ids()
    chan_db = chan_df.to_json(orient="index")

    form_data = request.form
    ki = TKComms()

    data_in = ki.tk_read()
    trans = TKTranslate()
    data_dict = trans.binary_to_dict(data_in)

    data_df = pd.DataFrame.from_dict(data_dict, orient="index")
    chan_df['channel_id'] = chan_df.index

    merge_df = data_df.merge(chan_df[['channel_id', 'freq_rx', 'freq_tx', 'qt_rx', 'qt_tx', 'power', 'width']],
                             how='left', on=['freq_rx', 'freq_tx', 'qt_rx', 'qt_tx', 'power', 'width'])
    merge_df.index += 1
    merge_df = merge_df.replace({np.nan: None})
    data_dict = merge_df.to_dict(orient='index')
    data_dict = json.dumps(data_dict)

    return render_template('index.html', channel_ids=chan_ids, chan_db=chan_db, qt_freqs=tkconst.QT_MASK, data_dict=data_dict)


@app.route('/add_channel', methods=['POST'])
def add_channel():
    """add new channel to frequency database"""
    chan_data = request.form
    db_conn = db_connect()

    cur = db_conn.cursor()

    sql_str = """INSERT INTO tk_channels (description, channel_id, freq_rx, freq_tx, qt_tx, qt_rx, power, scan, width)
    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    sql_values = (
        chan_data['description'],
        chan_data['channel_id'],
        float(chan_data['freq_rx']),
        float(chan_data['freq_tx']) if chan_data['freq_tx'] != '' else None,
        float(chan_data['qt_rx']),
        float(chan_data['qt_tx']),
        bool(int(chan_data['power'])),
        bool(int(chan_data['scan'])),
        bool(int(chan_data['width'])),
    )
    try:
        cur.execute(sql_str, sql_values)
        db_conn.commit()
    except sqlite3.IntegrityError:
        return "Record Already Exists", 404
    finally:
        cur.close()
        db_conn.close()

    return redirect('/')

@app.route('/delete_channel', methods=['POST'])
def delete_channel():
    """delete channel from database"""
    chan_data = request.form
    db_conn = db_connect()

    cur = db_conn.cursor()

    if chan_data['to_delete'] == 'None':
        return redirect('/')

    sql_str = """DELETE 
                FROM tk_channels
                WHERE channel_id = '{}'""".format(chan_data['to_delete'])

    cur.execute(sql_str)
    db_conn.commit()
    cur.close()
    db_conn.close()

    return redirect('/')

def db_connect():
    db_conn = sqlite3.connect("db/channels.db")
    return db_conn

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050)

