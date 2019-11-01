# -*- coding: utf-8 -*-
# uBase.py
import base64
import dbini
import dwconfig
import hashlib
import MySQLdb
import os
import random
import re
import requests
import smtplib
import sqlalchemy.pool as pool
import sqls as sql
import string
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import uwsgi
from Crypto.Cipher import AES
from datetime      import timedelta
from datetime      import datetime
from email.mime.text import MIMEText
from email.utils   import formatdate
from functools     import partial
from hashids       import Hashids
from MySQLdb.cursors     import DictCursor
from werkzeug      import BaseRequest, datastructures
from walrus        import Walrus
from jinja2        import Environment, FileSystemLoader
from werkzeug.exceptions import HTTPException, abort

uLibPath = r'../uLib'
if uLibPath not in sys.path:
    sys.path.insert(1, uLibPath)
import SiteDefined

try:
    import uwsgi
    bWeb = 1
except ImportError:
    bWeb = 0  # when batch import

gTemplateMTime   = None
gPickletMinMTime = None
hashids          = Hashids(salt='picks with salt')

# SNS
FACEBOOK_APP_ID     = '351177228910084'
FACEBOOK_APP_SECRET = '82c03bfebb940883b7610652f12c1046'

# Cookie Key
COOKIE_KEY = 'MhucXFuEnVJk8C3K'
COOKIE_IV  = 'dogwoodcommunity'

# Policy_Version
POLICY_VERSION = 1
# ----------------------------------------------------------------------------
class UserFunction(object):  # Dummy class for User Functions
    pass

