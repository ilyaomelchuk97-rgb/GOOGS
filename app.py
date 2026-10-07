#!/usr/bin/env python3
"""Локальное веб-приложение учёта работ. Python stdlib + SQLite; openpyxl нужен только для импорта/экспорта XLSX."""
import calendar
import csv
import datetime as dt
import hashlib
import hmac
import io
import json
import mimetypes
import math
import os
import re
import secrets
import sqlite3
import threading
import traceback
import backup_tools
import d1_store
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'worktrack.sqlite3'
BACKUP_DIR = ROOT / 'backups'
DB_LOCK = threading.RLock()
BUILD_ID = '20261006-28'  # Public /health marker to verify which build Render actually serves.
# New effects reuse the existing CHECK(kind IN ('people','speech')) table safely.
# This keeps old production D1/SQLite backups and schema compatible.
PRANK_EFFECT_PREFIX = '\x1eFORMA_EFFECT_V1:'
PRANK_NEW_KINDS = ('cat','achievement','parade')
TZ = ZoneInfo('Europe/Minsk')
TODAY = lambda: dt.datetime.now(TZ).date()
MONTH_PATTERN = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]{3,40}$')

def connect():
    backend=os.environ.get('DATABASE_BACKEND','sqlite').lower()
    if os.environ.get('RENDER')=='true' and backend!='d1':
        raise RuntimeError('Render requires DATABASE_BACKEND=d1; refusing ephemeral SQLite')
    if backend=='d1': return d1_store.D1Connection()
    if backend!='sqlite': raise RuntimeError('Unsupported DATABASE_BACKEND')
    con = sqlite3.connect(DB, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    con.execute('PRAGMA busy_timeout=15000')
    return con

def init_db():
    with connect() as db:
        db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
          password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','employee')),
          is_staff INTEGER NOT NULL DEFAULT 1 CHECK(is_staff IN (0,1)),
          active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS tasks (
          id INTEGER PRIMARY KEY, title TEXT NOT NULL UNIQUE COLLATE NOCASE, unit TEXT NOT NULL DEFAULT 'шт.',
          norm REAL NOT NULL DEFAULT 0, category TEXT NOT NULL DEFAULT 'Другое', active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS entries (
          id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), task_id INTEGER NOT NULL REFERENCES tasks(id),
          work_date TEXT NOT NULL, quantity REAL NOT NULL CHECK(quantity > 0), note TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(user_id,task_id,work_date));
        CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(work_date);
        CREATE TABLE IF NOT EXISTS cell_comments (
          user_id INTEGER NOT NULL REFERENCES users(id), task_id INTEGER NOT NULL REFERENCES tasks(id),
          work_date TEXT NOT NULL, body TEXT NOT NULL,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY(user_id,task_id,work_date));
        CREATE INDEX IF NOT EXISTS idx_cell_comments_date ON cell_comments(work_date);
        CREATE TABLE IF NOT EXISTS attendance (
          id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), day TEXT NOT NULL,
          status TEXT NOT NULL CHECK(status IN ('present','absent')), reason TEXT NOT NULL DEFAULT '',
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id,day));
        CREATE TABLE IF NOT EXISTS daily_hours (
          day TEXT PRIMARY KEY, hours REAL NOT NULL CHECK(hours BETWEEN 0 AND 24),
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS personal_hours (
          user_id INTEGER NOT NULL REFERENCES users(id), day TEXT NOT NULL,
          hours REAL NOT NULL CHECK(hours BETWEEN 0 AND 24),
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY(user_id,day));
        CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
          expires_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS activity (
          id INTEGER PRIMARY KEY, actor_id INTEGER REFERENCES users(id), action TEXT NOT NULL,
          detail TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS prank_presence (
          session_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
          last_seen TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_prank_presence_user ON prank_presence(user_id,last_seen);
        CREATE TABLE IF NOT EXISTS prank_events (
          id INTEGER PRIMARY KEY, target_id INTEGER NOT NULL REFERENCES users(id),
          kind TEXT NOT NULL CHECK(kind IN ('people','speech')),
          body TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_prank_events_target ON prank_events(target_id,id);
        ''')
        # Право администратора отдельно от принадлежности к сотрудникам: повышение
        # работника не должно удалять его работы из табеля и сводного отчёта.
        if 'is_staff' not in [col[1] for col in db.execute('PRAGMA table_info(users)')]:
            db.execute('ALTER TABLE users ADD COLUMN is_staff INTEGER NOT NULL DEFAULT 1')
        db.execute("UPDATE users SET is_staff=0 WHERE username='admin' AND role='admin' AND is_staff<>0")
        # Исправляем старые повышения, при которых работнику вместе с ролью admin
        # ошибочно ставили is_staff=0: это прятало его из отчётов и табеля.
        # Сохраняем одну исходную нештатную учётную запись администратора.
        primary=db.execute('''SELECT id FROM users WHERE role='admin' AND is_staff=0
            ORDER BY CASE WHEN username='admin' THEN 0 ELSE 1 END,created_at,id LIMIT 1''').fetchone()
        if primary:
            db.execute('UPDATE users SET is_staff=1 WHERE role=? AND is_staff=0 AND id<>?',
                       ('admin',primary['id']))
        # Перенос комментариев из старых записей при обновлении существующей базы.
        db.execute('''INSERT OR IGNORE INTO cell_comments(user_id,task_id,work_date,body)
            SELECT user_id,task_id,work_date,note FROM entries WHERE note<>?''',('',))

def hashed_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 260000)
    return salt.hex() + ':' + digest.hex()

def valid_password(stored, password):
    try:
        salt, digest = stored.split(':')
        actual = hashed_password(password, bytes.fromhex(salt)).split(':')[1]
        return hmac.compare_digest(actual, digest)
    except (ValueError, TypeError): return False

def json_rows(rows): return [dict(r) for r in rows]
def log(db, user_id, action, detail):
    db.execute('INSERT INTO activity(actor_id,action,detail) VALUES(?,?,?)',(user_id,action,detail[:350]))

def date_ok(value, future=False):
    try:
        day = dt.date.fromisoformat(value)
        if day.isoformat() != value or day.year < 2020 or day > TODAY()+dt.timedelta(days=366 if future else 0): raise ValueError()
        return day
    except (TypeError, ValueError): raise APIError(400,'Некорректная дата')

def scheduled_hours(day):
    weekday=dt.date.fromisoformat(day).weekday()
    return 8.25 if weekday<4 else 7.0 if weekday==4 else 0.0

def calculate_productivity(month,rows,users,attendance,daily_hours,personal_hours):
    """Как в исходном Excel: ROUND(нормо-часы, 0) / часы по табелю × 100."""
    count=calendar.monthrange(*map(int,month.split('-')))[1]
    by_user={}
    for row in rows:
        by_user[row['user_id']]=by_user.get(row['user_id'],0)+float(row['hours'])
    status_map={(a['user_id'],a['day']):a['status'] for a in attendance}
    global_map={a['day']:float(a['hours']) for a in daily_hours}
    personal_map={(a['user_id'],a['day']):float(a['hours']) for a in personal_hours}
    people=[]
    for user in users:
        uid=user['id'];worked=0.0
        for i in range(1,count+1):
            day=f'{month}-{i:02d}'
            status=status_map.get((uid,day),'present' if dt.date.fromisoformat(day).weekday()<5 else 'off')
            if status=='present':worked+=personal_map.get((uid,day),global_map.get(day,scheduled_hours(day)))
        norm=by_user.get(uid,0.0)
        rounded_norm=math.floor(norm+0.5) # Excel ROUND(...,0), для положительных нормо-часов
        people.append({'user_id':uid,'name':user['name'],'work_hours':round(worked,2),
                       'norm_hours':round(norm,3),'rounded_norm_hours':rounded_norm,
                       'percent':round(rounded_norm/worked*100,2) if worked else None})
    total_work=round(sum(row['work_hours'] for row in people),2)
    total_norm=round(sum(row['norm_hours'] for row in people),3)
    total_rounded=sum(row['rounded_norm_hours'] for row in people)
    overall={'work_hours':total_work,'norm_hours':total_norm,'rounded_norm_hours':total_rounded,
             'percent':round(total_rounded/total_work*100,2) if total_work else None}
    return people,overall

def month_range(month):
    if not MONTH_PATTERN.fullmatch(month or ''): raise APIError(400,'Некорректный месяц')
    year, mon = map(int,month.split('-'))
    if not 2020 <= year <= TODAY().year+1: raise APIError(400,'Месяц вне допустимого диапазона')
    return month+'-01', f'{year}-{mon:02d}-{calendar.monthrange(year,mon)[1]:02d}'

class APIError(Exception):
    def __init__(self, status, message): self.status=status; self.message=message

class Handler(BaseHTTPRequestHandler):
    server_version = 'Forma/1.0'
    def log_message(self, fmt, *args):
        # Не выводим резервный токен сеанса в журнал HTTP-запросов.
        message=re.sub(r'([?&]forma_ticket=)[^&\s]+',r'\1[redacted]',fmt%args)
        print('%s %s'%(self.address_string(),message),flush=True)
    def send_json(self, data, status=200, cookie=None):
        raw=json.dumps(data,ensure_ascii=False,default=str).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','no-referrer')
        if cookie: self.send_header('Set-Cookie',cookie)
        self.end_headers(); self.wfile.write(raw)
    def send_bytes(self, raw, filename, mime):
        self.send_response(200); self.send_header('Content-Type',mime)
        self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
        self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(raw)
    def auth_token(self):
        # Прокси предпросмотра может блокировать cookie и зарезервировать Authorization.
        # Свой заголовок позволяет работать в iframe без сторонних cookie.
        token=self.headers.get('X-Forma-Session','').strip()
        if token: return token if len(token)<=256 else None
        # Резервный путь: некоторые прокси вырезают даже нестандартные заголовки.
        ticket=parse_qs(urlparse(self.path).query).get('forma_ticket',[''])[0]
        if ticket: return ticket if len(ticket)<=256 else None
        authorization=self.headers.get('Authorization','')
        if authorization.startswith('Bearer '):
            token=authorization[7:].strip()
            return token if len(token)<=256 else None
        cookie=SimpleCookie()
        try: cookie.load(self.headers.get('Cookie',''))
        except Exception: return None
        return cookie['session'].value if 'session' in cookie else None
    def user(self, db):
        token=self.auth_token()
        if not token: return None
        return db.execute('''SELECT u.id,u.name,u.username,u.role,u.is_staff,u.active FROM sessions s JOIN users u ON u.id=s.user_id
            WHERE s.token_hash=? AND s.expires_at>? AND u.active=1''',
            (hashlib.sha256(token.encode()).hexdigest(),dt.datetime.now(dt.timezone.utc).isoformat())).fetchone()
    def require(self, db, admin=False):
        user=self.user(db)
        if not user:
            print('auth rejected: x-header=%s bearer=%s cookie=%s' %
                  (bool(self.headers.get('X-Forma-Session')),
                   self.headers.get('Authorization','').startswith('Bearer '),
                   bool(self.headers.get('Cookie'))),flush=True)
            raise APIError(401,'Войдите в аккаунт')
        if admin and user['role']!='admin': raise APIError(403,'Требуются права администратора')
        return user
    def body(self):
        if 'application/json' not in self.headers.get('Content-Type',''): raise APIError(415,'Требуется JSON')
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<1 or length>32768: raise APIError(413,'Неверный размер запроса')
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict): raise ValueError()
            return data
        except (ValueError,UnicodeDecodeError): raise APIError(400,'Некорректный JSON')
    def backup_body(self):
        if self.headers.get('Content-Type','').split(';')[0] not in ('application/octet-stream','application/zip'):
            raise APIError(415,'Загрузите ZIP-файл резервной копии')
        try: size=int(self.headers.get('Content-Length','0'))
        except ValueError: raise APIError(400,'Некорректный размер файла')
        if not 0<size<=backup_tools.MAX_ARCHIVE: raise APIError(413,'Архив слишком большой (максимум 25 МБ)')
        return self.rfile.read(size)
    def setup_gate(self, db):
        # This is a one-time, opt-in setup path. It must not be available to
        # ordinary employees or against an already-populated D1 database.
        if not isinstance(db,d1_store.D1Connection): raise APIError(404,'Страница недоступна')
        key=os.environ.get('INITIAL_IMPORT_TOKEN','')
        if len(key)<32: raise APIError(404,'Первоначальная загрузка не включена')
        if any(db.execute('SELECT COUNT(*) FROM "'+table+'"').fetchone()[0]
               for table in d1_store.TABLES):
            raise APIError(409,'База уже содержит данные. Повторная загрузка запрещена')
        return key
    def setup_page(self):
        with connect() as db: self.setup_gate(db)
        data=(ROOT/'web'/'setup.html').read_bytes()
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers(); self.wfile.write(data)
    def setup_import(self):
        with connect() as db:
            expected=self.setup_gate(db)
            supplied=self.headers.get('X-Forma-Setup-Key','')
            if len(supplied)>256 or not hmac.compare_digest(supplied,expected):
                raise APIError(403,'Неверный одноразовый ключ загрузки')
            password=self.headers.get('X-Forma-New-Password','')
            if not re.fullmatch(r'[\x21-\x7e]{14,128}',password):
                raise APIError(400,'Новый пароль администратора: 14–128 латинских символов, цифр и знаков, без пробелов')
            raw=self.backup_body()
            try: data,manifest,details=backup_tools.inspect(raw)
            except backup_tools.BackupError as exc: raise APIError(400,str(exc))
            with sqlite3.connect(':memory:') as source:
                source.deserialize(data)
                primary=source.execute('SELECT id,username FROM users WHERE role="admin" AND active=1 AND is_staff=0 LIMIT 1').fetchone()
                if not primary: raise APIError(400,'В архиве нет основного администратора')
                source.execute('UPDATE users SET password_hash=? WHERE id=?',(hashed_password(password),primary[0]))
                source.commit()
                d1_store.replace_atomic(db,source)
                expected_fingerprint=backup_tools.fingerprint(source)
            # The uploaded ZIP is intentionally never written to Render's disk.
            if (backup_tools.summary(db)['counts']!=details['counts'] or
                backup_tools.fingerprint(db)!=expected_fingerprint):
                raise APIError(503,'Данные отправлены в D1, но проверка не прошла. Не загружайте ZIP снова; обратитесь за помощью')
            return self.send_json({'ok':True,'username':primary[1],'counts':details['counts'],
                                   'first_work_date':details['first_work_date'],
                                   'last_work_date':details['last_work_date']})
    def serve_static(self, path):
        if path=='/': path='/index.html'
        if path not in ('/index.html','/styles.css','/main.js','/courier-cat.png','/courier-cat-walk.png'): raise APIError(404,'Страница не найдена')
        file=ROOT/'web'/path[1:]
        data=file.read_bytes(); mime=mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
        content_type=mime if path.endswith('.png') else mime+'; charset=utf-8'
        self.send_response(200); self.send_header('Content-Type',content_type); self.send_header('Content-Length',str(len(data)))
        self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Cache-Control','no-store, max-age=0, must-revalidate')
        self.send_header('Pragma','no-cache')
        self.end_headers(); self.wfile.write(data)
    def do_GET(self): self.dispatch('GET')
    def do_POST(self): self.dispatch('POST')
    def do_PATCH(self): self.dispatch('PATCH')
    def do_DELETE(self): self.dispatch('DELETE')
    def dispatch(self, method):
        # Восстановление БД не должно пересечься с чтением или записью другого запроса.
        with DB_LOCK: self._dispatch(method)
    def _dispatch(self, method):
        parsed=urlparse(self.path); path=parsed.path; q=parse_qs(parsed.query)
        try:
            if path=='/health' and method=='GET':
                return self.send_json({'ok':True,'service':'Forma','backend':os.environ.get('DATABASE_BACKEND','sqlite'),'build':BUILD_ID})
            if path=='/setup' and method=='GET':
                return self.setup_page()
            if path=='/setup/import' and method=='POST':
                return self.setup_import()
            if path=='/internal/backup' and method=='POST':
                # Dedicated read-only credential for Google Drive backups: never give
                # Apps Script an administrator password or an interactive session.
                expected=os.environ.get('AUTOMATED_BACKUP_TOKEN','')
                supplied=self.headers.get('X-Forma-Backup-Key','')
                if len(expected)<32 or len(supplied)>256 or not hmac.compare_digest(supplied,expected):
                    raise APIError(403,'Доступ запрещён')
                with connect() as db:
                    signature=backup_tools.fingerprint(db,backup_tools.CONTENT_TABLES)
                    previous=self.headers.get('X-Forma-If-Unchanged','').strip()
                    if len(previous)==64 and hmac.compare_digest(previous,signature):
                        self.send_response(204)
                        self.send_header('Cache-Control','no-store')
                        self.send_header('X-Forma-Data-Signature',signature)
                        self.end_headers()
                        return
                    raw,_manifest=self.make_backup(db)
                name='forma-backup-'+dt.datetime.now(TZ).strftime('%Y%m%d-%H%M%S')+'.zip'
                self.send_response(200)
                self.send_header('Content-Type','application/zip')
                self.send_header('Content-Disposition',f'attachment; filename="{name}"')
                self.send_header('Content-Length',str(len(raw)))
                self.send_header('Cache-Control','no-store')
                self.send_header('X-Content-Type-Options','nosniff')
                self.send_header('X-Forma-Data-Signature',signature)
                self.end_headers()
                return self.wfile.write(raw)
            if not path.startswith('/api/'):
                if method!='GET': raise APIError(405,'Метод не поддерживается')
                return self.serve_static(path)
            with connect() as db:
                if path=='/api/login' and method=='POST': return self.login(db)
                user=self.require(db, path in ('/api/users','/api/tasks','/api/logs','/api/report','/api/export') and path not in ('/api/tasks',)) if path!='/api/session' else self.user(db)
                if path=='/api/session': return self.send_json({'user':dict(user) if user else None,'today':TODAY().isoformat()})
                if path=='/api/logout' and method=='POST':
                    token=self.auth_token()
                    if token:
                        token_hash=hashlib.sha256(token.encode()).hexdigest()
                        db.execute('DELETE FROM sessions WHERE token_hash=?',(token_hash,))
                        db.execute('DELETE FROM prank_presence WHERE session_hash=?',(token_hash,))
                    log(db,user['id'],'logout','Вышел из системы'); db.commit()
                    return self.send_json({'ok':True},cookie='session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0')
                if path=='/api/backup/status' and method=='GET': return self.backup_status(db,self.require(db,True))
                if path=='/api/backup/download' and method=='GET': return self.backup_download(db,self.require(db,True))
                if path=='/api/backup/safety' and method=='GET': return self.backup_safety(db,self.require(db,True),q)
                if path=='/api/backup/inspect' and method=='POST': return self.backup_inspect(db,self.require(db,True))
                if path=='/api/backup/restore' and method=='POST': return self.backup_restore(db,self.require(db,True),q)
                if path=='/api/prank/poll' and method=='GET': return self.prank_poll(db,user,q)
                if path=='/api/presence' and method=='GET': return self.presence(db,user)
                if path=='/api/prank/online' and method=='GET': return self.prank_online(db,self.require(db,True))
                if path=='/api/prank/send' and method=='POST': return self.prank_send(db,self.require(db,True),self.body())
                if path=='/api/bootstrap' and method=='GET': return self.bootstrap(db,user,q)
                if path=='/api/entries' and method=='POST': return self.save_entry(db,user,self.body())
                if path=='/api/comments' and method=='POST': return self.save_comment(db,user,self.body())
                if path.startswith('/api/entries/') and method=='PATCH': return self.edit_entry(db,user,path,self.body())
                if path.startswith('/api/entries/') and method=='DELETE': return self.delete_entry(db,user,path)
                if path=='/api/attendance' and method=='POST': return self.save_attendance(db,self.require(db,True),self.body())
                if path=='/api/hours' and method=='POST': return self.save_hours(db,self.require(db,True),self.body())
                if path=='/api/users' and method=='POST': return self.add_user(db,self.require(db,True),self.body())
                if path.startswith('/api/users/') and method=='PATCH': return self.edit_user(db,self.require(db,True),path,self.body())
                if path=='/api/tasks' and method=='POST': return self.add_task(db,self.require(db,True),self.body())
                if path.startswith('/api/tasks/') and method=='PATCH': return self.edit_task(db,self.require(db,True),path,self.body())
                if path=='/api/password' and method=='POST': return self.password(db,self.require(db,True),self.body())
                if path=='/api/logs' and method=='GET':
                    self.require(db,True)
                    rows=db.execute('''SELECT a.id,a.action,a.detail,a.created_at,COALESCE(u.name,'Система') actor
                      FROM activity a LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 150''').fetchall()
                    return self.send_json({'logs':json_rows(rows)})
                if path=='/api/report' and method=='GET': return self.report(db,self.require(db,True),q)
                if path=='/api/export' and method=='GET': return self.export(db,self.require(db,True),q)
                raise APIError(404,'Адрес не найден')
        except APIError as exc: self.send_json({'error':exc.message},exc.status)
        except d1_store.RemoteError as exc: self.send_json({'error':str(exc)},503)
        except sqlite3.IntegrityError: self.send_json({'error':'Конфликт данных. Обновите страницу и повторите действие'},409)
        except (BrokenPipeError,ConnectionResetError): pass
        except Exception:
            traceback.print_exc(); self.send_json({'error':'Ошибка сервера'},500)
    def login(self,db):
        data=self.body(); username=str(data.get('username','')).strip(); password=str(data.get('password',''))
        row=db.execute('SELECT * FROM users WHERE username=? AND active=1',(username,)).fetchone()
        if not row or not valid_password(row['password_hash'],password): raise APIError(401,'Неверный логин или пароль')
        token=secrets.token_urlsafe(32)
        expires=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=14)).isoformat()
        db.execute('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row['id'],expires))
        log(db,row['id'],'login','Вход в систему'); db.commit()
        self.send_json({'user':{k:row[k] for k in ('id','name','username','role','is_staff','active')},'session_token':token},cookie=f'session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age=1209600')
    def backup_status(self,db,user):
        safety=[]
        if BACKUP_DIR.is_dir():
            for item in sorted(BACKUP_DIR.glob('before-restore-*.zip'),reverse=True)[:20]:
                if item.is_file() and not item.is_symlink():
                    safety.append({'name':item.name,'size':item.stat().st_size})
        self.send_json({'current':backup_tools.summary(db),'safety':safety})
    def backup_safety(self,db,user,q):
        name=q.get('name',[''])[0]
        if not re.fullmatch(r'before-restore-\d{8}-\d{6}-[0-9a-f]{8}\.zip',name):
            raise APIError(400,'Некорректное имя резервной копии')
        file=BACKUP_DIR/name
        if not file.is_file() or file.is_symlink(): raise APIError(404,'Копия не найдена')
        self.send_bytes(file.read_bytes(),name,'application/zip')
    def make_backup(self,db):
        if isinstance(db,d1_store.D1Connection):
            snapshot=d1_store.sqlite_snapshot(db)
            try: return backup_tools.archive(snapshot)
            finally: snapshot.close()
        return backup_tools.archive(db)
    def backup_download(self,db,user):
        raw,manifest=self.make_backup(db)
        name='forma-backup-'+dt.datetime.now(TZ).strftime('%Y%m%d-%H%M%S')+'.zip'
        self.send_bytes(raw,name,'application/zip')
    def backup_inspect(self,db,user):
        raw=self.backup_body()
        try: _data,manifest,saved=backup_tools.inspect(raw)
        except backup_tools.BackupError as exc: raise APIError(400,str(exc))
        current=backup_tools.summary(db)
        self.send_json({'created_at':manifest['created_at'],'backup':saved,'current':current,
                        'comparison':backup_tools.compare(current,saved),
                        'archive_hash':hashlib.sha256(raw).hexdigest(),
                        'current_signature':backup_tools.fingerprint(db)})
    def backup_restore(self,db,user,q):
        if self.headers.get('X-Forma-Confirm')!='RESTORE':
            raise APIError(400,'Подтвердите полную замену данных')
        raw=self.backup_body()
        try: data,manifest,saved=backup_tools.inspect(raw)
        except backup_tools.BackupError as exc: raise APIError(400,str(exc))
        supplied_hash=q.get('archive_hash',[''])[0]
        supplied_signature=q.get('current_signature',[''])[0]
        if not hmac.compare_digest(hashlib.sha256(raw).hexdigest(),supplied_hash):
            raise APIError(400,'Архив изменился после сравнения. Сравните данные ещё раз')
        if not hmac.compare_digest(backup_tools.fingerprint(db),supplied_signature):
            raise APIError(409,'Данные сайта изменились после сравнения. Сравните архив ещё раз')
        # Страховочная копия на сервере: скачайте свою копию отдельно.
        safety,_=self.make_backup(db)
        BACKUP_DIR.mkdir(mode=0o700,parents=True,exist_ok=True)
        safe_name='before-restore-'+dt.datetime.now(TZ).strftime('%Y%m%d-%H%M%S')+'-'+secrets.token_hex(4)+'.zip'
        safe_path=BACKUP_DIR/safe_name
        with safe_path.open('xb') as output: output.write(safety)
        safe_path.chmod(0o600)
        with sqlite3.connect(':memory:') as source:
            source.deserialize(data)
            if isinstance(db,d1_store.D1Connection): d1_store.replace_atomic(db,source)
            else: source.backup(db)
        if not isinstance(db,d1_store.D1Connection):
            db.execute('DELETE FROM sessions')
            db.execute('DELETE FROM prank_presence')
            db.execute('DELETE FROM prank_events')
        log(db,None,'backup_restored',f'Восстановлено из копии {manifest["created_at"]}; перед заменой: {safe_name}')
        db.commit()
        return self.send_json({'ok':True,'safety_copy':safe_name,'restored':saved})
    def prank_poll(self,db,user,q):
        """Heartbeat and short-lived event stream for open browser tabs."""
        now=dt.datetime.now(dt.timezone.utc)
        token_hash=hashlib.sha256(self.auth_token().encode()).hexdigest()
        initial='after' not in q
        try:
            after=int(q.get('after',['0'])[0])
            if after<0: raise ValueError()
        except (ValueError,TypeError): raise APIError(400,'Некорректный номер события')
        db.execute('''INSERT INTO prank_presence(session_hash,user_id,last_seen) VALUES(?,?,?)
          ON CONFLICT(session_hash) DO UPDATE SET user_id=excluded.user_id,last_seen=excluded.last_seen''',
          (token_hash,user['id'],now.isoformat()))
        latest=db.execute('SELECT COALESCE(MAX(id),0) FROM prank_events').fetchone()[0]
        # Первая проверка вкладки подписывает только на будущие события.
        events=[] if initial else json_rows(db.execute('''SELECT id,kind,body FROM prank_events
          WHERE target_id=? AND id>? AND created_at>? ORDER BY id LIMIT 20''',
          (user['id'],after,(now-dt.timedelta(minutes=2)).isoformat())).fetchall())
        for event in events:
            if event['kind']=='speech' and event['body'].startswith(PRANK_EFFECT_PREFIX):
                try:
                    packed=json.loads(event['body'][len(PRANK_EFFECT_PREFIX):])
                    if packed.get('kind') in PRANK_NEW_KINDS and isinstance(packed.get('text'),str):
                        event['kind']=packed['kind'];event['body']=packed['text']
                except (ValueError,TypeError,AttributeError): pass
        db.commit()
        return self.send_json({'events':events,'last_id':max(latest,after)})
    def presence(self,db,user):
        """Authenticated roster: only active sessions with a recent browser heartbeat."""
        now=dt.datetime.now(dt.timezone.utc)
        rows=db.execute('''SELECT DISTINCT u.id,u.name,u.role FROM users u
          JOIN prank_presence p ON p.user_id=u.id JOIN sessions s ON s.token_hash=p.session_hash
          WHERE u.active=1 AND p.last_seen>=? AND s.expires_at>?
          ORDER BY CASE WHEN u.role='admin' THEN 0 ELSE 1 END,u.name''',
          ((now-dt.timedelta(seconds=15)).isoformat(),now.isoformat())).fetchall()
        return self.send_json({'users':json_rows(rows)})
    def prank_online(self,db,user):
        now=dt.datetime.now(dt.timezone.utc)
        cutoff=(now-dt.timedelta(seconds=15)).isoformat()
        rows=db.execute('''SELECT DISTINCT p.user_id FROM prank_presence p
          JOIN users u ON u.id=p.user_id JOIN sessions s ON s.token_hash=p.session_hash
          WHERE p.last_seen>=? AND s.expires_at>? AND u.active=1 AND u.is_staff=1 ''',
          (cutoff,now.isoformat())).fetchall()
        return self.send_json({'user_ids':[row['user_id'] for row in rows]})
    def prank_send(self,db,user,data):
        try: target=int(data.get('user_id'))
        except (TypeError,ValueError): raise APIError(400,'Выберите сотрудника')
        if isinstance(data.get('user_id'),bool): raise APIError(400,'Выберите сотрудника')
        kind=data.get('kind')
        if kind not in ('people','speech',*PRANK_NEW_KINDS): raise APIError(400,'Неизвестный эффект')
        body=data.get('text','')
        if not isinstance(body,str): raise APIError(400,'Текст должен быть строкой')
        body=body.strip()
        if kind=='speech' and (not body or len(body)>400): raise APIError(400,'Введите текст от 1 до 400 символов')
        if kind=='cat' and (not body or len(body)>140): raise APIError(400,'Сообщение кота: от 1 до 140 символов')
        if kind=='achievement' and (not body or len(body)>80): raise APIError(400,'Название достижения: от 1 до 80 символов')
        if kind in ('people','parade'): body=''
        stored_kind=kind if kind in ('people','speech') else 'speech'
        stored_body=PRANK_EFFECT_PREFIX+json.dumps({'kind':kind,'text':body},ensure_ascii=False) if kind in PRANK_NEW_KINDS else body
        recipient=db.execute('SELECT name FROM users WHERE id=? AND is_staff=1 AND active=1',(target,)).fetchone()
        if not recipient: raise APIError(404,'Сотрудник не найден')
        now=dt.datetime.now(dt.timezone.utc)
        present=db.execute('''SELECT 1 FROM prank_presence p JOIN sessions s ON s.token_hash=p.session_hash
          WHERE p.user_id=? AND p.last_seen>=? AND s.expires_at>? LIMIT 1''',
          (target,(now-dt.timedelta(seconds=15)).isoformat(),now.isoformat())).fetchone()
        if not present: raise APIError(409,'Пользователь сейчас не в сети. Попросите его открыть сайт.')
        db.execute('INSERT INTO prank_events(target_id,kind,body,created_at) VALUES(?,?,?,?)',
                   (target,stored_kind,stored_body,now.isoformat()))
        db.execute('DELETE FROM prank_events WHERE created_at<?',((now-dt.timedelta(days=1)).isoformat(),))
        label={'people':'Человечки','speech':'Голосовое сообщение','cat':'Кот-курьер',
               'achievement':'Достижение','parade':'Мини-парад'}[kind]
        log(db,user['id'],'prank',f'{label} → {recipient["name"]}')
        db.commit()
        return self.send_json({'ok':True,'name':recipient['name']})
    def bootstrap(self,db,user,q):
        month=q.get('month',[TODAY().strftime('%Y-%m')])[0]; first,last=month_range(month)
        admin=user['role']=='admin'
        users=json_rows(db.execute('SELECT id,name,username,role,is_staff,active,created_at FROM users WHERE is_staff=1 ORDER BY active DESC,name').fetchall()) if admin else [dict(user)]
        tasks=json_rows(db.execute('SELECT id,title,unit,norm,category,active FROM tasks ORDER BY active DESC,id').fetchall())
        eargs=[first,last]; aargs=[first,last]
        efilter=''; afilter=''
        if not admin:
            efilter=' AND e.user_id=?'; afilter=' AND a.user_id=?'; eargs.append(user['id']); aargs.append(user['id'])
        entries=json_rows(db.execute('''SELECT e.id,e.user_id,e.task_id,e.work_date,e.quantity,e.note,e.created_at,e.updated_at
            FROM entries e WHERE e.work_date BETWEEN ? AND ?'''+efilter+' ORDER BY e.work_date DESC,e.id DESC',eargs).fetchall())
        comment_args=[first,last] if admin else [first,last,user['id']]
        comments=json_rows(db.execute('''SELECT user_id,task_id,work_date,body FROM cell_comments
            WHERE work_date BETWEEN ? AND ?'''+('' if admin else ' AND user_id=?'),comment_args).fetchall())
        attendance=json_rows(db.execute('SELECT a.user_id,a.day,a.status,a.reason FROM attendance a WHERE a.day BETWEEN ? AND ?'+afilter,aargs).fetchall())
        daily_hours=json_rows(db.execute('SELECT day,hours FROM daily_hours WHERE day BETWEEN ? AND ?',(first,last)).fetchall())
        hours_filter='' if admin else ' AND user_id=?'
        hours_args=[first,last] if admin else [first,last,user['id']]
        personal_hours=json_rows(db.execute('SELECT user_id,day,hours FROM personal_hours WHERE day BETWEEN ? AND ?'+hours_filter,hours_args).fetchall())
        recent=json_rows(db.execute('''SELECT a.action,a.detail,a.created_at,COALESCE(u.name,'Система') actor
            FROM activity a LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 6''').fetchall()) if admin else []
        return self.send_json({'user':dict(user),'users':users,'tasks':tasks,'entries':entries,'comments':comments,'attendance':attendance,
            'daily_hours':daily_hours,'personal_hours':personal_hours,'recent':recent,'month':month,'today':TODAY().isoformat()})
    def save_entry(self,db,user,data):
        task_id=int(data.get('task_id') or 0); day=date_ok(data.get('date'))
        try: qty=float(data.get('quantity'))
        except (ValueError,TypeError): raise APIError(400,'Укажите количество')
        if not 0<qty<=10000000 or not __import__('math').isfinite(qty): raise APIError(400,'Количество должно быть больше нуля')
        note=str(data.get('note','')).strip()[:500]
        task=db.execute('SELECT id,title,active FROM tasks WHERE id=?',(task_id,)).fetchone()
        if not task or not task['active']: raise APIError(400,'Работа не найдена или архивирована')
        target=int(data.get('user_id') or user['id'])
        if target!=user['id'] and user['role']!='admin': raise APIError(403,'Можно изменять только свои записи')
        owner=db.execute('SELECT name FROM users WHERE id=? AND is_staff=1 AND active=1',(target,)).fetchone()
        if not owner: raise APIError(400,'Сотрудник не найден')
        db.execute('''INSERT INTO entries(user_id,task_id,work_date,quantity,note) VALUES(?,?,?,?,?)
            ON CONFLICT(user_id,task_id,work_date) DO UPDATE SET quantity=excluded.quantity,note=excluded.note,updated_at=CURRENT_TIMESTAMP''',
            (target,task_id,day.isoformat(),qty,note))
        if note:
            db.execute('''INSERT INTO cell_comments(user_id,task_id,work_date,body) VALUES(?,?,?,?)
                ON CONFLICT(user_id,task_id,work_date) DO UPDATE SET body=excluded.body,updated_at=CURRENT_TIMESTAMP''',
                (target,task_id,day.isoformat(),note))
        elif 'note' in data:
            db.execute('DELETE FROM cell_comments WHERE user_id=? AND task_id=? AND work_date=?',(target,task_id,day.isoformat()))
        log(db,user['id'],'entry',f'{owner["name"]}: {task["title"][:85]} — {qty:g} ({day.isoformat()})'); db.commit()
        return self.send_json({'ok':True})
    def save_comment(self,db,user,data):
        day=date_ok(data.get('date')).isoformat()
        try: task_id=int(data.get('task_id')); target=int(data.get('user_id') or user['id'])
        except (ValueError,TypeError): raise APIError(400,'Некорректная работа или сотрудник')
        if target!=user['id'] and user['role']!='admin': raise APIError(403,'Можно комментировать только свою таблицу')
        owner=db.execute('SELECT name FROM users WHERE id=? AND is_staff=1 AND active=1',(target,)).fetchone()
        task=db.execute('SELECT title,active FROM tasks WHERE id=?',(task_id,)).fetchone()
        if not owner or not task: raise APIError(400,'Сотрудник или работа не найдены')
        if not task['active'] and not db.execute('''SELECT 1 FROM entries WHERE user_id=? AND task_id=? AND work_date=?
            UNION ALL SELECT 1 FROM cell_comments WHERE user_id=? AND task_id=? AND work_date=?''',
            (target,task_id,day,target,task_id,day)).fetchone():
            raise APIError(400,'Архивная работа недоступна для новой записи')
        comment=str(data.get('comment') or '').strip()
        if len(comment)>500: raise APIError(400,'Комментарий не длиннее 500 символов')
        if comment:
            db.execute('''INSERT INTO cell_comments(user_id,task_id,work_date,body) VALUES(?,?,?,?)
                ON CONFLICT(user_id,task_id,work_date) DO UPDATE SET body=excluded.body,updated_at=CURRENT_TIMESTAMP''',
                (target,task_id,day,comment))
        else:
            db.execute('DELETE FROM cell_comments WHERE user_id=? AND task_id=? AND work_date=?',(target,task_id,day))
        db.execute('UPDATE entries SET note=?,updated_at=CURRENT_TIMESTAMP WHERE user_id=? AND task_id=? AND work_date=?',
            (comment,target,task_id,day))
        log(db,user['id'],'comment',f'{owner["name"]}: {task["title"][:80]} ({day}) — {"комментарий сохранён" if comment else "комментарий удалён"}')
        db.commit(); self.send_json({'ok':True})
    def edit_entry(self,db,user,path,data):
        try: entry_id=int(path.rsplit('/',1)[1])
        except ValueError: raise APIError(400,'Некорректный идентификатор')
        existing=db.execute('SELECT * FROM entries WHERE id=?',(entry_id,)).fetchone()
        if not existing: raise APIError(404,'Запись не найдена')
        if existing['user_id']!=user['id'] and user['role']!='admin': raise APIError(403,'Нет доступа')
        day=date_ok(data.get('date'))
        try: task_id=int(data.get('task_id') or 0); target=int(data.get('user_id') or existing['user_id']); qty=float(data.get('quantity'))
        except (ValueError,TypeError): raise APIError(400,'Проверьте заполненные поля')
        if not 0<qty<=10000000 or not __import__('math').isfinite(qty): raise APIError(400,'Количество должно быть больше нуля')
        if target!=existing['user_id'] and user['role']!='admin': raise APIError(403,'Нет доступа')
        task=db.execute('SELECT title,active FROM tasks WHERE id=?',(task_id,)).fetchone()
        owner=db.execute('SELECT name FROM users WHERE id=? AND is_staff=1',(target,)).fetchone()
        if not task or (not task['active'] and task_id!=existing['task_id']) or not owner: raise APIError(400,'Работа или сотрудник не найдены')
        note=str(data.get('note','')).strip()[:500]
        try:
            db.execute('''UPDATE entries SET user_id=?,task_id=?,work_date=?,quantity=?,note=?,updated_at=CURRENT_TIMESTAMP WHERE id=?''',
                (target,task_id,day.isoformat(),qty,note,entry_id))
        except sqlite3.IntegrityError: raise APIError(409,'Запись для этого сотрудника, дня и работы уже существует')
        old_key=(existing['user_id'],existing['task_id'],existing['work_date'])
        new_key=(target,task_id,day.isoformat())
        if old_key!=new_key: db.execute('DELETE FROM cell_comments WHERE user_id=? AND task_id=? AND work_date=?',old_key)
        if note:
            db.execute('''INSERT INTO cell_comments(user_id,task_id,work_date,body) VALUES(?,?,?,?)
                ON CONFLICT(user_id,task_id,work_date) DO UPDATE SET body=excluded.body,updated_at=CURRENT_TIMESTAMP''',(*new_key,note))
        else: db.execute('DELETE FROM cell_comments WHERE user_id=? AND task_id=? AND work_date=?',new_key)
        log(db,user['id'],'entry',f'Исправлено: {owner["name"]}: {task["title"][:85]} — {qty:g} ({day.isoformat()})');db.commit()
        return self.send_json({'ok':True})
    def delete_entry(self,db,user,path):
        try: entry_id=int(path.rsplit('/',1)[1])
        except ValueError: raise APIError(400,'Некорректный идентификатор')
        row=db.execute('SELECT e.*,t.title FROM entries e JOIN tasks t ON t.id=e.task_id WHERE e.id=?',(entry_id,)).fetchone()
        if not row: raise APIError(404,'Запись не найдена')
        if row['user_id']!=user['id'] and user['role']!='admin': raise APIError(403,'Нет доступа')
        db.execute('DELETE FROM entries WHERE id=?',(entry_id,)); log(db,user['id'],'delete_entry',f'Удалена запись: {row["title"][:85]} ({row["work_date"]})'); db.commit()
        self.send_json({'ok':True})
    def save_attendance(self,db,user,data):
        if user['role']!='admin': raise APIError(403,'Табель изменяет только администратор')
        day=date_ok(data.get('date'),True)
        target=int(data.get('user_id') or user['id'])
        owner=db.execute('SELECT name FROM users WHERE id=? AND is_staff=1 AND active=1',(target,)).fetchone()
        if not owner: raise APIError(400,'Сотрудник не найден')
        status=data.get('status'); reason=str(data.get('reason','')).strip()[:160]
        if status not in ('present','absent','clear'): raise APIError(400,'Некорректный статус')
        if status=='absent' and not reason: raise APIError(400,'Укажите причину отсутствия')
        if status=='clear': db.execute('DELETE FROM attendance WHERE user_id=? AND day=?',(target,day.isoformat()))
        else: db.execute('''INSERT INTO attendance(user_id,day,status,reason) VALUES(?,?,?,?)
            ON CONFLICT(user_id,day) DO UPDATE SET status=excluded.status,reason=excluded.reason,updated_at=CURRENT_TIMESTAMP''',
            (target,day.isoformat(),status,reason if status=='absent' else ''))
        log(db,user['id'],'attendance',f'{owner["name"]}: {day.isoformat()} — {"отсутствует: "+reason if status=="absent" else "на работе" if status=="present" else "по графику"}')
        db.commit(); self.send_json({'ok':True})
    def save_hours(self,db,user,data):
        if 'hours' not in data: raise APIError(400,'Укажите часы или сброс к графику')
        day=date_ok(data.get('date'),True).isoformat()
        target=data.get('user_id')
        if target not in (None,''):
            try: target=int(target)
            except (ValueError,TypeError): raise APIError(400,'Некорректный сотрудник')
            owner=db.execute('SELECT name FROM users WHERE id=? AND is_staff=1',(target,)).fetchone()
            if not owner: raise APIError(400,'Сотрудник не найден')
            label=owner['name']
        else:
            target=None; label='Вся команда'
        if data.get('hours') is None:
            if target is None: db.execute('DELETE FROM daily_hours WHERE day=?',(day,))
            else: db.execute('DELETE FROM personal_hours WHERE user_id=? AND day=?',(target,day))
            detail='сброс к графику'
        else:
            try: hours=float(data['hours'])
            except (ValueError,TypeError): raise APIError(400,'Введите количество часов')
            if isinstance(data['hours'],bool) or not math.isfinite(hours) or not 0<=hours<=24 or round(hours,2)!=hours:
                raise APIError(400,'Количество часов: от 0 до 24, не более двух знаков после запятой')
            hours=round(hours,2)
            if target is None:
                db.execute('''INSERT INTO daily_hours(day,hours) VALUES(?,?)
                    ON CONFLICT(day) DO UPDATE SET hours=excluded.hours,updated_at=CURRENT_TIMESTAMP''',(day,hours))
            else:
                db.execute('''INSERT INTO personal_hours(user_id,day,hours) VALUES(?,?,?)
                    ON CONFLICT(user_id,day) DO UPDATE SET hours=excluded.hours,updated_at=CURRENT_TIMESTAMP''',(target,day,hours))
            detail=f'{hours:g} ч'
        log(db,user['id'],'hours',f'{label}: {day} — {detail}')
        db.commit(); self.send_json({'ok':True})
    def add_user(self,db,user,data):
        name=str(data.get('name','')).strip()[:90]; username=str(data.get('username','')).strip().lower()
        password=str(data.get('password',''))
        if len(name)<2 or not USERNAME_PATTERN.fullmatch(username) or len(password)<8: raise APIError(400,'Укажите имя, логин (от 3 символов) и пароль (от 8 символов)')
        try: row=db.execute('INSERT INTO users(name,username,password_hash,role) VALUES(?,?,?,"employee")',(name,username,hashed_password(password)))
        except sqlite3.IntegrityError: raise APIError(409,'Такой логин уже существует')
        log(db,user['id'],'user_added',f'Добавлен сотрудник {name} (@{username})'); db.commit(); self.send_json({'ok':True,'id':row.lastrowid})
    def edit_user(self,db,user,path,data):
        try: uid=int(path.rsplit('/',1)[1])
        except ValueError: raise APIError(400,'Некорректный пользователь')
        target=db.execute('SELECT * FROM users WHERE id=? AND is_staff=1',(uid,)).fetchone()
        if not target: raise APIError(404,'Сотрудник не найден')
        updates=[]; params=[]
        if 'role' in data:
            role=data['role']
            if role not in ('admin','employee'): raise APIError(400,'Некорректные права доступа')
            if uid==user['id'] and role!='admin': raise APIError(400,'Нельзя снять права администратора с самого себя')
            updates.append('role=?'); params.append(role)
            # Права администратора не забирают у человека статус сотрудника:
            # он остаётся в личной таблице, графиках, табеле и отчётах.
            if role=='admin': updates.append('is_staff=1')
            if target['role']=='admin' and role=='employee':
                db.execute('DELETE FROM sessions WHERE user_id=?',(uid,))
        if 'active' in data:
            updates.append('active=?'); params.append(1 if data['active'] is True else 0)
            if data['active'] is not True: db.execute('DELETE FROM sessions WHERE user_id=?',(uid,))
        if 'name' in data:
            name=str(data['name']).strip()[:90]
            if len(name)<2: raise APIError(400,'Введите имя')
            updates.append('name=?'); params.append(name)
        if 'username' in data:
            username=str(data['username']).strip().lower()
            if not USERNAME_PATTERN.fullmatch(username):
                raise APIError(400,'Логин: от 3 до 40 символов, латиница, цифры, точка, дефис или подчёркивание')
            updates.append('username=?'); params.append(username)
            if username!=target['username'].lower():
                db.execute('DELETE FROM sessions WHERE user_id=?',(uid,))
        if 'password' in data:
            if len(str(data['password']))<8: raise APIError(400,'Пароль не менее 8 символов')
            updates.append('password_hash=?'); params.append(hashed_password(str(data['password'])))
            db.execute('DELETE FROM sessions WHERE user_id=?',(uid,))
        if not updates: raise APIError(400,'Нет изменений')
        try: db.execute('UPDATE users SET '+','.join(updates)+' WHERE id=?',params+[uid])
        except sqlite3.IntegrityError: raise APIError(409,'Такой логин уже используется')
        detail=f'Обновлён сотрудник {target["name"]}'
        if 'username' in data and username!=target['username'].lower():
            detail+=f' · логин: @{target["username"]} → @{username}'
        if 'role' in data and data['role']!=target['role']: detail+=f' · права: {"администратор" if data["role"]=="admin" else "сотрудник"}'
        log(db,user['id'],'user_updated',detail); db.commit(); self.send_json({'ok':True})
    def add_task(self,db,user,data):
        title=str(data.get('title','')).strip()[:300]; unit=str(data.get('unit','шт.')).strip()[:30] or 'шт.'
        category=str(data.get('category','Другое')).strip()[:60] or 'Другое'
        try: norm=float(data.get('norm') or 0)
        except (ValueError,TypeError): raise APIError(400,'Некорректная норма')
        if len(title)<4 or not 0<=norm<=10000: raise APIError(400,'Введите название и корректную норму')
        try: res=db.execute('INSERT INTO tasks(title,unit,norm,category) VALUES(?,?,?,?)',(title,unit,norm,category))
        except sqlite3.IntegrityError: raise APIError(409,'Такая работа уже есть в каталоге')
        log(db,user['id'],'task_added',f'Добавлена работа: {title[:120]}'); db.commit(); self.send_json({'ok':True,'id':res.lastrowid})
    def edit_task(self,db,user,path,data):
        try: tid=int(path.rsplit('/',1)[1])
        except ValueError: raise APIError(400,'Некорректная работа')
        old=db.execute('SELECT * FROM tasks WHERE id=?',(tid,)).fetchone()
        if not old: raise APIError(404,'Работа не найдена')
        updates=[]; params=[]
        for key,maxlen in [('title',300),('unit',30),('category',60)]:
            if key in data:
                value=str(data[key]).strip()[:maxlen]
                if not value: raise APIError(400,'Поле не может быть пустым')
                updates.append(key+'=?'); params.append(value)
        if 'norm' in data:
            try: norm=float(data['norm'])
            except (ValueError,TypeError): raise APIError(400,'Некорректная норма')
            if not 0<=norm<=10000: raise APIError(400,'Некорректная норма')
            updates.append('norm=?'); params.append(norm)
        if 'active' in data: updates.append('active=?'); params.append(1 if data['active'] is True else 0)
        if not updates: raise APIError(400,'Нет изменений')
        try: db.execute('UPDATE tasks SET '+','.join(updates)+' WHERE id=?',params+[tid])
        except sqlite3.IntegrityError: raise APIError(409,'Такая работа уже существует')
        log(db,user['id'],'task_updated',f'Изменена работа: {old["title"][:120]}'); db.commit(); self.send_json({'ok':True})
    def password(self,db,user,data):
        if user['role']!='admin': raise APIError(403,'Пароли меняет только администратор')
        old=str(data.get('old','')); new=str(data.get('new',''))
        row=db.execute('SELECT password_hash FROM users WHERE id=?',(user['id'],)).fetchone()
        if not valid_password(row['password_hash'],old): raise APIError(400,'Текущий пароль неверен')
        if len(new)<8: raise APIError(400,'Новый пароль не менее 8 символов')
        db.execute('UPDATE users SET password_hash=? WHERE id=?',(hashed_password(new),user['id']))
        log(db,user['id'],'password','Пароль изменён'); db.commit(); self.send_json({'ok':True})
    def report_data(self,db,month):
        first,last=month_range(month)
        rows=json_rows(db.execute('''SELECT t.id task_id,t.title,t.unit,t.norm,t.category,u.id user_id,u.name,
            ROUND(SUM(e.quantity),3) quantity,ROUND(SUM(e.quantity)*t.norm,3) hours
            FROM entries e JOIN tasks t ON t.id=e.task_id JOIN users u ON u.id=e.user_id
            WHERE e.work_date BETWEEN ? AND ? GROUP BY t.id,u.id ORDER BY t.id,u.name''',(first,last)).fetchall())
        users=json_rows(db.execute('SELECT id,name FROM users WHERE is_staff=1 ORDER BY name').fetchall())
        tasks=json_rows(db.execute('SELECT id,title,unit,norm,category,active FROM tasks ORDER BY id').fetchall())
        attendance=json_rows(db.execute('SELECT user_id,day,status,reason FROM attendance WHERE day BETWEEN ? AND ?',(first,last)).fetchall())
        daily_hours=json_rows(db.execute('SELECT day,hours FROM daily_hours WHERE day BETWEEN ? AND ?',(first,last)).fetchall())
        personal_hours=json_rows(db.execute('SELECT user_id,day,hours FROM personal_hours WHERE day BETWEEN ? AND ?',(first,last)).fetchall())
        comments=json_rows(db.execute('''SELECT c.user_id,c.task_id,c.work_date,c.body,u.name,t.title
            FROM cell_comments c JOIN users u ON u.id=c.user_id JOIN tasks t ON t.id=c.task_id
            WHERE c.work_date BETWEEN ? AND ? ORDER BY c.work_date,u.name''',(first,last)).fetchall())
        return rows,users,tasks,attendance,daily_hours,personal_hours,comments,first,last
    def report(self,db,user,q):
        month=q.get('month',[TODAY().strftime('%Y-%m')])[0]
        rows,users,tasks,attendance,daily_hours,personal_hours,comments,first,last=self.report_data(db,month)
        productivity,overall=calculate_productivity(month,rows,users,attendance,daily_hours,personal_hours)
        self.send_json({'month':month,'rows':rows,'users':users,'tasks':tasks,'attendance':attendance,
            'daily_hours':daily_hours,'personal_hours':personal_hours,'comments':comments,
            'productivity':productivity,'productivity_total':overall})
    def export(self,db,user,q):
        month=q.get('month',[TODAY().strftime('%Y-%m')])[0]
        rows,users,tasks,attendance,daily_hours,personal_hours,comments,first,last=self.report_data(db,month)
        productivity,overall=calculate_productivity(month,rows,users,attendance,daily_hours,personal_hours)
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
            from openpyxl.utils import get_column_letter
        except ImportError: raise APIError(500,'Для экспорта Excel установите openpyxl')
        wb=Workbook(); ws=wb.active; ws.title='Сводный отчёт'
        navy='173347'; teal='158E77'; pale='E7F5EE'; muted='5F7885'
        light='F4F8F9'; line='DFE9EB'; white='FFFFFF'
        ws.sheet_view.showGridLines=False
        end_col=4+len(users)  # A: работа, B: ед., C: норма, далее сотрудники, последний: итог
        summary_end=max(end_col,8)
        month_label=['январь','февраль','март','апрель','май','июнь',
                     'июль','август','сентябрь','октябрь','ноябрь','декабрь'][int(month[5:])-1]+' '+month[:4]
        ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=summary_end)
        for col in range(1,summary_end+1): ws.cell(1,col).fill=PatternFill('solid',fgColor=navy)
        title=ws.cell(1,1,'Сводный отчёт · '+month_label)
        title.font=Font(name='Calibri',size=20,bold=True,color=white)
        title.alignment=Alignment(vertical='center')
        ws.row_dimensions[1].height=46
        ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=summary_end)
        subtitle=ws.cell(2,1,'Все результаты команды, собранные из персональных записей')
        subtitle.font=Font(name='Calibri',size=12,color=muted)
        ws.row_dimensions[2].height=25
        summary=[('СУММА КОЛИЧЕСТВА*',sum(float(x['quantity']) for x in rows)),
                 ('НОРМАТИВНОЕ ВРЕМЯ',round(sum(float(x['hours']) for x in rows),2)),
                 ('РАБОЧИХ ЧАСОВ ПО ТАБЕЛЮ',overall['work_hours']),
                 ('СОТРУДНИКОВ В ОТЧЁТЕ',f'{len({x["user_id"] for x in rows})} / {len(users)}')]
        for idx,(label,value) in enumerate(summary):
            left=1+(idx*summary_end)//4
            right=((idx+1)*summary_end)//4
            ws.merge_cells(start_row=4,start_column=left,end_row=4,end_column=right)
            ws.merge_cells(start_row=5,start_column=left,end_row=5,end_column=right)
            for col in range(left,right+1):
                for rownum in (4,5): ws.cell(rownum,col).fill=PatternFill('solid',fgColor=light)
            label_cell=ws.cell(4,left,label)
            label_cell.font=Font(name='Calibri',size=10,bold=True,color=muted)
            label_cell.alignment=Alignment(vertical='center',wrap_text=True,indent=1)
            value_cell=ws.cell(5,left,value)
            value_cell.font=Font(name='Calibri',size=17,bold=True,color=navy)
            value_cell.alignment=Alignment(vertical='center',indent=1)
            if idx in (0,1,2): value_cell.number_format='#,##0.##'
        ws.row_dimensions[4].height=27;ws.row_dimensions[5].height=35
        ws.merge_cells(start_row=7,start_column=1,end_row=7,end_column=summary_end)
        caption=ws.cell(7,1,'Сводная таблица · '+month_label+' · количество / нормо-часы')
        caption.font=Font(name='Calibri',size=12,bold=True,color=teal)
        ws.row_dimensions[7].height=25
        header_row=8
        labels=['Выполняемая работа','Ед.','Норма, ч']+[x['name'] for x in users]+['Итого']
        for col,label in enumerate(labels,1):
            cell=ws.cell(header_row,col,label)
            cell.fill=PatternFill('solid',fgColor=navy)
            cell.font=Font(name='Calibri',size=11,bold=True,color=white)
            cell.alignment=Alignment(vertical='center',horizontal='left' if col==1 else 'center',wrap_text=True)
        ws.row_dimensions[header_row].height=47
        by_task_user={(x['task_id'],x['user_id']):x for x in rows}
        recorded_tasks={x['task_id'] for x in rows}
        displayed_tasks=[x for x in tasks if x['active'] or x['id'] in recorded_tasks]
        qty_format='#,##0.##';hours_format='#,##0.##" ч"'
        for index,task in enumerate(displayed_tasks):
            number_row=header_row+1+index*2
            hours_row=number_row+1
            background=white if index%2==0 else light
            name=ws.cell(number_row,1,task['title'])
            name.font=Font(name='Calibri',size=12,bold=True,color=navy)
            name.alignment=Alignment(vertical='center',wrap_text=True,indent=1)
            category=ws.cell(hours_row,1,task['category'])
            category.font=Font(name='Calibri',size=10,italic=True,color=muted)
            category.alignment=Alignment(vertical='center',indent=2,wrap_text=True)
            ws.cell(number_row,2,task['unit'])
            norm=ws.cell(number_row,3,task['norm']);norm.number_format='#,##0.###'
            task_qty=0;task_hours=0
            for col,user in enumerate(users,4):
                record=by_task_user.get((task['id'],user['id']))
                if record:
                    qty=float(record['quantity']);hours=float(record['hours'])
                    task_qty+=qty;task_hours+=hours
                    qcell=ws.cell(number_row,col,qty);qcell.number_format=qty_format
                    hcell=ws.cell(hours_row,col,hours);hcell.number_format=hours_format
                else:
                    ws.cell(number_row,col,'—')
            ws.cell(number_row,end_col,round(task_qty,3)).number_format=qty_format
            ws.cell(hours_row,end_col,round(task_hours,3)).number_format=hours_format
            for rownum in (number_row,hours_row):
                for col in range(1,end_col+1):
                    cell=ws.cell(rownum,col)
                    cell.fill=PatternFill('solid',fgColor=pale if col==end_col else background)
                    cell.border=Border(bottom=Side(style='hair',color=line) if rownum==hours_row else Side())
                    if col>=4:cell.alignment=Alignment(vertical='center',horizontal='center')
            for rownum in (number_row,hours_row):
                c=ws.cell(rownum,end_col);c.font=Font(name='Calibri',size=11,bold=True,color='147B65')
            ws.row_dimensions[number_row].height=min(95,max(29,16*(1+(len(task['title'])//58))))
            ws.row_dimensions[hours_row].height=22
        total_row=header_row+1+len(displayed_tasks)*2
        def summary_row(rownum,label,values,fill,color,unit=''):
            for col in range(1,end_col+1):
                c=ws.cell(rownum,col)
                c.fill=PatternFill('solid',fgColor=fill)
                c.font=Font(name='Calibri',size=11,bold=True,color=color)
                c.alignment=Alignment(vertical='center',horizontal='left' if col==1 else 'center',wrap_text=col==1)
            ws.cell(rownum,1,label)
            ws.cell(rownum,2,unit or '—')
            ws.cell(rownum,3,'—')
            for col,value in enumerate(values,4):
                c=ws.cell(rownum,col,value)
                if type(value) in (int,float): c.number_format=qty_format
        quantities=[round(sum(float(x['quantity']) for x in rows if x['user_id']==u['id']),3) for u in users]
        norm_hours=[round(sum(float(x['hours']) for x in rows if x['user_id']==u['id']),3) for u in users]
        summary_row(total_row,'ИТОГО ПО КОМАНДЕ',quantities+[summary[0][1]],navy,white)
        summary_row(total_row+1,'Нормо-часы',norm_hours+[round(sum(float(x['hours']) for x in rows),3)],navy,white,'ч')
        for col in range(4,end_col+1):ws.cell(total_row+1,col).number_format=hours_format
        ws.row_dimensions[total_row].height=30;ws.row_dimensions[total_row+1].height=24
        work_hours={p['user_id']:p['work_hours'] for p in productivity}
        summary_row(total_row+2,'РАБОЧИЕ ЧАСЫ ЗА МЕСЯЦ\nпо табелю · с учётом отсутствий',
                    [work_hours.get(u['id'],0) for u in users]+[overall['work_hours']],
                    'EAF2F5','3A687B','ч')
        for col in range(4,end_col+1):ws.cell(total_row+2,col).number_format=hours_format
        ws.row_dimensions[total_row+2].height=43
        percentages={p['user_id']:p['percent'] for p in productivity}
        summary_row(total_row+3,'ПРОИЗВОДИТЕЛЬНОСТЬ\nокруглённые нормо-часы / рабочие часы × 100 %',
                    [percentages.get(u['id'])/100 if percentages.get(u['id']) is not None else '—' for u in users]
                    +[overall['percent']/100 if overall['percent'] is not None else '—'],
                    'DCF3E8','14765F','%')
        for col in range(4,end_col+1):ws.cell(total_row+3,col).number_format='0.00%'
        ws.row_dimensions[total_row+3].height=52
        note_row=total_row+5
        ws.merge_cells(start_row=note_row,start_column=1,end_row=note_row,end_column=summary_end)
        note=ws.cell(note_row,1,'* Общая сумма количества объединяет разные единицы измерения. Сравнивайте результаты по видам работ или нормо-часам. Производительность = округлённые нормо-часы / рабочие часы по табелю × 100 %. При 0 рабочих часов: «—».')
        note.font=Font(name='Calibri',size=11,color=muted)
        note.alignment=Alignment(vertical='center',wrap_text=True)
        ws.row_dimensions[note_row].height=42
        ws.column_dimensions['A'].width=67
        ws.column_dimensions['B'].width=14
        ws.column_dimensions['C'].width=16
        for col in range(4,end_col):ws.column_dimensions[get_column_letter(col)].width=25
        ws.column_dimensions[get_column_letter(end_col)].width=22
        ws.freeze_panes='D9'
        ws.print_options.horizontalCentered=True
        ws.page_setup.orientation='landscape'
        ws.page_setup.paperSize=ws.PAPERSIZE_A3
        ws.sheet_properties.pageSetUpPr.fitToPage=True
        ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
        ws.print_title_rows='1:8'
        at=wb.create_sheet('Табель 5-2'); day_count=int(last[-2:])
        at.append(['Сотрудник']+[str(i) for i in range(1,day_count+1)]+['Рабочих дней','Отсутствий','Часов по табелю'])
        for cell in at[1]:cell.fill=PatternFill('solid',fgColor=navy);cell.font=Font(bold=True,color='FFFFFF')
        attmap={(x['user_id'],x['day']):x for x in attendance}
        global_map={x['day']:x['hours'] for x in daily_hours}
        personal_map={(x['user_id'],x['day']):x['hours'] for x in personal_hours}
        for u in users:
            vals=[u['name']]; presents=0; absents=0; total_hours=0
            for i in range(1,day_count+1):
                d=f'{month}-{i:02d}'; weekday=dt.date.fromisoformat(d).weekday()<5
                override=attmap.get((u['id'],d)); status=override['status'] if override else ('present' if weekday else 'off')
                if status=='present':
                    presents+=1
                    hours=personal_map.get((u['id'],d),global_map.get(d,scheduled_hours(d)))
                    total_hours+=hours; vals.append(hours)
                elif status=='absent': absents+=1; vals.append(0)
                else: vals.append('—')
            at.append(vals+[presents,absents,round(total_hours,2)]); rr=at.max_row
            for i in range(1,day_count+1):
                d=f'{month}-{i:02d}'; override=attmap.get((u['id'],d))
                status=override['status'] if override else ('present' if dt.date.fromisoformat(d).weekday()<5 else 'off')
                cell=at.cell(rr,i+1);cell.alignment=Alignment(horizontal='center');cell.number_format='0.##'
                cell.fill=PatternFill('solid',fgColor='DDF3E8' if status=='present' else 'FDE3DF' if status=='absent' else 'F2F4F7')
                if status=='absent':cell.comment=__import__('openpyxl').comments.Comment(override['reason'] or 'Отсутствует','Табель')
            at.cell(rr,at.max_column).number_format='0.##'
        at.column_dimensions['A'].width=26
        for i in range(2,at.max_column+1):at.column_dimensions[get_column_letter(i)].width=9 if i<=day_count+1 else 19
        at.freeze_panes='B2'
        detail=wb.create_sheet('Записи');detail.append(['Дата','Сотрудник','Работа','Количество','Ед. изм.','Примечание'])
        for cell in detail[1]:cell.fill=PatternFill('solid',fgColor=navy);cell.font=Font(bold=True,color='FFFFFF')
        entries=db.execute('''SELECT e.work_date,u.name,t.title,e.quantity,t.unit,e.note FROM entries e JOIN users u ON u.id=e.user_id JOIN tasks t ON t.id=e.task_id WHERE e.work_date BETWEEN ? AND ? ORDER BY e.work_date,u.name''',(first,last)).fetchall()
        for entry in entries: detail.append(list(entry))
        for col,width in {'A':17,'B':24,'C':76,'D':18,'E':15,'F':45}.items():detail.column_dimensions[col].width=width
        detail.freeze_panes='C2';detail.auto_filter.ref=f'A1:F{detail.max_row}'
        notes=wb.create_sheet('Комментарии')
        notes.append(['Дата','Сотрудник','Работа','Комментарий'])
        for cell in notes[1]: cell.fill=PatternFill('solid',fgColor=navy);cell.font=Font(bold=True,color='FFFFFF')
        for item in comments: notes.append([item['work_date'],item['name'],item['title'],item['body']])
        for col,width in {'A':17,'B':24,'C':76,'D':80}.items(): notes.column_dimensions[col].width=width
        notes.freeze_panes='C2';notes.auto_filter.ref=f'A1:D{notes.max_row}'
        out=io.BytesIO();wb.save(out)
        self.send_bytes(out.getvalue(),f'forma-report-{month}.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__=='__main__':
    init_db()
    if os.environ.get('RENDER')=='true':
        with connect() as db:
            if not db.execute('SELECT id FROM users WHERE role="admin" AND active=1 LIMIT 1').fetchone():
                if len(os.environ.get('INITIAL_IMPORT_TOKEN',''))<32:
                    raise RuntimeError('D1 is empty: set a strong INITIAL_IMPORT_TOKEN for browser setup, or migrate a verified backup first')
                print('D1 is empty. One-time ZIP upload is available at /setup; remove INITIAL_IMPORT_TOKEN after importing.',flush=True)
    port=int(os.environ.get('PORT','8000'))
    print(f'Forma running at http://0.0.0.0:{port}',flush=True)
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
