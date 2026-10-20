"""Synchronous, parameterized D1 bridge for Forma's stdlib HTTP backend.

Mode is opt-in via DATABASE_BACKEND=d1. No silent fallback to local SQLite.
D1.batch is atomic for staged writes (<=40 statements per request).
"""
import json
import os
import re
import sqlite3
import secrets
import datetime as dt
import urllib.error
import urllib.request

class RemoteError(RuntimeError):
    pass

class D1Row(dict):
    def __getitem__(self, key):
        if isinstance(key,int): return list(self.values())[key]
        return super().__getitem__(key)
    def __iter__(self): return iter(self.values())

class D1Cursor:
    def __init__(self, result):
        self.rows=[D1Row(r) for r in result.get('rows',[])]
        self.lastrowid=result.get('lastrowid')
        self.rowcount=result.get('changes',0)
        self.index=0
    def fetchone(self):
        if self.index>=len(self.rows): return None
        row=self.rows[self.index];self.index+=1;return row
    def fetchall(self):
        rows=self.rows[self.index:];self.index=len(self.rows);return rows
    def __iter__(self): return iter(self.fetchall())

class D1Connection:
    def __init__(self, url=None, key=None):
        self.url=(url or os.environ.get('D1_WORKER_URL','')).rstrip('/')
        self.key=key or os.environ.get('D1_API_KEY','')
        if not self.url or not self.key: raise RuntimeError('D1_WORKER_URL and D1_API_KEY are required; no local fallback')
        if not self.url.startswith(('https://','http://127.0.0.1:','http://localhost:')):
            raise RuntimeError('D1 bridge requires HTTPS (except local testing)')
        self.pending=[]
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        if exc_type is None: self.commit()
        else: self.pending.clear()
        return False
    def _post(self, path, payload):
        body=json.dumps(payload,ensure_ascii=False,default=str).encode()
        request=urllib.request.Request(self.url+path,body,headers={
            'Content-Type':'application/json', 'Accept':'application/json',
            'User-Agent':'Forma-Render-Bridge/1.0',
            'X-Forma-Bridge':self.key},method='POST')
        try:
            with urllib.request.urlopen(request,timeout=25) as response: result=json.load(response)
        except urllib.error.HTTPError as exc:
            raw=exc.read(32768)  # Never print response HTML or request headers.
            try: detail=json.loads(raw)
            except (ValueError,UnicodeDecodeError): detail={}
            if not isinstance(detail,dict): detail={}
            if exc.code==409 or detail.get('conflict'):
                raise sqlite3.IntegrityError('D1 rejected conflicting data') from exc
            if exc.code==403:
                if detail.get('error')=='Forbidden':
                    raise RemoteError('Worker refused the bridge secret (403): BRIDGE_TOKEN on THIS Worker is missing or differs from D1_API_KEY in Render. No secret values were logged') from exc
                if b'1010' in raw and b'cloudflare' in raw.lower():
                    raise RemoteError('Cloudflare error 1010 blocked the request before the Worker; check Browser Integrity Check / security events. No secret values were logged') from exc
                raise RemoteError('Cloudflare returned 403 before the Forma Worker: check Worker Access/WAF/security events and D1_WORKER_URL; no secret values were logged') from exc
            raise RemoteError('Cloudflare D1 request failed (HTTP %d)'%exc.code) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RemoteError('Cloudflare D1 connection failed; write outcome is unknown. Check data before retrying') from exc
        if not isinstance(result,dict) or 'results' not in result: raise RemoteError('Invalid response from D1 bridge')
        return result['results']
    def query(self, sql, params=()):
        """Execute a single statement now. Used for reads and inserts that need lastrowid."""
        self.commit()
        return D1Cursor(self._post('/v1/query',{'sql':sql,'params':list(params)})[0])
    def execute(self, sql, params=()):
        params=list(params)
        verb=sql.lstrip().split(None,1)[0].upper()
        if verb in ('SELECT','WITH','PRAGMA','EXPLAIN'):
            return self.query(sql,params)
        if re.match(r'\s*INSERT\s+INTO\s+(users|tasks|chat_messages)\s*\(',sql,re.IGNORECASE):
            return self.query(sql,params)
        if verb in ('BEGIN','COMMIT','ROLLBACK'): raise RemoteError('Use D1 batch instead of SQL transactions')
        self.pending.append({'sql':sql,'params':params})
        if len(self.pending)>=40: self.commit()
        return D1Cursor({'rows':[]})
    def executemany(self, sql, items):
        for params in items:self.execute(sql,params)
        self.commit()
    def executescript(self, script):
        self.commit()
        statements=[x.strip() for x in script.split(';') if x.strip()]
        for statement in statements:
            if statement.upper().startswith('PRAGMA JOURNAL_MODE'):continue
            # CREATE TABLE/INDEX are idempotent: initialize through D1 transactions.
            self.pending.append({'sql':statement,'params':[]})
            if len(self.pending)>=40:self.commit()
        self.commit()
    def commit(self):
        if not self.pending:return
        todo=self.pending;self.pending=[]
        try:
            for start in range(0,len(todo),40):
                self._post('/v1/batch',{'statements':todo[start:start+40]})
        except Exception:
            # A committed batch is not retried; caller receives an error.
            raise
    def rollback(self): self.pending.clear()

