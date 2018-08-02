#!/usr/bin/python
# coding=utf-8

import os
import requests
import json
import time
import traceback
import string
import random
import re
# from requests.packages import urllib3

_FILE_PATH = 'cookies/betburger'
IndexArray=['home', 'away', 'league', 'current_score', 'market_depth', 'koef', 'created_at', 'updated_at', 'started_at']
_PERCENT_ = 'percent' 
_PAUSED_ = 'paused'
_MIDDLE_VALUE_ = 'middle_value'
_SPORT_ID_ = 'sport_id'
_EVENT_ID_ = 'event_id'
_BET1_id_ = 'bet1_id'
_BET2_id_ = 'bet2_id'
_VALUE_ = 'value'
_BV_ID_ = 'bv_id'
_ID_ = 'id'
_NAME_ = 'name'
_REQUEST_COUNT = 0
_ACCESS_TOKEN = '' 
_SEARCH_FILTER_ID = ''


class Betburger(object):
    '''
    获取betburger中所有的数据
    '''
    def __init__(self, username='', password=''):
        self._url = 'https://api-lv.betburger.com/api/v1/arbs/pro_search?access_token='
        self._dir_url = 'https://api-lv.betburger.com/api/v1/directories?access_token='
        self._bet_val_url = 'https://api-lv.betburger.com/api/v1/bet_combinations/'
        self.url_mid_name = 'betburger'
        self.username = username
        self.password = password

    def get_data_info(self):
        '''
        获取所有的数据
        '''
        global _REQUEST_COUNT
        global _ACCESS_TOKEN
        global _SEARCH_FILTER_ID
        _REQUEST_COUNT += 1
        print 'request_count:', _REQUEST_COUNT
        print 'access_token:', _ACCESS_TOKEN
        print 'search_filter_id:', _SEARCH_FILTER_ID
        url = self._url
        if not _ACCESS_TOKEN and not _SEARCH_FILTER_ID:
            if self.username and self.password:
                user_data = self.get_user_data()
                if user_data:
                    _SEARCH_FILTER_ID = user_data[0]
                    _ACCESS_TOKEN = user_data[1]
                else:
                    return '' 
            
        self._dir_url += _ACCESS_TOKEN
        if _SEARCH_FILTER_ID and _ACCESS_TOKEN:
            url += _ACCESS_TOKEN
            search_filter_id = _SEARCH_FILTER_ID
            web_json_data = self.get_betburger_web_content(url, search_filter_id)
        else:
            web_json_data = self.get_betburger_web_content(url)
        # if _REQUEST_COUNT >= 4000:
        #     _REQUEST_COUNT = 0
        #     _ACCESS_TOKEN = self.refresh_token(_ACCESS_TOKEN)
        directories_data = self.get_directories(self._dir_url, self.url_mid_name)        
        if not directories_data:
            return '' 

        result = []
        bet_url_str = ''
        if len(web_json_data) > 0:
            data = json.loads(web_json_data)
            if 'arbs' not in data:
                return ''
            try:
                for dataTmp in data['arbs']:
                    bets = {}
                    bet1 = {}
                    bet2 = {}
                    # bet3 = {}
                    bets['percent'] = dataTmp[_PERCENT_]
                    bets['paused'] = dataTmp[_PAUSED_]
                    bets['middle_value'] = dataTmp[_MIDDLE_VALUE_]
                    bets['event_id'] = dataTmp[_EVENT_ID_]
                    sport_id = dataTmp[_SPORT_ID_]
                    sport_name = self.get_directory_data(sport_id, directories_data, dir_kw='sports', get_kw='name') 
                    bets['sport'] = sport_name            

                    bet1[_BET1_id_] = bet1_id = dataTmp[_BET1_id_]
                    bet2[_BET2_id_] = bet2_id = dataTmp[_BET2_id_]
                    # bet3_id = dataTmp['bet3_id']
                    index1 = self.judge_index(bet1_id, data)
                    index2 = self.judge_index(bet2_id, data)
                    # index3 = self.judge_index(bet3_id, data)

                    bm_id_1 = data['bets'][index1]['bookmaker_id']
                    bm_id_2 = data['bets'][index2]['bookmaker_id']
                    bet1['bookmaker'] = self.get_directory_data(bm_id_1, directories_data, dir_kw='bookmakers', get_kw='name')
                    bet2['bookmaker'] = self.get_directory_data(bm_id_2, directories_data, dir_kw='bookmakers', get_kw='name')
                    bet1['bookmaker_url'] = self.get_directory_data(bm_id_1, directories_data, dir_kw='bookmakers', get_kw='url')
                    bet2['bookmaker_url'] = self.get_directory_data(bm_id_2, directories_data, dir_kw='bookmakers', get_kw='url')

                    bet1['period_id'] = period_id1 = data['bets'][index1]['period_id']
                    bet2['period_id'] = period_id2 = data['bets'][index2]['period_id']
                    bet1['period'] = self.get_directory_data(period_id1, directories_data, dir_kw='periods', get_kw='title')
                    bet2['period'] = self.get_directory_data(period_id2, directories_data, dir_kw='periods', get_kw='title')

                    bc_id1 = data['bets'][index1]['bc_id']
                    bc_id2 = data['bets'][index2]['bc_id']
                    bet1['bc_id'] = bc_id1
                    bet2['bc_id'] = bc_id2
                    bet_url_str += str(bc_id1) + ','
                    bet_url_str += str(bc_id2) + ','

                    for tmp in IndexArray:
                        bet1[tmp] = data['bets'][index1][tmp]
                        bet2[tmp] = data['bets'][index2][tmp]

                    # 暂时所有的bet3为空
                    # if index3 is not None:
                    #     for tmp in IndexArray:
                    #         bet3[tmp] = data['bets'][index3][tmp]
                    #     bets['bet3'] = bet3

                    bets['bet1'] = bet1
                    bets['bet2'] = bet2

                    result.append(bets)

                bet_url_str = bet_url_str.rstrip(',')
                new_bet_val_url = self._bet_val_url + bet_url_str + '?access_token=' + _ACCESS_TOKEN

                bet_value_data = self.get_bet_value(new_bet_val_url)
                if bet_value_data:
                    bet_combinations_data = bet_value_data['bet_combinations']
                else:
                    return ''

                # bet_variations_data = directories_data['bet_variations']
                for res in result:
                    if len(new_bet_val_url) > 0 and len(bet_value_data) > 0:
                        bet1_break = False 
                        bet2_break = False
                        for bet in bet_combinations_data:
                            if not bet1_break:
                                if bet[_ID_] == res['bet1']['bc_id']:
                                    res['bet1']['bet_value'] = bet[_VALUE_]
                                    # res['bet1']['bv_id'] = bet[_BV_ID_]
                                    bet_name_value = self.change_handicap(bet['title'])
                                    left_brackets_index1 = bet_name_value.find('(')
                                    right_brackets_index1 = bet_name_value.find(')')
                                    if (left_brackets_index1 != -1) and (right_brackets_index1 != -1):
                                        res['bet1']['bet_name'] = bet_name_value.replace(bet_name_value[left_brackets_index1:right_brackets_index1+1], '')
                                    else:
                                        res['bet1']['bet_name'] = bet_name_value
                                    res['bet1']['bet_variation_name'] = bet_name_value 
                                    bet1_break = True
                            if not bet2_break:
                                if bet[_ID_] == res['bet2']['bc_id']:
                                    res['bet2']['bet_value'] = bet[_VALUE_]
                                    # res['bet2']['bv_id'] = bet[_BV_ID_]
                                    bet_name_value = self.change_handicap(bet['title'])
                                    left_brackets_index2 = bet_name_value.find('(')
                                    right_brackets_index2 = bet_name_value.find(')')
                                    if (left_brackets_index2 != -1) and (right_brackets_index2 != -1) :
                                        res['bet2']['bet_name'] = bet_name_value.replace(bet_name_value[left_brackets_index2:right_brackets_index2+1], '')
                                    else:
                                        res['bet2']['bet_name'] = bet_name_value
                                    res['bet2']['bet_variation_name'] = bet_name_value 
                                    bet1_break = True
                            if bet1_break and bet2_break:
                                break

                        # b1_break = False
                        # b2_break = False
                        # for variationsData in bet_variations_data:
                        #     if not b1_break:
                        #         if res['bet1']['bv_id'] == variationsData[_ID_]:
                        #             res['bet1']['bet_variation_name'] = variationsData[_NAME_]
                        #             b1_break = True
                        #     if not b2_break:
                        #         if res['bet2']['bv_id'] == variationsData[_ID_]:
                        #             res['bet2']['bet_variation_name'] = variationsData[_NAME_]
                        #             b2_break = True
                        #     if b1_break and b2_break:
                        #         break
                    else:
                        result = ''
            except Exception, e:
                traceback.print_exc()
                print e
                result = ''
        else:
            result = ''
        print 'res_len:', len(result)
        return result

    def change_handicap(self, title):
        '''
        转换盘口
        '''
        if title == 'GBH2-Y()':
            title = 'Team2 to score in both halves - yes'
        elif title == 'GBH2-N()':
            title = 'Team2 to score in both halves - no'
        elif title == 'GBH1-Y()':
            title = 'Team1 to score in both halves - yes'
        elif title == 'GBH1-N()':
            title = 'Team1 to score in both halves - no'
        elif title.startswith('F-F1'):
            title = title.replace('F-F1', 'AH1')
        elif title.startswith('F-F2'):
            title = title.replace('F-F2', 'AH2')
        elif title.startswith('1X2-2'):
            title = '2'
        elif title.startswith('1X2-1'):
            title = '1'
        elif title.startswith('1X2-X'):
            title = 'X'
        elif title == 'DC-1X()':
            title = '1X'
        elif title == 'DC-X2()':
            title = 'X2'
        elif title.startswith('EH-EH1'):
            title = title.replace('EH-EH1', 'EH1')
        elif title.startswith('EH-EH2'):
            title = title.replace('EH-EH2', 'EH2')
        elif title == 'BTS-Y()':
            title = 'Both to score'
        elif title == 'BTS-N()':
            title = 'One scoreless'
        elif title.startswith('OU2-TO'):
            title = title.replace('OU2-TO', 'TO') + ' for Team2'
        elif title.startswith('OU2-TU'):
            title = title.replace('OU2-TU', 'TU') + ' for Team2'
        elif title.startswith('OU1-TO'):
            title = title.replace('OU1-TO', 'TO') + ' for Team1'
        elif title.startswith('OU1-TU'):
            title = title.replace('OU1-TU', 'TU') + ' for Team1'
        elif title == 'ML-ML1()':
            title = 'Team1 win'
        elif title == 'ML-ML2()':
            title = 'Team2 win'
        elif title.startswith('OU-TO'):
            title = title.replace('OU-TO', 'TO')
        elif title.startswith('OU-TU'):
            title = title.replace('OU-TU', 'TU')
        elif title.startswith('EG1-EG'):
            title = title.replace('EG1-EG', 'Exact') + ' for Team1'
        elif title.startswith('EG2-EG'):
            title = title.replace('EG2-EG', 'Exact') + ' for Team2'
        elif title == 'OE-ODD()':
            title = 'Odd'
        elif title == 'OE-EVEN()':
            title = 'Even'
        else:
            title = title 
        return title

    def refresh_token(self, access_token):
        '''
        刷新token
        '''
        url = 'https://api-lv.betburger.com/api/v1/refresh_token?access_token='
        url += access_token 
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Length': '93',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'api-lv.betburger.com',
            'Origin': 'https://www.betburger.com',
            'Referer': 'https://www.betburger.com/arbs/live',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                                'Chrome/66.0.3359.139 Safari/537.36'
        }
        form_data = {
            'mouse_clicks': '0',
            'context_changes': '0',
            'mouse_movements': '75',
            'total_time': '60',
            'time_on_page': '60',
            'requests': '31'
        }
        new_access_token = self.is_request_success(url, methods='post', headers=headers, formData=form_data)
        print 'new_access_token:', new_access_token
        return new_access_token

    def get_directories(self, url, url_mid_name):
        '''
        获取运动的名称
        '''
        work_dir = os.getcwd()
        file_dir = './tmp/' + url_mid_name + '.txt'
        dir_list = os.listdir(work_dir + '/tmp')
        is_open = True
        for dir in dir_list:
            if dir.split('.')[0] == url_mid_name:
                is_open = False
        headers_tmp={'If-None-Match': '3a0362770e0052df257ccb65039d9110'}
        headers = self.make_headers(headers_tmp)

        if is_open:
            data = self.is_request_success(url, methods='get', headers=headers)
            print len(data)
            if data != "":
                data = json.loads(data)
                with open(file_dir, 'w') as f:
                    f.write(str(data))
                return data
            else:
                return ""
        else:
            with open(file_dir, 'r') as f:
                fstr = f.read()
            return eval(fstr)

    def get_betburger_web_content(self, url, search_filter_id=''):
        '''
        从betburger获取数据
        '''

        # 创建请求头信息 
        headers_tmp = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        headers = self.make_headers(headers_tmp)
        formData = {
            'auto_update': 'true',
            # 'notification_sound': 'true' if len(self.cookies) > 0 else 'false',
            'notification_sound': 'true',
            'notification_popup': 'false',
            'show_event_arbs': 'true',
            'grouped': 'true',
            'per_page': '50',
            'sort_by': 'percent',
            'event_id': '',
            '''
            'event_arb_types[]': '1',
            'event_arb_types[]': '2',
            'event_arb_types[]': '3',
            'event_arb_types[]': '4',
            'event_arb_types[]': '5',
            'event_arb_types[]': '6',
            'event_arb_types[]': '7',
            '''
            'is_live': 'true',
            'search_filter[]': search_filter_id if search_filter_id else '25555',
        }
        data = self.is_request_success(url=url, methods='post', headers=headers, formData=formData)
        # print data
        return data

    def get_directory_data(self, dir_id, dir_data, dir_kw, get_kw):
        '''
        获取目录对应的数据
        '''
        if dir_data:
            if dir_data[dir_kw] != "":
                for d in dir_data[dir_kw]:
                    if d['id'] == dir_id:
                        return d[get_kw]
            else:
                return ""
        return '' 


    def judge_index(self, bet_id, data):
        '''
        判读每场比赛的索引位置
        '''
        n = 0 
        for b in data['bets']:
            if b['id'] == bet_id:
                return n
            n += 1    

    # 获取bet_values值
    def get_bet_value(self, url):
        '''
        if len(self.cookies) > 0:
            try:
                access_token = self.cookies[1]
                url += access_token
            except Exception, e:
                print e
        '''
        headers = self.make_headers(None)
        data = self.is_request_success(url=url, methods='get', headers=headers)
        if data != "":
            data = json.loads(data)
            return data
        else:
            return ""

    def is_request_success(self, url, methods, headers, params='', formData=""): 
        '''
        判断request请求是否成功， 并返回所有的数据
        '''
        try:
            n = 1
            while True:
                if methods == 'post':
                    rp = requests.post(url, data=formData, headers=headers, timeout=10)
                else:
                    rp = requests.get(url, headers=headers, params=params, timeout=10)
                if rp.status_code == 200:
                    return rp.content
                if n >= 10:
                    return ''
                n += 1
        except requests.exceptions.Timeout:
            print 'request请求超时！'
            return ''
        except Exception, e:
            print e
            # traceback.print_exc()
            return "" 

    def make_headers(self, tmp=None):
        '''
        制作头信息
        '''
        headers = {}
        headers['Accept'] = '*/*'
        # headers['accept-encoding'] = 'gzip, deflate, br'
        headers['Accept-Language'] = 'zh-CN,zh;q=0.9'
        headers['Connection'] = 'keep-alive'
        headers['Host'] = 'api-lv.betburger.com'
        headers['Origin'] = 'https://www.betburger.com'
        headers['Referer'] = 'https://www.betburger.com/arbs/live'
        headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                                'Chrome/66.0.3359.139 Safari/537.36'

        if tmp is not None:
            try:
                for key, value in dict(tmp).items():
                    headers[key] = value
            except Exception, e:
                print e
        return headers

    '''
    用户登陆
    '''

    def get_user_data(self):
        '''
        获取search_filters_id的值
        '''
        global _ACCESS_TOKEN
        n = 0
        replay_conut = 3
        tmp = self.isLogined()
        print '是否登录成功：', tmp
        while not tmp:
            is_login = self.login()
            if is_login:
                access_token = self.get_access_token()
                if access_token:
                    break
            time.sleep(1)
            if n > replay_conut:
                return ''
            n += 1
        tmp = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'api-lv.betburger.com',          
        }
        headers = self.make_headers(tmp)
        url = 'https://api-lv.betburger.com/api/v1/search_filters?access_token='
        if not _ACCESS_TOKEN:
            access_token = self.get_access_token()
            url += access_token
        
        rp = self.is_login_request_success(url=url, methods='get', headers=headers)
        if rp:
            json_data = rp.content
            try:
                search_filter_id = json.loads(json_data)[0]['id']
                print('access_token and id==================================:%s---%d'%(access_token, search_filter_id))
                if search_filter_id and access_token:
                    return search_filter_id, access_token
                else:
                    return ''
            except Exception, e:
                print e
                return ''
        else:
            return ''

    def get_access_token(self):
        '''
        获取access_token的值
        '''
        url = 'https://www.betburger.com/settings?live=true'
        
        cookies_dict = self.get_cookies()
        # headers = self.betburger_live_access_token_headers()
        tmp = {
            'Host': 'www.betburger.com',
            'X-Requested-With': 'XMLHttpRequest',
        }
        headers = self.make_headers(tmp)
        rp = self.is_login_request_success(url, methods='get', headers=headers, cookies=cookies_dict)

        if rp:
            try:
                json_data = rp.content
                dict_data = json.loads(json_data)
                access_token = dict_data['access_token']
                if len(access_token):
                    return access_token
                return ''
            except Exception, e:
                print e
                return ''
        else:
            return ''

    def get_cookies(self):
        try:
            with open(_FILE_PATH, 'r') as f:
                fstr = f.read()
                if fstr:
                    return eval(fstr)
        except:
            pass
        return ''

    def isLogined(self):
        if self.get_logined_user():
            return True
        return False

    def login(self):
        '''
        输入用户名，和密码
        '''
        if not self.username or not self.password:
            return False 
        url = 'https://www.betburger.com/users/sign_in'
        # headers = self.betburger_login_headers()
        tmp = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Content-Length': '256',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'www.betburger.com',
            'Origin': 'https://www.betburger.com',
            'Referer': 'https://www.betburger.com/users/sign_in',
            'Upgrade-Insecure-Requests': '1',
        }
        headers = self.make_headers(tmp)
        token_cookie = self.get_token_cookie()
        formData = {
            'utf8': '✓',
            'authenticity_token': token_cookie['token'] if token_cookie  else '',
            'bb_user[email]': self.username,
            'bb_user[password]': self.password,
            # 'bb_user[remember_me]': '0',
            'bb_user[remember_me]': '1' # 记住密码
        }
        cookies_dict = token_cookie['start_cookie'] if token_cookie else ''
        try:
            # urllib3.disable_warnings()
            rp = requests.post(url, headers=headers, data=formData, allow_redirects=False, cookies=cookies_dict, verify=False, timeout=10)
            cookie_dict = dict(rp.cookies)
            with open(_FILE_PATH, 'w') as f:
                f.write(str(cookie_dict))
            return True
        except Exception, e:
            print '===============login==============',e
            traceback.print_exc()
            return False 

    def get_token_cookie(self):
        '''
        获取token， 还有cookie
        '''
        url = 'https://www.betburger.com/users/sign_in'
        # headers = self.get_betburger_token_headers()
        tmp = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Cache-Control': 'max-age=0',
            'Host': 'www.betburger.com',
            'Upgrade-Insecure-Requests': '1',            
        }
        headers = self.make_headers(tmp)
        rp = self.is_login_request_success(url, methods='get', headers=headers)
        if rp:
            web_cookie = dict(rp.cookies)
            html = rp.content
            pattern = '.+name="authenticity_token" value="(.+)?"'
            token_obj = re.search(pattern, html)
            if token_obj is None:
                return ''
            else:
                token = token_obj.group(1)
            print '===========================', token
            web_cookie['time_zone_offset'] = str(8)
            result = {}
            result['token'] = token
            result['start_cookie'] = web_cookie
            return result
        else:
            return ''

    def is_login_request_success(self, url, methods, headers, cookies=None, params='', formData=''):
        '''
        判断请求是否成功,并返回所有的数据
        '''
        try:
            while True:
                # urllib3.disable_warnings()
                if methods == 'get':
                    rp = requests.get(url, headers=headers, params=params, cookies=cookies, verify=False, allow_redirects=False, timeout=10)
                else:
                    rp = requests.post(url, data=formData, headers=headers, cookies=cookies, verify=False, allow_redirects=False, timeout=10)
                if rp.status_code == 200 or rp.status_code == 301:
                    return rp
                else:
                    return None
        except Exception, e:
            print e
            # traceback.print_exc()
            return None

    def get_logined_user(self):
        url = 'https://www.betburger.com/settings/user_data'
        try:
            # headers = self.betburger_live_access_token_headers()
            tmp = {
                'Host': 'www.betburger.com',
                'X-Requested-With': 'XMLHttpRequest',
            }
            headers = self.make_headers(tmp)
            cookies_dict = self.get_cookies()
            if not cookies_dict:
                return ''
            response = requests.get(url, headers=headers, cookies=cookies_dict, timeout=60)
            res_text = response.text
            j_res_text = json.loads(res_text)
            user = str(j_res_text['email'])
            if len(user):
                print 'username:', user
                return True 
        except Exception, e:
            print e
            # traceback.print_exc()
            return False 


if __name__ == '__main__':

    username = '54256821@qq.com'
    password = 'Aa555888'

    bg = Betburger(username, password)
    # bg = Betburger()
    # user_data = bg.get_user_data()
    # print user_data
    print '==========================='
    while True:
        print 'res_num:', len(bg.get_data_info())
