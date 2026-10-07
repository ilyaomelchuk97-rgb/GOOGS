#!/usr/bin/env python3
"""One-time, guarded transfer of a Forma SQLite backup ZIP into an EMPTY D1.

Requires DATABASE_BACKEND=d1, D1_WORKER_URL, D1_API_KEY, and --archive.
Never run while another copy of the site or an external D1 writer is active.
"""
import argparse
import os
import sqlite3
from pathlib import Path

import backup_tools
import d1_store


def main():
    parser=argparse.ArgumentParser(description='Перенос данных Forma из ZIP-копии в пустую Cloudflare D1')
    parser.add_argument('--archive',required=True, type=Path,help='Локальная ZIP-копия, не добавляйте её в GitHub')
    parser.add_argument('--apply', action='store_true', help='Действительно записать данные; без флага только проверить')
    args=parser.parse_args()
    if os.environ.get('DATABASE_BACKEND')!='d1': parser.error('Для переноса укажите DATABASE_BACKEND=d1')
    raw=args.archive.read_bytes()
    data,manifest,details=backup_tools.inspect(raw)
    print('Проверенная резервная копия:',manifest['created_at'])
    print('Сотрудники:',details['counts']['users'],'Записи:',details['counts']['entries'])
    print('Период:',details['first_work_date'],'—',details['last_work_date'])
    with d1_store.D1Connection() as remote:
        # Tables must already exist: apply cloudflare/schema.sql first.
        nonempty={table:remote.execute('SELECT COUNT(*) FROM "'+table+'"').fetchone()[0]
                  for table in d1_store.TABLES}
        if any(nonempty.values()):
            parser.error('ОТКАЗ: D1 не пуста. Ничего не заменено: '+str(nonempty))
        if not args.apply:
            print('D1 пуста. Пробный запуск завершён; для переноса добавьте --apply.')
            return
        with sqlite3.connect(':memory:') as source:
            source.deserialize(data)
            backup_tools.validate(source)  # Старый архив может не содержать таблицу чата.
            d1_store.replace_atomic(remote,source)
            match=backup_tools.fingerprint(source)==backup_tools.fingerprint(remote)
        counts=backup_tools.summary(remote)['counts']
        print('D1:',counts)
        if not match or counts!=details['counts']:
            raise RuntimeError('Проверка переноса НЕ ПРОШЛА — не запускайте сайт, проверьте данные и сохраните архив')
        print('Перенос завершён: количество строк и контрольная сумма бизнес-данных совпадают.')
        print('Архив оставьте у себя в безопасном месте; не отправляйте в репозиторий.')

if __name__=='__main__':main()
