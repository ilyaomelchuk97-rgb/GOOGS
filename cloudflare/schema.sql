-- Production schema for Cloudflare D1; apply once before importing data.
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
        CREATE TABLE IF NOT EXISTS chat_messages (
          id INTEGER PRIMARY KEY, sender_id INTEGER NOT NULL REFERENCES users(id),
          recipient_id INTEGER REFERENCES users(id), body TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_chat_recipient ON chat_messages(recipient_id,id);
        CREATE INDEX IF NOT EXISTS idx_chat_sender ON chat_messages(sender_id,id);
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
