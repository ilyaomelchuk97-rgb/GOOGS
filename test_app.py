"""Изолированные интеграционные проверки API. Запуск: python test_app.py"""
import os
import sqlite3
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
import requests
import app


def main():
    with tempfile.TemporaryDirectory() as tmp:
        app.DB=Path(tmp)/'test.sqlite3'
        app.BACKUP_DIR=Path(tmp)/'backups'
        with sqlite3.connect(Path(__file__).with_name('worktrack.sqlite3')) as source:
            with sqlite3.connect(app.DB) as target: source.backup(target)
        app.init_db()
        server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        root=f'http://127.0.0.1:{server.server_address[1]}'
        assert requests.get(root+'/health').json()['build']==app.BUILD_ID
        for asset in ('chat-flower.png','chat-branch.png','mingas-official-logo.webp'):
            image=requests.get(root+'/'+asset)
            assert image.status_code==200 and image.headers['Content-Type'].startswith('image/'),asset
        lines=Path(__file__).with_name('initial_credentials.txt').read_text().splitlines()
        # Рабочие пароли могли быть изменены; восстанавливаем тестовые только в копии БД.
        with app.connect() as db:
            for line in (lines[7],lines[8]):
                label,password=line.split(' / ')
                db.execute('UPDATE users SET password_hash=? WHERE username=?',
                           (app.hashed_password(password),label.split(': ')[1]))
        admin=requests.Session();employee=requests.Session();other=requests.Session()
        a=admin.post(root+'/api/login',json={'username':'admin','password':'admin'})
        assert a.status_code==200,a.text
        token=a.json()['session_token']
        original_backup=admin.get(root+'/api/backup/download')
        assert original_backup.status_code==200 and original_backup.content[:2]==b'PK'
        original_status=admin.get(root+'/api/backup/status').json()
        assert original_status['current']['counts']['entries']>=2203
        # Архивы, скачанные ДО появления чата, также должны восстанавливаться.
        import io,json,hashlib,zipfile
        old_data,old_manifest,_=app.backup_tools.inspect(original_backup.content)
        with sqlite3.connect(':memory:') as legacy:
            legacy.deserialize(old_data)
            legacy.execute('DROP TABLE chat_messages')
            legacy_data=bytearray(legacy.serialize())
            legacy_data[18]=legacy_data[19]=1
        legacy_data=bytes(legacy_data)
        old_manifest['db_sha256']=hashlib.sha256(legacy_data).hexdigest()
        archive_stream=io.BytesIO()
        with zipfile.ZipFile(archive_stream,'w',zipfile.ZIP_DEFLATED) as zipped:
            zipped.writestr('manifest.json',json.dumps(old_manifest,ensure_ascii=False))
            zipped.writestr('database.sqlite3',legacy_data)
        legacy_archive=archive_stream.getvalue()
        assert app.backup_tools.inspect(legacy_archive)[2]['counts']['chat_messages']==0
        # Регрессия превью: после входа браузер может не отправить стороннюю cookie.
        # Запрос с токеном должен открыть кабинет даже БЕЗ Cookie.
        guest=requests.Session()
        assert guest.get(root+'/api/bootstrap?month=2026-10').status_code==401
        preview=guest.get(root+'/api/bootstrap?month=2026-10',headers={'X-Forma-Session':token})
        assert preview.status_code==200,preview.text
        assert preview.json()['user']['role']=='admin'
        assert guest.get(root+'/api/report?month=2026-10',headers={'X-Forma-Session':token}).status_code==200
        # На случай если прокси убирает и нестандартные заголовки.
        assert guest.get(root+'/api/bootstrap?month=2026-10',params={'forma_ticket':token}).status_code==200
        def sign_in(session,line):
            label,passwd=line.split(' / ')
            username=label.split(': ')[1]
            res=session.post(root+'/api/login',json={'username':username,'password':passwd})
            assert res.status_code==200,res.text
            return res.json()['user']
        u=sign_in(employee,lines[7]);second=sign_in(other,lines[8])
        # Общий чат видят все, личный — только два участника; чужой диалог не выдаётся.
        assert guest.get(root+'/api/chat').status_code==401
        assert guest.post(root+'/api/chat',json={'recipient_id':None,'body':'Чужое'}).status_code==401
        assert employee.get(root+'/api/chat',params={'room':'general'}).json()['messages']==[]
        assert second['id'] in [p['id'] for p in employee.get(root+'/api/chat').json()['users']]
        text='<b>Привет</b> от коллеги'
        fancy={'bubble':'#112233','glow':True,'glow_color':'#ff0099',
               'border_effect':20,'flower':20,'branch':20,'logo':20}
        direct=employee.post(root+'/api/chat',json={'recipient_id':second['id'],'body':text,'style':fancy})
        assert direct.status_code==200,direct.text
        direct_id=direct.json()['id']
        pair=other.get(root+'/api/chat',params={'room':str(u['id'])}).json()['messages']
        assert len(pair)==1 and pair[0]['id']==direct_id and pair[0]['body']==text and pair[0]['style']==fancy
        assert employee.post(root+'/api/chat/theme',json={'room':str(second['id']),'style':fancy}).status_code==200
        assert other.get(root+'/api/chat',params={'room':str(u['id'])}).json()['theme']==fancy
        assert admin.get(root+'/api/chat',params={'room':'general'}).json()['theme']=={}
        assert employee.post(root+'/api/chat/theme',json={'room':'general','style':{'flower':7,'border_effect':9}}).status_code==200
        assert admin.get(root+'/api/chat').json()['theme']=={'flower':7,'border_effect':9}
        assert employee.post(root+'/api/chat/theme',json={'room':'general','style':{'flower':21}}).status_code==400
        assert employee.post(root+'/api/chat/theme',json={'room':'general','style':{'glow':'true'}}).status_code==400
        assert employee.post(root+'/api/chat/theme',json={'room':'999999','style':fancy}).status_code==400
        assert guest.post(root+'/api/chat/theme',json={'room':'general','style':fancy}).status_code==401
        assert employee.post(root+'/api/chat',json={'recipient_id':None,'body':'bad','style':{'bubble':'red; background:url(x)'}}).status_code==400
        outsider=admin.get(root+'/api/chat',params={'room':str(u['id'])}).json()
        assert outsider['messages']==[] and outsider['theme']=={}
        assert employee.get(root+'/api/chat',params={'room':str(second['id']),'after':str(direct_id)}).json()['messages']==[]
        assert employee.get(root+'/api/chat',params={'room':'not-an-id'}).status_code==400
        assert employee.get(root+'/api/chat',params={'room':str(u['id'])}).status_code==400
        assert employee.post(root+'/api/chat',json={'recipient_id':u['id'],'body':'сам себе'}).status_code==400
        assert employee.post(root+'/api/chat',json={'recipient_id':999999,'body':'ошибка'}).status_code==404
        assert employee.post(root+'/api/chat',json={'recipient_id':None,'body':'  '}).status_code==400
        assert employee.post(root+'/api/chat',json={'recipient_id':None,'body':'x'*2001}).status_code==400
        group=employee.post(root+'/api/chat',json={'recipient_id':None,'body':'Общее сообщение'})
        assert group.status_code==200,group.text
        for session in (employee,other,admin):
            messages=session.get(root+'/api/chat',params={'room':'general'}).json()['messages']
            assert [m['body'] for m in messages]==['Общее сообщение']
        assert employee.get(root+'/api/chat',params={'room':'general','after':str(group.json()['id'])}).json()['messages']==[]
        assert other.get(root+'/api/chat',params={'room':str(u['id']),'before':str(group.json()['id'])}).json()['messages'][0]['id']==direct_id
        assert other.get(root+'/api/chat',params={'room':str(u['id']),'before':'1','after':'0'}).status_code==400
        unread=other.get(root+'/api/chat/status').json()
        assert unread['direct']=={str(u['id']):1} and unread['general']==1 and unread['notices']==[]
        assert admin.get(root+'/api/chat/status').json()['direct']=={}
        assert admin.get(root+'/api/chat/status').json()['general']==1
        assert employee.get(root+'/api/chat/status').json()['general']==0
        new_for_other=other.get(root+'/api/chat/status',params={'after':str(direct_id-1)}).json()['notices']
        assert [n['id'] for n in new_for_other]==[direct_id,group.json()['id']]
        assert admin.get(root+'/api/chat/status',params={'after':str(direct_id-1)}).json()['notices'][0]['id']==group.json()['id']
        assert other.post(root+'/api/chat/read',json={'room':str(u['id'])}).status_code==200
        unread=other.get(root+'/api/chat/status').json()
        assert unread['direct']=={} and unread['general']==1
        assert other.post(root+'/api/chat/read',json={'room':'general'}).status_code==200
        assert other.get(root+'/api/chat/status').json()['general']==0
        assert other.post(root+'/api/chat/read',json={'room':'999999'}).status_code==400
        # Аватар виден другим, но его содержимое НИКОГДА не входит в ZIP.
        import base64
        small_png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO4Bai4AAAAASUVORK5CYII=')
        assert guest.get(root+f'/api/avatar/{u["id"]}').status_code==401
        saved=employee.post(root+'/api/avatar',json={'image_b64':base64.b64encode(small_png).decode()})
        assert saved.status_code==200,saved.text
        assert saved.json()['avatar_revision']==1 and saved.json()['avatar_stored']
        assert other.get(root+f'/api/avatar/{u["id"]}').content==small_png
        avatar_people=other.get(root+'/api/chat').json()['users']
        assert next(p for p in avatar_people if p['id']==u['id'])['avatar_revision']==1
        avatar_backup=admin.get(root+'/api/backup/download')
        snap_data=app.backup_tools.inspect(avatar_backup.content)[0]
        with sqlite3.connect(':memory:') as snap:
            snap.deserialize(snap_data)
            assert snap.execute('SELECT COUNT(*) FROM user_avatars').fetchone()[0]==0
        assert base64.b64encode(small_png) not in snap_data
        second_image=Path(__file__).with_name('web').joinpath('courier-cat.png').read_bytes()
        replaced=employee.post(root+'/api/avatar',json={'image_b64':base64.b64encode(second_image).decode()})
        assert replaced.status_code==200,replaced.text
        assert replaced.json()['avatar_revision']==2 and other.get(root+f'/api/avatar/{u["id"]}').content==second_image
        linked=employee.post(root+'/api/avatar',json={'url':'https://example.com/picture.jpg'})
        assert linked.status_code==200 and linked.json()['avatar_revision']==3
        assert other.get(root+f'/api/avatar/{u["id"]}').status_code==404
        assert next(p for p in other.get(root+'/api/chat').json()['users'] if p['id']==u['id'])['avatar_url']=='https://example.com/picture.jpg'
        assert employee.post(root+'/api/avatar',json={'url':'http://example.com/not-secure.jpg'}).status_code==400
        assert employee.post(root+'/api/avatar',json={'url':'https://example.com:badport/photo.jpg'}).status_code==400
        assert employee.post(root+'/api/avatar',json={'image_b64':base64.b64encode(b'<svg/>').decode()}).status_code==400
        removed=employee.post(root+'/api/avatar',json={'remove':True})
        assert removed.status_code==200 and removed.json()['avatar_revision']==4
        assert other.get(root+f'/api/avatar/{u["id"]}').status_code==404
        assert employee.post(root+'/api/avatar',json={'image_b64':base64.b64encode(small_png).decode()}).status_code==200
        chat_backup=admin.get(root+'/api/backup/download')
        assert chat_backup.status_code==200
        _db,_manifest,contents=app.backup_tools.inspect(chat_backup.content)
        assert contents['counts']['chat_messages']==2 and contents['counts']['chat_themes']==2
        with sqlite3.connect(':memory:') as themed_snapshot:
            themed_snapshot.deserialize(_db)
            assert themed_snapshot.execute('SELECT style_json FROM chat_messages WHERE id=?',(direct_id,)).fetchone()[0].startswith('{')
        # Приколы: только админ, только открытая вкладка, события не выдаются постороннему.
        assert guest.get(root+'/api/prank/poll').status_code==401
        assert guest.get(root+'/api/presence').status_code==401
        admin.get(root+'/api/prank/poll')
        assert employee.get(root+'/api/prank/online').status_code==403
        assert employee.post(root+'/api/prank/send',json={'user_id':u['id'],'kind':'people'}).status_code==403
        initial=employee.get(root+'/api/prank/poll').json()
        cursor=initial['last_id'];assert initial['events']==[]
        roster=employee.get(root+'/api/presence')
        assert roster.status_code==200,roster.text
        people=roster.json()['users']
        assert {p['id'] for p in people}=={a.json()['user']['id'],u['id']}
        assert all(set(p)=={'id','name','role'} for p in people)
        online=admin.get(root+'/api/prank/online').json()['user_ids']
        assert u['id'] in online and second['id'] not in online
        assert admin.post(root+'/api/prank/send',json={'user_id':second['id'],'kind':'people'}).status_code==409
        assert admin.post(root+'/api/prank/send',json={'user_id':u['id'],'kind':'speech','text':' '}).status_code==400
        assert admin.post(root+'/api/prank/send',json={'user_id':u['id'],'kind':'speech','text':'A'*401}).status_code==400
        assert admin.post(root+'/api/prank/send',json={'user_id':1,'kind':'people'}).status_code==404
        sent=admin.post(root+'/api/prank/send',json={'user_id':u['id'],'kind':'people'})
        assert sent.status_code==200,sent.text
        received=employee.get(root+'/api/prank/poll',params={'after':cursor}).json()
        assert len(received['events'])==1 and received['events'][0]['kind']=='people'
        assert other.get(root+'/api/prank/poll').json()['events']==[]
        assert {p['id'] for p in employee.get(root+'/api/presence').json()['users']}=={a.json()['user']['id'],u['id'],second['id']}
        text='<b>Привет! & тест</b>'
        sent=admin.post(root+'/api/prank/send',json={'user_id':u['id'],'kind':'speech','text':text})
        assert sent.status_code==200,sent.text
        received=employee.get(root+'/api/prank/poll',params={'after':received['last_id']}).json()
        assert len(received['events'])==1 and received['events'][0]['body']==text
        assert employee.get(root+'/api/prank/poll',params={'after':received['last_id']}).json()['events']==[]
        # Новые эффекты поверх старой D1/SQLite-схемы: без изменения CHECK(kind).
        for kind,message in (('cat','Кот несёт письмо!'),('achievement','Король пятницы'),('parade','')):
            assert employee.post(root+'/api/prank/send',json={'user_id':u['id'],'kind':kind,'text':message}).status_code==403
            sent=admin.post(root+'/api/prank/send',json={'user_id':u['id'],'kind':kind,'text':message})
            assert sent.status_code==200,(kind,sent.text)
            received=employee.get(root+'/api/prank/poll',params={'after':received['last_id']}).json()
            assert len(received['events'])==1,(kind,received)
            assert received['events'][0]['kind']==kind
            assert received['events'][0]['body']==message
            assert other.get(root+'/api/prank/poll').json()['events']==[]
        assert admin.post(root+'/api/prank/send',json={'user_id':u['id'],'kind':'cat','text':' '}).status_code==400
        assert admin.post(root+'/api/prank/send',json={'user_id':u['id'],'kind':'cat','text':'x'*141}).status_code==400
        assert admin.post(root+'/api/prank/send',json={'user_id':u['id'],'kind':'achievement','text':'x'*81}).status_code==400
        cat_asset=guest.get(root+'/courier-cat.png')
        assert cat_asset.status_code==200 and cat_asset.headers['Content-Type']=='image/png'
        assert cat_asset.content.startswith(b'\x89PNG\r\n\x1a\n')
        gait_asset=guest.get(root+'/courier-cat-walk.png')
        assert gait_asset.status_code==200 and gait_asset.headers['Content-Type']=='image/png'
        assert gait_asset.content.startswith(b'\x89PNG\r\n\x1a\n')
        import struct
        assert struct.unpack('>II',gait_asset.content[16:24])==(743*4,520)
        with app.connect() as db:
            db.execute('UPDATE prank_presence SET last_seen=? WHERE user_id=?',('2020-01-01T00:00:00+00:00',u['id']))
        assert u['id'] not in admin.get(root+'/api/prank/online').json()['user_ids']
        assert u['id'] not in {p['id'] for p in other.get(root+'/api/presence').json()['users']}
        assert admin.post(root+'/api/prank/send',json={'user_id':u['id'],'kind':'people'}).status_code==409
        month='2026-10'
        all_data=admin.get(root+'/api/bootstrap?month='+month).json()
        my_data=employee.get(root+'/api/bootstrap?month='+month).json()
        assert len(all_data['users'])==10 and len(all_data['tasks'])==23
        assert len(all_data['entries'])>len(my_data['entries'])
        assert all(e['user_id']==u['id'] for e in my_data['entries'])
        assert employee.get(root+'/api/report?month='+month).status_code==403
        assert employee.get(root+'/api/backup/status').status_code==403
        assert employee.get(root+'/api/backup/download').status_code==403
        assert employee.post(root+'/api/backup/inspect',data=original_backup.content,headers={'Content-Type':'application/octet-stream'}).status_code==403
        assert admin.post(root+'/api/backup/inspect',data=b'not a backup',headers={'Content-Type':'application/octet-stream'}).status_code==400
        assert employee.post(root+'/api/tasks',json={'title':'Forbidden','norm':0}).status_code==403
        assert employee.post(root+'/api/users',json={'name':'Forbidden'}).status_code==403
        friday='2026-10-09'
        assert app.scheduled_hours('2026-10-06')==8.25
        assert app.scheduled_hours(friday)==7
        assert app.scheduled_hours('2026-10-10')==0
        assert employee.post(root+'/api/hours',json={'date':friday,'hours':6}).status_code==403
        assert employee.post(root+'/api/attendance',json={'date':friday,'status':'absent','reason':'Тест'}).status_code==403
        assert employee.post(root+'/api/password',json={'old':'anything','new':'newPassword123'}).status_code==403
        assert admin.post(root+'/api/password',json={'old':'wrong','new':'newPassword123'}).status_code==400
        baseline=admin.get(root+'/api/report?month='+month).json()
        base_perf=next(p for p in baseline['productivity'] if p['user_id']==u['id'])
        assert base_perf['work_hours']>0
        global_result=admin.post(root+'/api/hours',json={'date':friday,'hours':6.5})
        assert global_result.status_code==200,global_result.text
        own_result=admin.post(root+'/api/hours',json={'date':friday,'hours':5,'user_id':u['id']})
        assert own_result.status_code==200,own_result.text
        assert admin.post(root+'/api/hours',json={'date':friday,'hours':25}).status_code==400
        state=employee.get(root+'/api/bootstrap?month=2026-10').json()
        assert state['daily_hours']==[{'day':friday,'hours':6.5}]
        assert state['personal_hours']==[{'user_id':u['id'],'day':friday,'hours':5}]
        report_hours=admin.get(root+'/api/report?month=2026-10').json()
        assert report_hours['daily_hours'][0]['hours']==6.5 and report_hours['personal_hours'][0]['hours']==5
        person=next(p for p in report_hours['productivity'] if p['user_id']==u['id'])
        assert person['work_hours']==round(base_perf['work_hours']-2,2)
        assert person['rounded_norm_hours']==base_perf['rounded_norm_hours']
        assert person['percent']==round(person['rounded_norm_hours']/person['work_hours']*100,2)
        import io,openpyxl
        export_hours=admin.get(root+'/api/export?month=2026-10')
        assert export_hours.status_code==200,export_hours.text[:200] if not export_hours.ok else ''
        book=openpyxl.load_workbook(io.BytesIO(export_hours.content),data_only=True)
        sheet=book['Табель 5-2']
        row=next(i for i in range(2,sheet.max_row+1) if sheet.cell(i,1).value==u['name'])
        assert sheet.cell(row,10).value==5, (sheet.cell(row,10).value,row)
        summary=book['Отчёт']
        export_users=sorted(report_hours['users'],key=lambda person:person['id'])
        assert book.sheetnames==['Отчёт','Табель 5-2','Записи','Комментарии']
        original=openpyxl.load_workbook(Path(__file__).with_name('source.xlsx'))['Отчёт']
        assert summary['A1'].value==original['A1'].value
        from openpyxl.utils import get_column_letter
        for c in range(1,26):
            key=get_column_letter(c)
            assert summary.column_dimensions[key].width==original.column_dimensions[key].width,(key,summary.column_dimensions[key].width,original.column_dimensions[key].width)
        for r in range(1,40):
            if original.row_dimensions[r].height is not None:
                assert summary.row_dimensions[r].height==original.row_dimensions[r].height,(r,summary.row_dimensions[r].height,original.row_dimensions[r].height)
        assert summary.freeze_panes=='C4'
        assert summary['A2'].value==original['A2'].value
        assert summary['B2'].value==original['B2'].value
        assert summary['C2'].value=='По количеству'
        assert summary['O2'].value=='По времени'
        assert summary['M3'].value=='Общее' and summary['N2'].value=='Норма времени'
        assert summary['Y2'].value=='Итого'
        assert summary['O1'].value=='Октябрь' and summary['Q1'].value==2026
        assert {str(m) for m in summary.merged_cells.ranges if m.min_row<=3} >= {
            'A1:N1','O1:P1','A2:A3','B2:B3','C2:L2','N2:N3','O2:X2','Y2:Y3'}
        assert [summary.cell(3,c).value for c in range(3,13)]==[p['name'] for p in export_users]
        assert [summary.cell(3,c).value for c in range(3,13)]==[original.cell(3,c).value for c in range(3,13)]
        assert [summary.cell(3,c).value for c in range(15,25)]==[p['name'] for p in export_users]
        record=next(x for x in report_hours['rows'] if x['user_id']==u['id'])
        task_row=next(i for i in range(4,summary.max_row) if summary.cell(i,1).value==record['title'])
        person_index=next(i for i,x in enumerate(export_users) if x['id']==u['id'])
        assert summary.cell(task_row,3+person_index).value==record['quantity']
        assert summary.cell(task_row,15+person_index).value==record['hours']
        for task in report_hours['tasks']:
            if not task['active'] and not any(x['task_id']==task['id'] for x in report_hours['rows']):continue
            line=next(i for i in range(4,summary.max_row) if summary.cell(i,1).value==task['title'])
            assert summary.cell(line,2).value==task['unit']
            assert summary.cell(line,14).value==task['norm']
            for index,p in enumerate(export_users):
                match=next((x for x in report_hours['rows'] if x['task_id']==task['id'] and x['user_id']==p['id']),None)
                assert summary.cell(line,3+index).value==(match['quantity'] if match else None)
                assert summary.cell(line,15+index).value==(match['hours'] if match else None)
            assert summary.cell(line,13).value==round(sum(x['quantity'] for x in report_hours['rows'] if x['task_id']==task['id']),3)
            assert summary.cell(line,25).value==round(sum(x['hours'] for x in report_hours['rows'] if x['task_id']==task['id']),3)
        total_row=next(i for i in range(4,summary.max_row) if summary.cell(i,1).value=='Общее')
        assert total_row==27 and summary.cell(total_row+1,1).value=='Производительность'
        assert summary.cell(total_row,13).value==sum(x['quantity'] for x in report_hours['rows'])
        assert summary.cell(total_row,25).value==int(report_hours['productivity_total']['norm_hours']+0.5)
        assert summary.cell(total_row+1,15+person_index).value==person['percent']/100
        assert summary.cell(total_row+1,15+person_index).number_format=='0.00%'
        assert summary.cell(30+person_index,4).value==person['work_hours']
        assert summary.cell(50,2).value=='Май' and summary.cell(50,31).value=='Сентябрь'
        assert summary.cell(50,55).value=='Всё'
        assert summary.cell(51+person_index,30).value==u['name']
        assert summary.cell(51+person_index,33).value is not None  # сентябрьские часы по данным сайта
        assert summary.cell(51+person_index,45).value is None  # ноябрь ещё не наступил
        assert admin.post(root+'/api/hours',json={'date':friday,'user_id':u['id'],'hours':None}).status_code==200
        assert not employee.get(root+'/api/bootstrap?month=2026-10').json()['personal_hours']
        assert admin.post(root+'/api/hours',json={'date':friday,'hours':None}).status_code==200
        assert not employee.get(root+'/api/bootstrap?month=2026-10').json()['daily_hours']
        task=admin.post(root+'/api/tasks',json={'title':'Тестовая новая работа','unit':'шт.','norm':0.5,'category':'Другое'})
        assert task.status_code==200,task.text
        tid=task.json()['id']
        assert any(t['id']==tid for t in employee.get(root+'/api/bootstrap?month='+month).json()['tasks'])
        work_date='2026-10-06'
        note_payload={'task_id':tid,'date':work_date,'comment':'Комментарий без количества'}
        comment_only=employee.post(root+'/api/comments',json=note_payload)
        assert comment_only.status_code==200,comment_only.text
        assert other.post(root+'/api/comments',json={**note_payload,'user_id':u['id']}).status_code==403
        assert any(c['task_id']==tid and c['body']=='Комментарий без количества' for c in employee.get(root+'/api/bootstrap?month='+month).json()['comments'])
        assert not any(c['user_id']==u['id'] and c['task_id']==tid for c in other.get(root+'/api/bootstrap?month='+month).json()['comments'])
        assert not any(r['task_id']==tid for r in admin.get(root+'/api/report?month='+month).json()['rows'])
        note_book=openpyxl.load_workbook(io.BytesIO(admin.get(root+'/api/export?month='+month).content),data_only=True)
        assert any(row[3]=='Комментарий без количества' for row in note_book['Комментарии'].values)
        posted=employee.post(root+'/api/entries',json={'task_id':tid,'date':work_date,'quantity':5,'note':'Тест'})
        assert posted.status_code==200,posted.text
        e=[e for e in employee.get(root+'/api/bootstrap?month='+month).json()['entries'] if e['task_id']==tid][0]
        assert e['quantity']==5
        assert other.patch(root+'/api/entries/'+str(e['id']),json={'task_id':tid,'date':work_date,'quantity':7}).status_code==403
        updated=employee.patch(root+'/api/entries/'+str(e['id']),json={'task_id':tid,'date':work_date,'quantity':7,'note':'Исправлено'})
        assert updated.status_code==200,updated.text
        after_edit=employee.get(root+'/api/bootstrap?month='+month).json()
        assert [e for e in after_edit['entries'] if e['task_id']==tid][0]['quantity']==7
        assert any(c['task_id']==tid and c['body']=='Исправлено' for c in after_edit['comments'])
        wrong=employee.patch(root+'/api/entries/'+str(e['id']),json={'task_id':tid,'date':'2027-01-01','quantity':9})
        assert wrong.status_code==400
        assert employee.post(root+'/api/attendance',json={'date':work_date,'status':'absent','reason':'Больничный'}).status_code==403
        absent=admin.post(root+'/api/attendance',json={'user_id':u['id'],'date':work_date,'status':'absent','reason':'Больничный'})
        assert absent.status_code==200,absent.text
        assert other.post(root+'/api/attendance',json={'user_id':u['id'],'date':work_date,'status':'present'}).status_code==403
        att=[a for a in admin.get(root+'/api/bootstrap?month='+month).json()['attendance'] if a['user_id']==u['id']]
        assert len(att)==1 and att[0]['reason']=='Больничный'
        assert admin.post(root+'/api/hours',json={'date':work_date,'user_id':u['id'],'hours':10}).status_code==200
        assert admin.post(root+'/api/hours',json={'date':work_date,'hours':9}).status_code==200
        absent_book=openpyxl.load_workbook(io.BytesIO(admin.get(root+'/api/export?month='+month).content),data_only=True)
        absent_sheet=absent_book['Табель 5-2']
        row=next(i for i in range(2,absent_sheet.max_row+1) if absent_sheet.cell(i,1).value==u['name'])
        assert absent_sheet.cell(row,7).value==0  # отсутствует: даже ручные часы не засчитываются
        report=admin.get(root+'/api/report?month='+month)
        assert report.status_code==200 and any(r['task_id']==tid and r['quantity']==7 and r['hours']==3.5 for r in report.json()['rows'])
        exported=admin.get(root+'/api/export?month='+month)
        assert exported.status_code==200 and exported.content[:2]==b'PK'
        logs=admin.get(root+'/api/logs').json()['logs']
        assert any(x['action']=='attendance' for x in logs)
        assert employee.delete(root+'/api/entries/'+str(e['id'])).status_code==200
        after_delete=employee.get(root+'/api/bootstrap?month='+month).json()
        assert not any(x['task_id']==tid for x in after_delete['entries'])
        assert any(c['task_id']==tid and c['body']=='Исправлено' for c in after_delete['comments'])
        assert employee.post(root+'/api/comments',json={**note_payload,'comment':''}).status_code==200
        assert not any(c['task_id']==tid for c in employee.get(root+'/api/bootstrap?month='+month).json()['comments'])
        # Повышение не должно удалять исторические работы сотрудника из отчёта.
        before_report=admin.get(root+'/api/report?month='+month).json()
        before_users=before_report['users']
        assert admin.patch(root+f'/api/users/{u["id"]}',json={'role':'owner'}).status_code==400
        promoted=admin.patch(root+f'/api/users/{u["id"]}',json={'role':'admin'})
        assert promoted.status_code==200,promoted.text
        assert employee.get(root+'/api/report?month='+month).status_code==200
        with app.connect() as db:
            assert db.execute('SELECT role,is_staff FROM users WHERE id=?',(u['id'],)).fetchone()['is_staff']==1
            assert db.execute("SELECT is_staff FROM users WHERE username='admin'").fetchone()['is_staff']==0
        promoted_report=admin.get(root+'/api/report?month='+month).json()
        assert u['id'] not in [p['id'] for p in promoted_report['users']]
        assert u['id'] not in [x['user_id'] for x in promoted_report['rows']]
        assert u['id'] not in [p['user_id'] for p in promoted_report['productivity']]
        assert u['id'] not in [a['user_id'] for a in promoted_report['attendance']]
        assert len(before_users)==len(promoted_report['users'])+1
        old_quantity=sum(x['quantity'] for x in before_report['rows'])
        promoted_quantity=sum(x['quantity'] for x in promoted_report['rows'])
        old_person_quantity=sum(x['quantity'] for x in before_report['rows'] if x['user_id']==u['id'])
        assert round(old_quantity-promoted_quantity,3)==round(old_person_quantity,3)
        old_person_hours=next(p['work_hours'] for p in before_report['productivity'] if p['user_id']==u['id'])
        assert round(before_report['productivity_total']['work_hours']-promoted_report['productivity_total']['work_hours'],2)==old_person_hours
        assert any(p['id']==u['id'] and p['role']=='admin' and p['is_staff']==1
                   for p in admin.get(root+'/api/bootstrap?month='+month).json()['users'])
        after_promotion=openpyxl.load_workbook(io.BytesIO(admin.get(root+'/api/export?month='+month).content),data_only=True)
        assert all(u['name']!=cell.value for row in after_promotion['Отчёт'].iter_rows() for cell in row)
        assert all(u['name']!=row[0] for row in list(after_promotion['Табель 5-2'].values)[1:])
        assert all(u['name']!=row[1] for row in list(after_promotion['Записи'].values)[1:])
        assert all(u['name']!=row[1] for row in list(after_promotion['Комментарии'].values)[1:])
        # Уже повышенный работник в старой версии мог быть помечен нештатным:
        # при следующем запуске возвращаем его в графики, не трогая работы.
        with app.connect() as db:
            preserved=db.execute('SELECT COUNT(*) FROM entries WHERE user_id=?',(u['id'],)).fetchone()[0]
            db.execute('UPDATE users SET is_staff=0 WHERE id=?',(u['id'],))
        assert u['id'] not in [p['id'] for p in admin.get(root+'/api/report?month='+month).json()['users']]
        app.init_db()
        with app.connect() as db:
            assert db.execute('SELECT is_staff FROM users WHERE id=?',(u['id'],)).fetchone()[0]==1
            assert db.execute('SELECT COUNT(*) FROM entries WHERE user_id=?',(u['id'],)).fetchone()[0]==preserved
            assert db.execute("SELECT is_staff FROM users WHERE username='admin'").fetchone()[0]==0
        # is_staff восстановлен, поэтому другие разделы по-прежнему видят человека,
        # но роль admin запрещает возвращать его в отчёт и выбор личных листов.
        assert u['id'] not in [p['id'] for p in admin.get(root+'/api/report?month='+month).json()['users']]
        assert any(p['id']==u['id'] for p in admin.get(root+'/api/bootstrap?month='+month).json()['users'])
        assert employee.post(root+'/api/hours',json={'date':friday,'hours':6}).status_code==200
        assert employee.patch(root+f'/api/users/{u["id"]}',json={'role':'employee'}).status_code==400
        demoted=admin.patch(root+f'/api/users/{u["id"]}',json={'role':'employee'})
        assert demoted.status_code==200,demoted.text
        restored_report=admin.get(root+'/api/report?month='+month).json()
        assert u['id'] in [p['id'] for p in restored_report['users']]
        assert any(x['user_id']==u['id'] for x in restored_report['rows'])
        assert employee.get(root+'/api/report?month='+month).status_code==401
        u=sign_in(employee,lines[7]);assert employee.get(root+'/api/report?month='+month).status_code==403
        headers={'Content-Type':'application/octet-stream'}
        inspect=admin.post(root+'/api/backup/inspect',data=original_backup.content,headers=headers)
        assert inspect.status_code==200,inspect.text
        preview=inspect.json()
        assert preview['backup']['counts']['tasks']==23
        assert preview['comparison']['tasks']['difference']==-1
        assert preview['backup']['first_work_date'] and preview['created_at']
        params={k:preview[k] for k in ('archive_hash','current_signature')}
        url=root+'/api/backup/restore'
        assert admin.post(url,params=params,data=original_backup.content,headers=headers).status_code==400
        assert admin.post(root+'/api/hours',json={'date':friday,'hours':8}).status_code==200
        assert admin.post(url,params=params,data=original_backup.content,
                          headers={**headers,'X-Forma-Confirm':'RESTORE'}).status_code==409
        preview=admin.post(root+'/api/backup/inspect',data=original_backup.content,headers=headers).json()
        restored=admin.post(url,params={k:preview[k] for k in ('archive_hash','current_signature')},
                            data=original_backup.content,headers={**headers,'X-Forma-Confirm':'RESTORE'})
        assert restored.status_code==200,restored.text
        assert admin.get(root+'/api/backup/status').status_code==401  # сеансы сброшены
        assert employee.get(root+'/api/bootstrap?month='+month).status_code==401
        assert admin.post(root+'/api/login',json={'username':'admin','password':'admin'}).status_code==200
        final=admin.get(root+'/api/backup/status').json()
        assert final['current']['counts']['tasks']==23
        assert final['current']['counts']['entries']==original_status['current']['counts']['entries']
        assert len(final['safety'])==1
        safety=admin.get(root+'/api/backup/safety',params={'name':final['safety'][0]['name']})
        assert safety.status_code==200 and safety.content[:2]==b'PK'
        assert app.backup_tools.inspect(safety.content)[2]['counts']['chat_messages']==2
        assert final['current']['counts']['chat_messages']==0
        assert admin.get(root+f'/api/avatar/{u["id"]}').status_code==404
        # Логин сотрудника меняется администратором без потери его работ и ролей.
        u=sign_in(employee,lines[7])
        before=employee.get(root+'/api/bootstrap?month='+month).json()
        assert employee.patch(root+f'/api/users/{u["id"]}',json={'username':'not_allowed'}).status_code==403
        assert admin.patch(root+f'/api/users/{u["id"]}',json={'username':'x'}).status_code==400
        assert admin.patch(root+f'/api/users/{u["id"]}',json={'username':'ADMIN'}).status_code==409
        assert admin.patch(root+f'/api/users/{u["id"]}',json={'username':'GOROH'}).status_code==409
        changed=admin.patch(root+f'/api/users/{u["id"]}',json={'username':'Gorodinskiy_New'})
        assert changed.status_code==200,changed.text
        assert employee.get(root+'/api/bootstrap?month='+month).status_code==401
        old_password=lines[7].split(' / ')[1]
        assert employee.post(root+'/api/login',json={'username':'gorodinskiy','password':old_password}).status_code==401
        relogin=employee.post(root+'/api/login',json={'username':'gorodinskiy_new','password':old_password})
        assert relogin.status_code==200,relogin.text
        assert relogin.json()['user']['id']==u['id'] and relogin.json()['user']['role']=='employee'
        after=employee.get(root+'/api/bootstrap?month='+month).json()
        assert len(before['entries'])==len(after['entries']) and before['attendance']==after['attendance']
        assert admin.patch(root+f'/api/users/{u["id"]}',json={'username':'Gorodinskiy_New'}).status_code==200
        assert employee.get(root+'/api/bootstrap?month='+month).status_code==200
        with app.connect() as db:
            for i in range(105):
                db.execute('INSERT INTO chat_messages(sender_id,recipient_id,body) VALUES(?,?,?)',
                           (u['id'],None,f'История {i}'))
        recent=admin.get(root+'/api/chat',params={'room':'general'}).json()
        assert len(recent['messages'])==100 and recent['has_more'] is True
        assert admin.get(root+'/api/chat/status').json()['general']==105
        assert admin.post(root+'/api/chat/read',json={'room':'general','up_to':recent['messages'][-2]['id']}).status_code==200
        assert admin.get(root+'/api/chat/status').json()['general']==1  # новое после показанного не теряется
        assert admin.post(root+'/api/chat/read',json={'room':'general','up_to':99999999}).status_code==400
        earlier=admin.get(root+'/api/chat',params={'room':'general','before':str(recent['messages'][0]['id'])}).json()
        assert len(earlier['messages'])==5 and earlier['has_more'] is False
        legacy_check=admin.post(root+'/api/backup/inspect',data=legacy_archive,headers={'Content-Type':'application/octet-stream'})
        assert legacy_check.status_code==200,legacy_check.text
        check=legacy_check.json()
        restored_old=admin.post(root+'/api/backup/restore',params={k:check[k] for k in ('archive_hash','current_signature')},
                                data=legacy_archive,headers={'Content-Type':'application/octet-stream','X-Forma-Confirm':'RESTORE'})
        assert restored_old.status_code==200,restored_old.text
        with app.connect() as db:
            assert db.execute('SELECT COUNT(*) FROM chat_messages').fetchone()[0]==0
        server.shutdown()
    print('OK: роли, работы, табель, Excel, личный/общий чат, пагинация и резервные копии')

if __name__=='__main__':main()
