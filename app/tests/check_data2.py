import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.execute('SELECT id, company, status, priority FROM proposals ORDER BY created_at DESC LIMIT 5')
for row in cursor.fetchall():
    print(f'ID: {row[0]}, Company: {row[1]}, Status: {row[2]}, Priority: {row[3]}')
conn.close()
