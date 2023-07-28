import sqlite3


connect = sqlite3.connect('users.db')
cursor = connect.cursor()

cursor.execute('''
CREATE TABLE users (
    info text,
    user_id integer
)
''')
connect.commit()

connect.close()
