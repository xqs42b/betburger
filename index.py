# coding=utf-8

import time
import threading
import Queue
import json
import traceback
import betburger_manager 
import logging
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
now_queue = Queue.Queue()
_data_info = {'data':[], 'now_tim':None} 
_hide_bet = []

@app.route('/')
def index(): 
    return render_template('index.html')

def while_get_data():
    global _data_info
    global now_queue
    _username = '54256821@qq.com'
    _password = 'Aa555888'
    # _username = ''
    # _password = ''
    betburger_class = betburger_manager.Betburger(_username, _password)

    n = 0
    while True:
        # time.sleep(1)
        n += 1
        print '=============%d'%n
        data = betburger_class.get_data_info()
        print 'data:', len(data)
        if data:
            now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            _data_info['now_time'] = now_time
        print 'now_queue_size:', now_queue.qsize()
        if not now_queue.empty():
            is_logout = now_queue.get_nowait()
            if is_logout == 'logout':
                print '退出循环'
                break
        _data_info['data'] = data 

@app.route('/get_one_data/', methods=['GET'])
def get_one_data():
    # data = get_one_db()
    global _data_info
    global _hide_bet
    data = _data_info
    datas = data['data']
    now_time = int(time.time())
    if _hide_bet:
        for h in _hide_bet:
            if h['create_time'] + 14400 < now_time:
                _hide_bet.remove(h)
    try:
        if datas and _hide_bet:
            for d in datas:
                for h in _hide_bet:
                    if d['sport'] == h['sport']:
                        if d['bet1']['bookmaker'] == h['bookmaker1']:
                            if (d['bet1']['home'] == h['home1']) and (d['bet1']['away'] == h['away1']):
                                datas.remove(d)
                                continue
                        if d['bet1']['bookmaker'] == h['bookmaker2']:
                            if (d['bet1']['home'] == h['home2']) and (d['bet1']['away'] == h['away2']):
                                datas.remove(d)
                                continue
                        if d['bet2']['bookmaker'] == h['bookmaker1']:
                            if (d['bet2']['home'] == h['home1']) and (d['bet2']['away'] == h['away1']):
                                datas.remove(d)
                                continue
                        if d['bet2']['bookmaker'] == h['bookmaker2']:
                            if (d['bet2']['home'] == h['home2']) and (d['bet2']['away'] == h['away2']):
                                datas.remove(d)
                                continue
    except Exception as e:
        print e
    return jsonify(data)

@app.route('/login/', methods=['GET'])
def login():
    '''
    登录
    '''
    try:
        t1 = threading.Thread(target=while_get_data)
        t1.start()
    except:
        return jsonify({'status': False})
    return jsonify({'status': True})

@app.route('/logout/', methods=['GET'])
def logout():
    '''
    退出登录
    '''
    global now_queue
    now_queue.put('logout')
    return jsonify({'status': True})

@app.route('/hide_event/', methods=['GET'])
def hide_event():
    '''
    隐藏对应的比赛
    '''
    global _hide_bet
    res_dict = {}
    if request.method == 'GET':
        try:
            sport = request.args.get('sport')
            home_away1 = request.args.get('home_away1')
            if home_away1 and home_away1.find(' - '):
                home1, away1 = home_away1.split(' - ')
            else:
                home1 = ''
                away1 = ''
            home_away2 = request.args.get('home_away2')
            if home_away2 and home_away2.find(' - '):
                home2, away2 = home_away2.split(' - ')
            else:
                home2 = ''
                away2 = ''
            bookmaker1 = request.args.get('bookmaker1')
            bookmaker2 = request.args.get('bookmaker2')
            now_time = int(time.time())
            
            if _hide_bet:
                for h in _hide_bet:
                    if h['sport'] == sport:
                        if home1 and away1 and home2 and away2:
                            if h['home1'] == home1 and h['away1'] == away1 and h['home2'] and h['away2']:
                                return jsonify({'hide': False})
                        if home1 and away1:
                            if h['home1'] == home1 and h['away1'] == away1:
                                return jsonify({'hide': False})
                        if home2 and away2:    
                            if h['home2'] == home2 and h['away2'] == away2:
                                return jsonify({'hide': False})

            res_dict['sport'] = sport
            res_dict['home1'] = home1
            res_dict['away1'] = away1 
            res_dict['bookmaker1'] = bookmaker1
            res_dict['home2'] = home2
            res_dict['away2'] = away2
            res_dict['bookmaker2'] = bookmaker2
            res_dict['create_time'] = now_time
            _hide_bet.append(res_dict)
        except Exception as e:
            print e
            return jsonify({'hide': False})
        return jsonify({'hide': True})


if __name__ == '__main__':
    t1 = threading.Thread(target=while_get_data)
    t1.start()
    app.run(host='0.0.0.0', port=8000)
