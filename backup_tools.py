"""Контрольные суммы, проверка и сравнение архивов Forma без изменения рабочей БД."""
import datetime as dt
import hashlib
import io
import json
import sqlite3
import zipfile

FORMAT = 'forma-sqlite-v1'
BUSINESS = ('users', 'tasks', 'entries', 'cell_comments', 'attendance',
            'daily_hours', 'personal_hours', 'activity', 'chat_messages', 'chat_reads', 'chat_themes')
# Reading messages does not create an hourly backup; new messages do.
CONTENT_TABLES = tuple(t for t in BUSINESS if t not in ('activity','chat_reads'))
# Old ZIPs had no chat tables; avatars are deliberately absent from EVERY ZIP.
REQUIRED = (set(BUSINESS) - {'chat_messages','chat_reads','chat_themes'}) | {'sessions', 'prank_presence', 'prank_events'}
CHAT_SCHEMA = '''CREATE TABLE IF NOT EXISTS chat_messages (
 id INTEGER PRIMARY KEY, sender_id INTEGER NOT NULL REFERENCES users(id),
 recipient_id INTEGER REFERENCES users(id), body TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 style_json TEXT NOT NULL DEFAULT '{}');
 CREATE INDEX IF NOT EXISTS idx_chat_recipient ON chat_messages(recipient_id,id);
 CREATE INDEX IF NOT EXISTS idx_chat_sender ON chat_messages(sender_id,id);
 CREATE TABLE IF NOT EXISTS chat_reads (
 user_id INTEGER NOT NULL REFERENCES users(id), room_key TEXT NOT NULL,
 last_read_id INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(user_id,room_key));
 CREATE TABLE IF NOT EXISTS chat_themes (
 room_key TEXT PRIMARY KEY, theme_json TEXT NOT NULL,
 updated_by INTEGER NOT NULL REFERENCES users(id),
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS user_avatars (
 user_id INTEGER PRIMARY KEY REFERENCES users(id), image_b64 TEXT NOT NULL DEFAULT '',
 mime TEXT NOT NULL DEFAULT '', image_url TEXT NOT NULL DEFAULT '', revision INTEGER NOT NULL DEFAULT 1);'''
MAX_ARCHIVE = 25 * 1024 * 1024
MAX_DATABASE = 100 * 1024 * 1024

class BackupError(Exception):
    pass

def summary(con):
    counts = {table: con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in BUSINESS}
    first, last = con.execute('SELECT MIN(work_date),MAX(work_date) FROM entries').fetchone()
    last_activity = con.execute('SELECT MAX(created_at) FROM activity').fetchone()[0]
    staff = con.execute('SELECT COUNT(*) FROM users WHERE is_staff=1').fetchone()[0]
    admins = con.execute('SELECT COUNT(*) FROM users WHERE active=1 AND role="admin"').fetchone()[0]
    return {'counts': counts, 'first_work_date': first, 'last_work_date': last,
            'last_activity': last_activity, 'staff': staff, 'active_admins': admins}

def fingerprint(con, tables=BUSINESS):
    """Canonical content fingerprint, independent of page layout and schema column order."""
    digest = hashlib.sha256()
    for table in tables:
        digest.update(table.encode())
        # Legacy SQLite may append is_staff after created_at; D1 starts with it.
        # Canonical column order keeps a fingerprint stable across both schemas.
        columns=sorted(row[1] for row in con.execute(f'PRAGMA table_info("{table}")'))
        projection=','.join('"'+column+'"' for column in columns)
        for row in con.execute(f'SELECT {projection} FROM "{table}" ORDER BY rowid'):
            # JSON numbers from JavaScript turn 1.0 into 1; canonicalize REALs.
            values=[int(x) if type(x) is float and x.is_integer() else x for x in row]
            digest.update(json.dumps(values, ensure_ascii=False, default=str,
                                     separators=(',', ':')).encode())
            digest.update(b'\n')
    return digest.hexdigest()

