# -*- coding: utf-8 -*-
import datetime
import html
import json
import os
import sqls as sql
import sys
from functools    import wraps

uLibPath = r'../uLib'
if uLibPath not in sys.path:
    sys.path.insert(1, uLibPath)
import Defined
import uBase

gwkdir = os.path.dirname(os.path.realpath(__file__))
gValidFunctions = []

REDIS_USER_REGIST = 'regist.company.regist'

def routed(f):
    gValidFunctions.append(f.__name__)

    @wraps(f)
    def wrapper(*args, **kwds):
        return f(*args, **kwds)
    return wrapper

@routed
def _not_found(self, req):
    return ""

@routed
def loginError(self, req):
    return ""

@routed
def error(self, req):
    return ''

@routed
def logout(self, req):
    uBase._logout(self)
    return ''

@routed
def termsOfService(self, req):
    user = self.fetchone(sql.select_s_user_policy, self.userData, sDB='user')
    if user is not None:
        if 'policy_version' in user and uBase.POLICY_VERSION <= int(user['policy_version']):
            self.redirect(self, "https://regist.dogwood-community.jp/entryForm")
    data = self.fetchone(sql.select_m_privacy_policy)
    self.tParams['policy_text'] = data['text']
    return ""

def _setParams(token, type='input', dic={}):
    data = {
        'year_list'           : Defined.YEAR_LIST,
        'month_list'          : Defined.MONTH_LIST,
        'day_list'            : Defined.DAY_LIST,
        'japanese_list'       : Defined.JAPANESE_LIST,
        'nationality_list'    : Defined.NATIONALITY_LIST,
        'language_list'       : Defined.LANGUAGE_LIST,
        'year_expiration_list': Defined.YEAR_EXPIRATION_LIST,
        'specific_skills_list': Defined.SPECIFIED_SKILLS,
        'prefectures_list'    : Defined.PREFECTURES,
        'visa_list'           : Defined.VISA_LIST,
        'token'               : token,
    }
    if type == 'input':
        data.update({
            'year'           : dic['year'] if 'year' in dic else 0,
            'month'          : dic['month'] if 'month' in dic else 0,
            'day'            : dic['day'] if 'day' in dic else 0,
            'expiration_year': dic['expiration_year'] if 'expiration_year' in dic else 0,
            'expiration_month': dic['expiration_month'] if 'expiration_month' in dic else 0,
            'expiration_day': dic['expiration_day'] if 'expiration_day' in dic else 0,
            'jobchange_date_year': dic['jobchange_date_year'] if 'jobchange_date_year' in dic else 0,
            'jobchange_date_month': dic['jobchange_date_month'] if 'jobchange_date_month' in dic else 0,
            'jobchange_date_day': dic['jobchange_date_day'] if 'jobchange_date_day' in dic else 0,
        })
    elif type == 'edit':
        language_dic = dic['language'].split(',')
        if language_dic:
            for i, value in enumerate(language_dic):
                data.update({f'language_{i + 1}': value})
        data.update({
            'zip31': str(dic['address_0'])[0:3],
            'zip32': str(dic['address_0'])[3:7],
        })
    elif type == 'error':
        data.update({
            'func'           : 'entryForm',
            'error'          : '<br><span class="red">エラー：必須項目を入力してください</span>'
        })
    return data

@routed
def entryForm(self, req):
    xDic = {}
    # 利用規約同意
    if 'policy_check' in self.form_original and self.form_original['policy_check']:
        user = self.fetch(sql.select_s_user_policy, self.userData, sDB='user')
        if user:
            self.fetch(sql.update_s_user_policy, dict(user_id = self.userData['user_id'], policy_version = str(uBase.POLICY_VERSION)), bLog=True, sDB='user')
        else:
            self.fetch(sql.insert_s_user_policy, dict(user_id = self.userData['user_id'], policy_version = str(uBase.POLICY_VERSION)), bLog=True, sDB='user')
    # token判定
    if 'token' in self.form_original:
        token = self.form_original['token']
        xDic  = _inputEntryCommon(self, req)
    else:
        token = uBase.randomname(12)
    uBase._set_cache(self, REDIS_USER_REGIST, token, json.dumps(dict(token = 1)))
    xDic.update(_setParams(token, dic = xDic))
    self.tParams = xDic
    return ""

def _inputEntryValidate(self, key, v):
    required = ['salary', 'college', 'final_education', 'license', 'career', 'jobchange', 'specific_skills', 'language', 'language_1', 'language_2', 'language_3', 'language_4', 'language_5', 'lang_str', 'expiration_year', 'expiration_month', 'expiration_day']
    if key not in required and not v:
        raise ValueError
    if key == 'work_location':
        if self.func not in ['entryComplete', 'entryEditComplete']:
            v = Defined.PREFECTURES[v]
    elif key in ['specified_skilled_plans', 'jobchange']:
        if self.func not in ['entryComplete', 'entryEditComplete']:
            v = Defined.REQUIRED[v]
    elif key == 'language':
        if self.func not in ['entryComplete', 'entryEditComplete']:
            lang_str = []
            for value in v.split(','):
                lang_str.append(Defined.LANGUAGE_LIST[value])
            v = ','.join(lang_str)
    return (key, html.escape(v))