# Parents first for inserts, children first for deletes. Volatile login/presence tables
# are intentionally not copied; users log in again after migration or restore.
TABLES=('users','tasks','entries','cell_comments','attendance','daily_hours',
        'personal_hours','activity','chat_messages','chat_reads','chat_themes','chat_pins','vacation_schedule','sotipb_runs','sotipb_parts','user_avatars',
        'sessions','prank_presence','prank_events')
# Only temporary session/event tables and avatars are intentionally excluded from ZIP.
EXCLUDED_FROM_BACKUP=frozenset(('sessions','prank_presence','prank_events','user_avatars'))

def require_complete_schema(con):
    """Fail closed if a future data table is not part of the D1 backup/restore map."""
    present={row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    missing=set(TABLES)-present
    unknown=present-(set(TABLES)|{'restore_stage','backup_monitor'})
    if missing or unknown:
        raise RemoteError('Резервная копия остановлена: набор таблиц D1 отличается от версии кода '
                          '(нет: %s; новые: %s). Обновите модуль резервного копирования, данные не изменены' %
                          (', '.join(sorted(missing)) or '—',', '.join(sorted(unknown)) or '—'))

def sqlite_snapshot(remote):
    """Download a consistent-enough SQLite snapshot for an admin backup.

    The single-instance application's DB_LOCK protects concurrent web handlers.
    A second Render instance or external D1 writer must not be running during backup.
    """
    from pathlib import Path
    from backup_tools import BUSINESS, fingerprint
    if set(TABLES)-EXCLUDED_FROM_BACKUP != set(BUSINESS):
        raise RemoteError('Резервная копия остановлена: перечень сохраняемых таблиц не совпадает с составом архива')
    schema=(Path(__file__).parent/'cloudflare'/'schema.sql').read_text()
    remote.commit()
    require_complete_schema(remote)
    snap=sqlite3.connect(':memory:')
    try:
        snap.executescript(schema)
        require_complete_schema(snap)
        for table in TABLES:
            if table in EXCLUDED_FROM_BACKUP: continue
            columns=[row[1] for row in snap.execute('PRAGMA table_info("'+table+'")')]
            insert='INSERT INTO "'+table+'" ('+','.join('"'+c+'"' for c in columns)+') VALUES ('+','.join('?' for _ in columns)+')'
            offset=0
            while True:
                rows=remote.execute('SELECT * FROM "'+table+'" ORDER BY rowid LIMIT 100 OFFSET ?', (offset,)).fetchall()
                if not rows: break
                snap.executemany(insert, [tuple(row[c] for c in columns) for row in rows])
                offset+=len(rows)
        snap.commit()
        if fingerprint(remote)!=fingerprint(snap):
            raise RemoteError('Снимок D1 не совпал с данными сайта; неполный ZIP не выдан. Повторите позже')
        return snap
    except BaseException:
        snap.close()
        raise

def replace_atomic(remote, source):
    """Stage large restores in D1; one small final D1.batch swaps ALL business rows.

    The upload is resumable only by a new attempt; uncommitted chunks are temporary.
    No live business table changes until the final atomic D1.batch succeeds.
    """
    from backup_tools import validate
    validate(source)
    require_complete_schema(source)
    remote.commit()
    require_complete_schema(remote)
    transfer_id=secrets.token_hex(20)
    cutoff=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    remote.query('DELETE FROM restore_stage WHERE created_at<?',(cutoff,))
    staged=[]
    try:
        for table in TABLES:
            if table in EXCLUDED_FROM_BACKUP:continue
            cols=[r[1] for r in source.execute('PRAGMA table_info("'+table+'")')]
            projection=','.join('"'+c+'"' for c in cols)
            chunk=[];size=2;part=0
            def upload(rows,chunk_number):
                payload=json.dumps(rows,ensure_ascii=False,separators=(',',':'))
                remote.query('INSERT INTO restore_stage(transfer_id,table_name,chunk_no,payload) VALUES(?,?,?,?)',
                             (transfer_id,table,chunk_number,payload))
                staged.append((table,chunk_number,payload))
            for row in source.execute('SELECT '+projection+' FROM "'+table+'" ORDER BY rowid'):
                item=list(row)
                encoded=json.dumps(item,ensure_ascii=False,separators=(',',':'))
                width=len(encoded.encode('utf-8'))+1
                if width>95000:raise RemoteError('A single database row exceeds the staged restore chunk limit')
                if chunk and size+width>95000:
                    upload(chunk,part);part+=1;chunk=[];size=2
                chunk.append(item);size+=width
            if chunk:upload(chunk,part)
        # Confirm each uploaded piece before touching live tables. D1 bridge JSON
        # may reject or truncate an oversized upload, but cannot go unnoticed.
        for table,part,payload in staged:
            row=remote.execute('SELECT payload FROM restore_stage WHERE transfer_id=? AND table_name=? AND chunk_no=?',
                               (transfer_id,table,part)).fetchone()
            if not row or row[0]!=payload:raise RemoteError('Staged D1 data failed verification; live records were not changed')
        statements=[{'sql':'DELETE FROM "'+t+'"','params':[]} for t in reversed(TABLES)]
        for table in TABLES:
            if table in EXCLUDED_FROM_BACKUP:continue
            cols=[r[1] for r in source.execute('PRAGMA table_info("'+table+'")')]
            projection=','.join('"'+c+'"' for c in cols)
            extract=','.join("json_extract(j.value,'$["+str(i)+"]')" for i in range(len(cols)))
            sql=('INSERT INTO "'+table+'" ('+projection+') SELECT '+extract+
                 ' FROM restore_stage s, json_each(s.payload) j WHERE s.transfer_id=? AND s.table_name=?'+
                 ' ORDER BY s.chunk_no,CAST(j.key AS INTEGER)')
            statements.append({'sql':sql,'params':[transfer_id,table]})
        statements.append({'sql':'DELETE FROM restore_stage WHERE transfer_id=?','params':[transfer_id]})
        if len(statements)>40:raise RemoteError('Too many D1 statements for atomic restore')
        remote.commit()
        remote._post('/v1/batch',{'statements':statements})
    except Exception:
        # Do not retry a final batch after a network error: it may have committed.
        # Leftover stage data is private and expires on the next restore.
        raise
