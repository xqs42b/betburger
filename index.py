# coding=utf-8

import time
import datetime
import threading
import Queue
import json
import traceback
import betburger_manager 
import logging
import os
import shutil
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
now_queue = Queue.Queue()
_data_info = {'data':[], 'now_time':None, 'is_login': True} 
_hide_bet = []
_FILE_PATH = 'cookies/betburger'

@app.route('/')
def index(): 
    return render_template('index.html')

def while_get_data():
    global _data_info
    global now_queue
    _username = ''
    _password = ''
    betburger_class = betburger_manager.Betburger(_username, _password)

    n = 0
    while True:
        time.sleep(1)
        n += 1
        print '=============%d'%n
        data = betburger_class.get_data_info()
        print 'data:', len(data)
        if data:
            now_time = datetime.datetime.now() 
            add_hour = datetime.timedelta(hours=8)
            add_now_time = now_time + add_hour
            _data_info['now_time'] = add_now_time.strftime('%Y-%m-%d %H:%M:%S') 
        print 'now_queue_size:', now_queue.qsize()
        if not now_queue.empty():
            is_logout = now_queue.get_nowait()
            if is_logout == 'logout':
                print '退出循环'
                betburger_manager._ACCESS_TOKEN = ''
                betburger_manager._SEARCH_FILTER_ID = ''
                now_dir = os.getcwd() + '/tmp/'
                dir_list = os.listdir(now_dir)
                if len(dir_list) > 0:
                    shutil.rmtree(now_dir)
                    os.mkdir(now_dir)                
                break
        _data_info['data'] = data 

@app.route('/get_one_data/', methods=['GET'])
def get_one_data():
    # data = get_one_db()
    global _data_info
    global _hide_bet
    get_data = _data_info
    datas = get_data['data']
    now_time = int(time.time())
    if _hide_bet:
        for h in _hide_bet:
            if h['create_time'] + 14400 < now_time:
                _hide_bet.remove(h)
    try:
        if datas and _hide_bet:
            remove_datas = [] 
            new_datas = []
            for d in datas:
                for h in _hide_bet:
                    if (d['bet1']['home'] == h['home']) and (d['bet1']['away'] == h['away']) and \
                    (d['sport'] == h['sport']) and (d['bet1']['bookmaker'] == h['bookmaker']):
                        remove_datas.append(d)
                    if (d['bet2']['home'] == h['home']) and (d['bet2']['away'] == h['away']) and \
                    (d['sport'] == h['sport']) and (d['bet2']['bookmaker'] == h['bookmaker']):
                        remove_datas.append(d)
            for ds in datas:
                if ds not in remove_datas:
                    new_datas.append(ds)
            get_data['data'] = new_datas
            return jsonify(get_data)
    except Exception as e:
        print e
        # traceback.print_exc()
    return jsonify(get_data)

@app.route('/login/', methods=['GET'])
def login():
    '''
    登录
    '''
    global _data_info
    try:
        t1 = threading.Thread(target=while_get_data)
        t1.start()
    except:
        _data_info['is_login'] = False
        return jsonify({'status': False})
    _data_info['is_login'] = True 
    return jsonify({'status': True})

@app.route('/logout/', methods=['GET'])
def logout():
    '''
    退出登录
    '''
    global now_queue
    global _data_info
    now_queue.put('logout')
    _data_info['is_login'] = False
    return jsonify({'status': True})

@app.route('/hide_event/', methods=['GET'])
def hide_event():
    '''
    隐藏对应的比赛
    '''
    global _hide_bet
    res_dict1 = {}
    res_dict2 = {}
    if request.method == 'GET':
        try:
            sport = request.args.get('sport')
            home_away1 = request.args.get('home_away1')
            home_away2 = request.args.get('home_away2')
            bookmaker1 = request.args.get('bookmaker1')
            bookmaker2 = request.args.get('bookmaker2')
            if not sport:
                return jsonify({'hide':False})
            if bookmaker1 and home_away1:
                if home_away1.find(' - '):
                    home1, away1 = home_away1.split(' - ')
                else:
                    return jsonify({'hide':False})
            else:
                home1 = ''
                away1 = ''

            if bookmaker2 and home_away2:
                if home_away2.find(' - '):
                    home2, away2 = home_away2.split(' - ')
                else:
                    return jsonify({'hide':False})
            else:
                home2 = ''
                away2 = ''
            now_time = int(time.time())
            is_append1 = True
            is_append2 = True
            if _hide_bet:
                for h in _hide_bet:
                    if h['sport'] == sport:
                        if home1 and away1 and home2 and away2:
                            if h['home'] == home1 and h['away'] == away1:
                                is_append1 = False 
                            if h['home'] == home2 and h['away'] == away2:
                                is_append2 = False
                            if not is_append1 and not is_append2:
                                return jsonify({'hide': 'repeat'})
                        if home1 and away1 and (not home2) and (not away2):
                            if h['home'] == home1 and h['away'] == away1:
                                return jsonify({'hide': 'repeat'})
                        if home2 and away2 and (not home1) and (not away1):    
                            if h['home'] == home2 and h['away'] == away2:
                                return jsonify({'hide': 'repeat'})
            if is_append1 and bookmaker1 and home1 and away1:
                res_dict1['sport'] = sport
                res_dict1['home'] = home1
                res_dict1['away'] = away1 
                res_dict1['bookmaker'] = bookmaker1
                res_dict1['create_time'] = now_time
                _hide_bet.append(res_dict1)

            if is_append2 and bookmaker2 and home2 and away2:
                res_dict2['sport'] = sport
                res_dict2['home'] = home2
                res_dict2['away'] = away2
                res_dict2['bookmaker'] = bookmaker2
                res_dict2['create_time'] = now_time
                _hide_bet.append(res_dict2)
            # print '_hide_bet:', _hide_bet
        except Exception as e:
            print '==============hide_error================', e
            # print traceback.print_exc()
            return jsonify({'hide': False})
        return jsonify({'hide': True})


if __name__ == '__main__':
    t1 = threading.Thread(target=while_get_data)
    t1.start()
    app.run(host='0.0.0.0', port=8000)