def _inputEntryCommon(self, req):
    def _set_Dic(self, xDic, token):
        xDic.update(self.form_original)
        xDic.update({
            'work_location_key'           : self.form_original['work_location'],
            'specified_skilled_plans_key' : self.form_original['specified_skilled_plans'],
            'jobchange_key'               : self.form_original['jobchange'],
            'language_key'                : self.form_original['language'],
        })
        xDic.update({_inputEntryValidate(self, key, v) for key, v in self.form_original.items()})
        uBase._set_cache(self, REDIS_USER_REGIST, token, json.dumps(xDic))
        return xDic
    if not self.form_original:
        xDic = dict(func = 'error')
        pass
    elif 'token' not in self.form_original:
        xDic = dict(func = 'error')
        pass
    else:
        token = self.form_original['token']
        xDic  = json.loads(uBase._get_cache(self, REDIS_USER_REGIST, token))
        if not xDic:
            xDic = dict(func = 'error')
            pass
        try:
            _setParams(token)
            xDic = _set_Dic(self, xDic, token)
        except ValueError:
            # 業種設定
            xDic.update(_setParams(token, type='error'))
        except KeyError:
            # 業種設定
            xDic.update(_setParams(token, type='error'))
    self.tParams = xDic
    return xDic

@routed
def entryConfirm(self, req):
    return _inputEntryCommon(self, req)

@routed
def entryComplete(self, req):
    xDic = _inputEntryCommon(self, req)
    if 'error' not in xDic:
        xDic.update({
            'user_id'        : self.userData['user_id'],
            'user_key'       : uBase._makeUserKey(self),
            'address_0'      : f"{xDic['zip31']}{xDic['zip32']}",
            'birthdate'      : f"{xDic['year']}-{xDic['month']}-{xDic['day']} 00:00:00",
            'visa_expiration': f"{xDic['expiration_year']}-{xDic['expiration_month']}-{xDic['expiration_day']} 00:00:00",
            'jobchange_date' : f"{xDic['jobchange_date_year']}-{xDic['jobchange_date_month']}-{xDic['jobchange_date_day']} 00:00:00"
        })
        self.fetch(sql.insert_m_user, xDic, sDB='user', bLog=True)
        uBase._delete_cache(self, REDIS_USER_REGIST, xDic['token'])
        uBase._sendMail(self, 'PreEntry 完了', 'PreEntryが完了')
        uBase._sendCustumMail(self, xDic, )
    return ""

@routed
def myPage(self, req):
    return ""

def _setEntryData(key, v):
    if key == 'work_location':
        v = Defined.PREFECTURES[str(v)]
    elif key in ['specified_skilled_plans', 'jobchange']:
        v = Defined.REQUIRED[str(v)]
    elif key == 'language':
        lang_str = []
        for value in v.split(','):
            lang_str.append(Defined.LANGUAGE_LIST[value])
        v = ','.join(lang_str)
    return (key, v)

@routed
def myEntryDetail(self, req):
    xDic = self.fetchone(sql.selectForm_m_user, dict(user_id = self.userData['user_id']), sDB='user')
    xDic.update({_setEntryData(key, v) for key, v in xDic.items()})
    self.tParams = xDic
    return ""

@routed
def entryEdit(self, req):
    xDic = {}
    # token判定
    if 'token' in self.form_original:
        token = self.form_original['token']
    else:
        token = uBase.randomname(12)
    uBase._set_cache(self, REDIS_USER_REGIST, token, json.dumps(dict(token = 1)))
    xDic = self.fetchone(sql.selectForm_m_user, dict(user_id = self.userData['user_id']), sDB='user')
    xDic.update({_setEntryData(key, v) for key, v in xDic.items()})
    xDic.update(_setParams(token, type='edit', dic = xDic))
    self.tParams = xDic
    return ""

@routed
def entryEditConfirm(self, req):
    return _inputEntryCommon(self, req)

@routed
def entryEditComplete(self, req):
    xDic = _inputEntryCommon(self, req)
    if 'error' not in xDic:
        xDic.update({
            'user_id'        : self.userData['user_id'],
            'address_0'      : f"{xDic['zip31']}{xDic['zip32']}",
            'birthdate'      : f"{xDic['year']}-{xDic['month']}-{xDic['day']} 00:00:00",
            'visa_expiration': f"{xDic['expiration_year']}-{xDic['expiration_month']}-{xDic['expiration_day']} 00:00:00",
            'jobchange_date' : f"{xDic['jobchange_date_year']}-{xDic['jobchange_date_month']}-{xDic['jobchange_date_day']} 00:00:00"
        })
        self.fetch(sql.update_m_user, xDic, sDB='user')
        uBase._delete_cache(self, REDIS_USER_REGIST, xDic['token'])
    return ""

# ----------------------------------------------------------------------------
# uwsgi entry point
# ----------------------------------------------------------------------------
def application(env, sr):
    return uBase.run_web(env, sr, sys.modules[__name__], gwkdir, gValidFunctions)

# End