def validate(con):
    try:
        if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise BackupError('Файл базы данных повреждён')
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not REQUIRED.issubset(tables):
            raise BackupError('Архив не соответствует текущему формату Forma')
        if not {'chat_messages','chat_reads','chat_themes','user_avatars'}.issubset(tables):
            con.executescript(CHAT_SCHEMA)  # Старый архив: создать недостающие таблицы.
        if 'style_json' not in {row[1] for row in con.execute('PRAGMA table_info(chat_messages)')}:
            con.execute("ALTER TABLE chat_messages ADD COLUMN style_json TEXT NOT NULL DEFAULT '{}'")
        cols = {row[1] for row in con.execute('PRAGMA table_info(users)')}
        if not {'id','username','role','is_staff','password_hash'}.issubset(cols):
            raise BackupError('Архив не содержит сведения о сотрудниках и правах доступа')
        if con.execute('PRAGMA foreign_key_check').fetchone():
            raise BackupError('Нарушены связи между записями в архиве')
        if not con.execute('SELECT 1 FROM users WHERE role="admin" AND active=1 AND is_staff=0 LIMIT 1').fetchone():
            raise BackupError('В архиве нет активной основной учётной записи администратора')
        return summary(con)
    except sqlite3.DatabaseError as exc:
        raise BackupError('Некорректная или повреждённая база данных') from exc

def archive(con):
    """SQLite online backup; passwords/roles kept, live sessions and fleeting events removed."""
    with sqlite3.connect(':memory:') as snapshot:
        con.backup(snapshot)
        for table in ('sessions', 'prank_presence', 'prank_events', 'user_avatars'):
            snapshot.execute(f'DELETE FROM {table}')
        snapshot.commit()
        # DELETE clears rows but may leave their image bytes in SQLite free pages.
        # VACUUM compacts the file so even raw ZIP contents contain no avatar pixels.
        snapshot.execute('VACUUM')
        data = bytearray(snapshot.serialize())
        # sqlite3.backup из WAL оставляет в заголовке флаги WAL (2,2), хотя
        # сериализованная in-memory копия уже не содержит отдельного WAL-файла.
        data[18] = data[19] = 1
        data = bytes(data)
        manifest = {'format': FORMAT, 'created_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                    'db_sha256': hashlib.sha256(data).hexdigest(), 'summary': summary(snapshot)}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
        zipped.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False))
        zipped.writestr('database.sqlite3', data)
    return stream.getvalue(), manifest

def inspect(raw):
    if not raw or len(raw) > MAX_ARCHIVE: raise BackupError('Размер архива превышает 25 МБ')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
            if set(zipped.namelist()) != {'manifest.json', 'database.sqlite3'}:
                raise BackupError('Ожидается ZIP-архив резервной копии Forma')
            if zipped.getinfo('manifest.json').file_size > 65536 or zipped.getinfo('database.sqlite3').file_size > MAX_DATABASE:
                raise BackupError('Слишком большой архив')
            manifest = json.loads(zipped.read('manifest.json'))
            if not isinstance(manifest,dict) or manifest.get('format') != FORMAT:
                raise BackupError('Неизвестная версия архива')
            stamp=dt.datetime.fromisoformat(manifest['created_at'])
            if stamp.tzinfo is None or not 2020<=stamp.year<=dt.datetime.now(dt.timezone.utc).year+1:
                raise BackupError('Некорректная дата резервной копии')
            data = zipped.read('database.sqlite3')
        if not data.startswith(b'SQLite format 3\x00') or hashlib.sha256(data).hexdigest() != manifest.get('db_sha256'):
            raise BackupError('Контрольная сумма резервной копии не совпала')
        with sqlite3.connect(':memory:') as snapshot:
            snapshot.deserialize(data)
            details = validate(snapshot)
        return data, manifest, details
    except (zipfile.BadZipFile, zipfile.LargeZipFile, ValueError, TypeError, KeyError, sqlite3.DatabaseError) as exc:
        raise BackupError('Некорректный ZIP-архив резервной копии Forma') from exc

def compare(current, saved):
    return {key: {'now': current['counts'][key], 'backup': saved['counts'][key],
                  'difference': saved['counts'][key] - current['counts'][key]}
            for key in BUSINESS}
