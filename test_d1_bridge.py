"""Run the production D1 transport against an isolated local SQLite Worker emulator."""
import base64
import json
import os
import sqlite3
import tempfile
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import requests
import app

class Worker(BaseHTTPRequestHandler):
    db=None
    lock=threading.Lock()
    def log_message(self,*args):pass
    def do_POST(self):
        if self.headers.get('X-Forma-Bridge')!='test-only-key':
            self.send_error(403);return
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        queries=[body] if self.path=='/v1/query' else body['statements']
        try:
            with self.lock:
                self.db.execute('BEGIN')
                results=[]
                for q in queries:
                    cursor=self.db.execute(q['sql'],q['params'])
                    rows=[dict(row) for row in cursor.fetchall()] if cursor.description else []
                    results.append({'rows':rows,'lastrowid':cursor.lastrowid,'changes':max(cursor.rowcount,0)})
                self.db.commit()
            raw=json.dumps({'results':results}).encode();code=200
        except Exception as error:
            self.db.rollback();raw=json.dumps({'error':str(error)}).encode();code=400
        self.send_response(code);self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)

def main():
    with tempfile.TemporaryDirectory() as tmp:
        Worker.db=sqlite3.connect(str(Path(tmp)/'remote.sqlite3'),check_same_thread=False,isolation_level=None)
        Worker.db.row_factory=sqlite3.Row
        Worker.db.execute('PRAGMA foreign_keys=ON')
        worker=ThreadingHTTPServer(('127.0.0.1',0),Worker)
        threading.Thread(target=worker.serve_forever,daemon=True).start()
        os.environ.update(DATABASE_BACKEND='d1',D1_WORKER_URL=f'http://127.0.0.1:{worker.server_address[1]}',D1_API_KEY='test-only-key')
        app.BACKUP_DIR=Path(tmp)/'backups'
        app.init_db()
        with app.connect() as db:
            admin=db.execute('INSERT INTO users(name,username,password_hash,role,is_staff) VALUES(?,?,?,?,?)',
                ('Администратор','admin',app.hashed_password('admin'),'admin',0)).lastrowid
            person=db.execute('INSERT INTO users(name,username,password_hash,role) VALUES(?,?,?,?)',
                ('Тестовый человек','tester',app.hashed_password('testerpass'),'employee')).lastrowid
            assert admin and person
        server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        root=f'http://127.0.0.1:{server.server_address[1]}'
        a=requests.Session();b=requests.Session()
        assert a.post(root+'/api/login',json={'username':'admin','password':'admin'}).status_code==200
        assert b.post(root+'/api/login',json={'username':'tester','password':'testerpass'}).status_code==200
        style={'bubble':'#173a53','glow':True,'glow_color':'#fea891',
               'border_effect':18,'flower':13,'branch':16,'logo':20}
        dm=a.post(root+'/api/chat',json={'recipient_id':person,'body':'лично','style':style})
        assert b.post(root+'/api/chat/theme',json={'room':str(admin),'style':style}).status_code==200
        assert a.get(root+'/api/chat',params={'room':str(person)}).json()['theme']==style
        assert b.get(root+'/api/chat',params={'room':str(admin)}).json()['messages'][0]['style']==style
        group=a.post(root+'/api/chat',json={'recipient_id':None,'body':'общий'})
        assert dm.status_code==group.status_code==200,(dm.text,group.text)
        status=b.get(root+'/api/chat/status').json()
        assert status['direct']=={str(admin):1} and status['general']==1,status
        assert b.post(root+'/api/chat/read',json={'room':str(admin)}).status_code==200
        assert b.get(root+'/api/chat/status').json()['direct']=={}
        tiny=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO4Bai4AAAAASUVORK5CYII=')
        avatar=b.post(root+'/api/avatar',json={'image_b64':base64.b64encode(tiny).decode()})
        assert avatar.status_code==200,avatar.text
        assert a.get(root+f'/api/avatar/{person}').content==tiny
        backup=a.get(root+'/api/backup/download')
        assert backup.status_code==200,backup.text[:200]
        contents=app.backup_tools.inspect(backup.content)
        with sqlite3.connect(':memory:') as snap:
            snap.deserialize(contents[0]);assert snap.execute('SELECT COUNT(*) FROM user_avatars').fetchone()[0]==0
            assert snap.execute('SELECT COUNT(*) FROM chat_reads').fetchone()[0]==1
            assert snap.execute('SELECT COUNT(*) FROM chat_themes').fetchone()[0]==1
            assert json.loads(snap.execute('SELECT style_json FROM chat_messages WHERE id=?',(dm.json()['id'],)).fetchone()[0])==style
        assert b.post(root+'/api/avatar',json={'url':'https://example.com/profile.jpg'}).status_code==200
        preview=a.post(root+'/api/backup/inspect',data=backup.content,headers={'Content-Type':'application/octet-stream'})
        assert preview.status_code==200,preview.text
        confirm=a.post(root+'/api/backup/restore',params={k:preview.json()[k] for k in ('archive_hash','current_signature')},
            data=backup.content,headers={'Content-Type':'application/octet-stream','X-Forma-Confirm':'RESTORE'})
        assert confirm.status_code==200,confirm.text
        assert not Worker.db.execute('SELECT COUNT(*) FROM user_avatars').fetchone()[0]
        assert Worker.db.execute('SELECT COUNT(*) FROM chat_reads').fetchone()[0]==1
        assert Worker.db.execute('SELECT COUNT(*) FROM chat_themes').fetchone()[0]==1
        server.shutdown();worker.shutdown();Worker.db.close()
        print('OK: D1-мост, непрочитанные, аватар, ZIP без изображения, восстановление')

if __name__=='__main__':main()