class AESCipher(object):
    def __init__(self, key):
        self.bs = 16
        self.cipher = AES.new(key, AES.MODE_ECB)

    def encrypt(self, raw):
        raw = self._pad(raw)
        encrypted = self.cipher.encrypt(raw)
        encoded = base64.b64encode(encrypted)
        return str(encoded, 'utf-8')

    def decrypt(self, raw):
        decoded = base64.b64decode(raw)
        decrypted = self.cipher.decrypt(decoded)
        return str(self._unpad(decrypted), 'utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    def _unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]
# ----------------------------------------------------------------------------
# SQLAlchemy pool

def _mysql_connect():
    dbParam = dbini.dbParamDic['real'].copy()
    return MySQLdb.Connect(
        db           = dbParam['db'],
        user         = dbParam['user'],
        passwd       = dbParam['pass'],
        host         = dbParam['host'],
        autocommit   = True,
        charset      = 'utf8',
        use_unicode  = True
    )

def _mysql_connect_user():
    dbParam = dbini.dbParamDic['user'].copy()
    return MySQLdb.Connect(
        db           = dbParam['db'],
        user         = dbParam['user'],
        passwd       = dbParam['pass'],
        host         = dbParam['host'],
        autocommit   = True,
        charset      = 'utf8',
        use_unicode  = True
    )
mypool     = pool.QueuePool(_mysql_connect, recycle=3600)
mypooluser = pool.QueuePool(_mysql_connect_user, recycle=3600)

# ----------------------------------------------------------------------------
def _dic_values(keys, xDic):
    xList = []
    for key in keys:
        if key in xDic:
            xList.append(xDic[key])
    return xList

def _initialize(self):
    ses_id    = self.req.cookies.get('DWSES', 0)
    dict_data = dict(user_class = 'guest')
    if ses_id:
        cipher    = AESCipher(COOKIE_KEY)
        user_id   = cipher.decrypt(ses_id)
        user_data = self.fetchone(sql.selectHas_s_user_sns, dict(user_id = user_id), sDB='user')
        if user_data['cnt'] < 1:
            self.headers_out.add('Set-Cookie', 'DWSES=; path=/; expires=Tue, 01-May-2001 00:00:00 GMT')
        else:
            m_user_data = self.fetchone(sql.selectHas_m_user, dict(user_id = user_id), sDB='user')
            if m_user_data['cnt'] > 0:
                dict_data = dict(user_class = 'member', user_id = user_id)
            else:
                dict_data = dict(user_class = 'pre_member', user_id = user_id)
    else:
        if self.func != 'loginError':
            self.redirect(self, 'https://regist.dogwood-community.jp/loginError')
    self.userData = dict_data
    _checkUser(self)
    return ''

def _setCookies(self, xDic):
    jp_time     = 9 * 60 * 60  # GMT 東京(+9:00)
    logout_time = 24 * 60 * 60  # 24h
    expire      = datetime.now() + timedelta(seconds=logout_time) - timedelta(seconds=jp_time)
    cipher = AESCipher(COOKIE_KEY)
    seskey = cipher.encrypt(xDic)
    self.headers_out.add('Set-Cookie', 'DWSES=%s; path=/; Domain=.dogwood-community.jp; expires=%s' % (seskey, expire.strftime('%a, %d-%b-%Y %H:%M:%S')))
    return ""

def _escape_sql(sSQL, params):
    xsql = '\n'.join(sSQL) if type(sSQL) in [list, tuple] else sSQL
    if params is None:
        return xsql
    for key, value in list(params.items()):
        if key.startswith('no_escape'):
            continue
        if key == 'where':
            continue
        if value in ('=', '!='):  # compare operator                          1
            continue
        if isinstance(value, str):
            # xparams[key] = MySQLdb.escape_string(value).decode('utf-8')
            xsql = xsql.replace(f"[{key}]", f"'{MySQLdb.escape_string(value).decode('utf-8')}'")
    return xsql

def _getHostForDB():
    return ['drpicksk.carenet.com', 'drpicks.carenet.com'][_isHonban()]


reSelect = re.compile(r'^select|^show', re.IGNORECASE)
# def _fetch(sSQL, params=None, bLog=False, req=None, self=None, bNotExecute=False, bFetchOne=False, bCache=True):
# キャッシュしてしまうとテストができないので一旦bCacheをFalse
def _fetch(sSQL, params=None, bLog=False, req=None, self=None, bNotExecute=False, bFetchOne=False, bCache=False, sDB=None):
    def invalidate_cache(perids):
        for perid in perids:
            redis_key = 'cache:drpicks:{}:*'.format(perid)
            for key in self.redis.search(redis_key):
                self.redis.delete(key)
    if self is None:
        raise 'No self...'  # must valid!
    template = _escape_sql(sSQL, params)
    query = str(template)
    bSelect = reSelect.match(query.lstrip())
    fields = ''
    if bCache:
        if type(template) != str:
            fields = template.fields()
    redis_key = None
    cache = self.redis.cache()
    if bSelect:
        key = ""
        if bCache:
            x = _dic_values(fields, params)
            if x:
                key = x[0]
        if bCache and isinstance(key, int) is False and key.isdigit() and len(key) == 8:
            hash = hashlib.sha224(query.encode('utf-8')).hexdigest()
            redis_key = 'drpicks:{}:{}'.format(':'.join(map(str, x)), hash)  # cacheではキーに自動的に「cache:」がprefixされる
            xRec = cache.get(redis_key)
            if xRec is not None:
                if bLog:
                    self.SaveLog('sSQL=%s' % query)
                self.last_rowcount = xRec[0]
                return xRec[1]
    if sDB == 'user':
        conn = mypooluser.connect()
    else:
        conn = mypool.connect()
    cursor = conn.cursor(cursorclass=DictCursor)
    try:
        if bLog:
            self.SaveLog('sSQL=%s' % query)
            if bNotExecute:
                return
        rowcount = cursor.execute(query)
        if bSelect:
            self.last_rowcount = rowcount
            recs = (cursor.fetchone() if bFetchOne else cursor.fetchall())
            if redis_key:
                xRecs = (rowcount, recs)
                cache.set(redis_key, xRecs, self.redis.xTimeSecs)
            return recs
        if fields:
            perids = [x for x in _dic_values(fields, params) if x and isinstance(x, int) is False and x.isdigit() and len(x) == 8]  # peridsは8けた数字
            invalidate_cache(perids)
        return rowcount, cursor.lastrowid  # INSERT/REPLACE/DELETE...
    finally:
        cursor.close()
        conn.close()  # return conn to pool

def _isHonban():
    return os.environ.get('ENV') == 'honban'

# ----------------------------------------------------------------------------
# Misc
def _SaveLog(xtr, self=None):
    if bWeb:
        t = time.localtime(time.time())
        st = time.strftime("%y-%m-%d %H:%M:%S", t)
        uwsgi.log(f"{uwsgi.total_requests()} {st} {xtr}")
    else:  # pytest
        print(xtr)


def _getRedirectURL(self, bQuote=True):
    uri = self.req.script_root + self.req.path
    unparsed_uri = self.req.environ.get('REQUEST_URI', '')
    url_param = unparsed_uri.replace(uri, '')
    paramList = []
    if url_param:
        paramList = url_param[1:].split('&')
    http = 'http'
    sslmode = int(self.req.is_secure)
    if sslmode:
        http = 'https'
    host = self.req.environ.get('HTTP_HOST', '')
    url  = '{}://{}{}'.format(http, host, uri)
    if paramList:
        url = '{}?{}'.format(url, '&'.join(paramList))
    func = self.req.path[1:]
    if 'more_rec' in func:
        url = '{}://{}{}'.format(http, host, self.req.script_root)
    if bQuote:
        return urllib.parse.quote_plus(url)
    return url

def _login(self):
    # sessionを削除
    self.headers_out.add('Set-Cookie', 'ses_%s=; path=/; expires=Tue, 01-May-2001 00:00:00 GMT' % self.hperid)
    subdomain = ('www' if self.isHonban() else 'www-d1')
    com_redirectlogin = 'https://%s.carenet.com/login.php' % subdomain  # ドットコムログイン画面表示
    sURL = '%s?RedirectUrl=%s' % (com_redirectlogin, _getRedirectURL(self))
    line = StringTemplate(self.t.RedirectTemplate)
    line['URL'] = sURL
    self.wtr << str(line)
    abort('redirect')

reLi = re.compile(r'<li>(.*?)</li>')

def _logout(self):
    self.headers_out.add('Set-Cookie', 'key=; path=/; Domain=.dogwood-community.jp; expires=Tue, 01-May-2001 00:00:00 GMT')
    self.redirect(self, "https://job.dogwood-community.jp/logout")

def _set_session_to_cookie(self):
    jp_time     = 9 * 60 * 60  # GMT 東京(+9:00)
    logout_time = 1 * 60 * 60  # 1h
    expire      = datetime.now() + timedelta(seconds=logout_time) - timedelta(seconds=jp_time)
    self.headers_out.add('Set-Cookie', 'ses_%s=%s; path=/;expires=%s' % (self.hperid, self.session_id, expire.strftime('%a, %d-%b-%Y %H:%M:%S')))
    return

def _rec_dp_session(self, req, userDic):
    paramDic = dict(
        personal_id = self.perid,
        linkfrom    = self.form.linkfrom,
        useragent   = req.environ.get('HTTP_USER_AGENT', '')
    )
    res, session_id = self.fetch(sql.insert_dp_session, paramDic)
    return session_id

def _rec_dp_action(self, xaction):
    # health_checkはアクションに記録しない
    if xaction == 'health_check':
        return
    # 新しくPickした際に、news_idを生成してから登録する為、最初は記録しない
    if xaction == 'saveComment' and not self.form.news_id:
        return
    if xaction == 'index':
        xaction = 'top'
        if self.form.get('category'):
            xaction = 'category_%s' % self.form.category
        if self.form.get('usr'):
            xaction = 'usr_%s' % self.display_pid
    paramDic = dict(
        session_id = self.session_id,
        action     = xaction,
        news_id    = self.form.news_id if self.form.news_id else 0
    )
    self.fetch(sql.insert_dp_action, paramDic)

def _redirect(self, url):
    self.redirectURL = url
    self.tParams     = dict(URL = url)
    abort('redirect')

# BOTからのりクエストか判定
def _isSnsBot(self):
    # UAで判定
    useragent = self.req.environ.get('HTTP_USER_AGENT', '').lower()
    # Twitter、Facebook
    for agent in ('twitterbot/1.0', 'facebookexternalhit/1.1', 'Slackbot-LinkExpanding'):
        if agent in useragent:
            return True
    return False

def _init_rediscached(self):
    self.redis = Walrus(host='localhost', port=6379, db=0)
    self.redis.xTimeSecs         = 60 * 30  # secs
    self.redis.TranslateTimeSecs = 60 * 30  # secs 検証用に時間を早めにする

# Userステータスチェック
def _checkUser(self):
    # guestが入れるページ
    guest_list = ['index', 'loginError', '_not_found', 'redirect']
    if self.userData['user_class'] == 'guest' and self.func not in guest_list:
        self.tParams = dict(func = 'loginError')
    return ""

# Redisにキャッシュ
def _set_cache(self, prefix, hash_data, cache_data):
    xTime = self.redis.xTimeSecs
    hash      = hashlib.sha224(hash_data.encode('utf-8')).hexdigest()
    redis_key = f":{prefix}:{hash}"
    self.redis.set(redis_key, cache_data, xTime)

def _get_cache(self, prefix, hash_data):
    hash      = hashlib.sha224(hash_data.encode('utf-8')).hexdigest()
    redis_key = f":{prefix}:{hash}"
    return self.redis.get(redis_key)

# Redisにキャッシュ
def _delete_cache(self, prefix, hash_data):
    hash      = hashlib.sha224(hash_data.encode('utf-8')).hexdigest()
    redis_key = f":{prefix}:{hash}"
    self.redis.delete(redis_key)

# メール送信
def _sendMail(self, title, body, suser = 'system', tomail = ''):
    mailParam      = dwconfig.mailParamDic[suser].copy()
    main_text      = body
    msg            = MIMEText(main_text, "plain", "utf-8")
    msg.replace_header("Content-Transfer-Encoding", "base64")
    msg["Subject"] = title
    msg["From"]    = mailParam['from']
    if tomail == '':
        msg["To"]      = 'tomoya.ikeda.official@gmail.com'
        msg["Cc"]      = 'tetsuya.ikeda@dogwood-community.jp'
    else:
        msg["To"]      = tomail
    msg["Date"]    = formatdate(None, True)
    smtpclient = smtplib.SMTP(mailParam['host'], 587, timeout=10)
    smtpclient.ehlo()
    smtpclient.starttls()
    smtpclient.login(mailParam['user'], mailParam['pass'])
    smtpclient.send_message(msg)
    smtpclient.quit()

# カスタマーメール送信
def _sendCustumMail(self, xDic, type = 'preentry', suser = 'info'):
    if type == 'preentry':
        title = 'Dogwood Community PreEntry完了'
        body  = f"""
{xDic['name']} 様

PreEntryありがとうございます。
PreEntryフォームからの登録を受け付けました。

今後のやりとりはFacebookページで担当者とやりとりさせて頂きますので
一度、下記にメッセージをお願いいたします。

■Facebookページ
https://www.facebook.com/dogwoodcommunity/

以上、よろしくお願いいたします。
        """
        _sendMail(self, title, body, suser, tomail = xDic['mail'])

def _setCommon(self):
    title = SiteDefined.title
    url   = "https://regist.dogwood-community.jp"
    if self.func in SiteDefined.TITLES:
        title = f"{title} {SiteDefined.TITLES[self.func]}"
    if self.func != 'index':
        url = f"{url}/{self.func}"
    self.tParams['time']   = datetime.now()
    self.tParams['title']  = title
    self.tParams['common'] = f"""
<meta name="description" content="{SiteDefined.DESCRIPTION}">
<meta name="keywords" content="{SiteDefined.KEYWORDS}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{SiteDefined.DESCRIPTION}">
<meta property="og:type" content="website">
<meta property="og:image" content="https://job.dogwood-community.jp/images/logo.png" />
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@DogwoodCommuni1">
<meta name="twitter:title" content="{title}".>
<meta name="twitter:url" content="{url}">
<meta name="twitter:description" content="{SiteDefined.DESCRIPTION}" />
<meta name="twitter:image" content="https://job.dogwood-community.jp/images/logo.png" />
    """

def _setFooter(self):
    self.tParams['footer'] = """
<footer class="footer">
  <div class="footer--other">
    <div class="inner inner-sm flex flex-between align-center">
      <h3 class="footer--other_logo"><a href="https://dogwood-community.jp/" target="_blank"><img src="/images/logo.png" height="53" width="110" alt="株式会社Dogwood Community"></a></h3>
      <div class="footer--other_links">
        <ul class="flex">
          <li><a href="https://dogwood-community.jp/about/" target="_blank">会社概要</a><span>｜</span></li>
          <li><a href="https://dogwood-community.jp/https://dogwood-community.jp/contact//" target="_blank">お問い合わせ</a><span>｜</span></li>
          <li><a href="https://dogwood-community.jp/privacypolicy/" target="_blank">プライバシーポリシー</a></li>
        </ul>
        <p>Copyright© 2019 Dogwood Community All Rights Reserved.</p>
      </div>
    </div>
  </div>
</footer>
    """

def randomname(n):
    randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
    return ''.join(randlst)

def _makeUserID(self, strFlag=False):
    for i in range(10):
        id  = random.randint(10000000000, 19999999999)
        ids = self.fetchone(sql.selectHas_s_user_sns, dict(user_id = str(id)), sDB='user')
        if ids['cnt'] > 0:
            continue
        else:
            break
    return id if strFlag is False else str(id)

def _makeUserKey(self):
    for i in range(10):
        key  = randomname(8)
        keys = self.fetchone(sql.selectHas_m_user_key, dict(user_key = key), sDB='user')
        if keys['cnt'] > 0:
            continue
        else:
            break
    return key
# ----------------------------------------------------------------------------
def run_web(env, sr, app, wkdir, validFunctions):
    req = BaseRequest(env)  # http://werkzeug.pocoo.org/docs/0.11/wrappers/
    env = Environment(loader=FileSystemLoader('./', encoding='utf8'))
    # ------------------------------------------------------------------------
    # Convenient user functions

    xDic = {}
    self = UserFunction()
    _init_rediscached(self)
    self.html          = ''
    self.form          = {}
    self.tParams       = {}
    self.userDara      = {}
    self.req           = req
    self.form_original = req.values.to_dict()
    self.form['host']  = req.host
    self.func          = ''
    self.headers_out   = datastructures.Headers()
    self.redirectURL   = ''
    self.redirect      = _redirect
    self.fetch         = partial(_fetch, req=req, self=self)
    self.fetchone      = partial(_fetch, req=req, self=self, bFetchOne=True)
    self.SaveLog       = partial(_SaveLog, self=self)
    self.escape_sql    = _escape_sql
    # self.rec_dp_action = _rec_dp_action
    self.session_id           = ''

    # ------------------------------------------------------------------------
    # dispatch
    try:
        handle   = None
        func     = req.path[1:]
        func     = 'index' if not func else func
        if func not in validFunctions:  # 安全の為チェックする
            func = '_not_found'
        self.func = func
        handle   = getattr(app, func)
        _initialize(self)
        xDic     = handle(self, req)
    except HTTPException:
        func = 'redirect'
        pass  # raised by abort in redirectPage...
    if 'func' in xDic:
        func  = xDic['func']
    _setCommon(self)
    _setFooter(self)
    self.headers_out.add('Cache-Control', 'no-cache')
    if 'Content-Type' not in self.headers_out:
        self.headers_out['Content-Type'] = 'text/html'
    env  = Environment(loader=FileSystemLoader('./', encoding='utf8'))
    tmpl = env.get_template(f'./template/{func}.html')
    html = tmpl.render(self.tParams)
    sr('200 OK', list(self.headers_out.items()))
    # sr('200 OK', [('Cache-Control', 'no-cache'), ('Content-Type', 'text/html')])
    return [html.encode('utf-8')]


# End
