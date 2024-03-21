import sqlite3

def create_messages():
    try:
        con = sqlite3.connect('messages.db')
        cur = con.cursor()

        cur.execute('CREATE TABLE messages_text (name VARCHAR(255), text VARCHAR(255));')
        cur.execute("INSERT INTO messages_text VALUES('START', 'Стартовое сообщение')")
        cur.execute("INSERT INTO messages_text VALUES('MENU', 'Меню')")
        cur.execute("INSERT INTO messages_text VALUES('INFO', 'Тут информация')")

        con.commit()
        con.close()
    except:
        pass

def get_text(name):
    con = sqlite3.connect('messages.db')
    cur = con.cursor()

    cur.execute(f'SELECT text FROM messages_text WHERE name = "{name}"')
    text = cur.fetchone()

    con.close()

    return text[0]

def change_text(name, text):
    con = sqlite3.connect('messages.db')
    cur = con.cursor()

    cur.execute(f'UPDATE messages_text SET text = "{text}" WHERE name = "{name}"')

    con.commit()
    con.close()
