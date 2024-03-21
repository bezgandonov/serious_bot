import sqlite3

default_db_name = 'tg_bot_info.db'
default_table_name_1 = 'tg_admins'
default_table_name_2 = 'templates'

def create_tables(db_name=default_db_name, table_name_1=default_table_name_1, table_name_2=default_table_name_2):
    con = sqlite3.connect(db_name)
    cur = con.cursor()

    command = f'CREATE TABLE IF NOT EXISTS {table_name_1} (user_id INT);'
    cur.execute(command)

    command = f'''CREATE TABLE IF NOT EXISTS {table_name_2} (
                  id INT,
                  name VARCHAR(255),
                  price INT,
                  desc VARCHAR(255),
                  image_path VARCHAR(255),
                  file_path VARCHAR(255)
                  );'''
    cur.execute(command)

    con.commit()
    con.close()


def is_admin_check(user_id=0, db_name=default_db_name, table_name=default_table_name_1):
    con = sqlite3.connect(db_name)
    cur = con.cursor()

    command = f'SELECT user_id FROM {table_name} WHERE user_id={user_id};'
    cur.execute(command)
    admin = cur.fetchone()

    con.close()

    if admin:
        return True
    else:
        return False


def add_admin(user_id=0, db_name=default_db_name, table_name=default_table_name_1):
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()

        if is_admin_check(user_id, db_name, table_name):
            return f'User {user_id} is already an admin.'

        command = f'INSERT INTO {table_name} (user_id) VALUES ({user_id});'
        cur.execute(command)

        con.commit()
        con.close()

        return f'Пользователь {user_id} был добавлен как администратор'
    except sqlite3.Error as e:
        return f'Произошла ошибка при создании администратора: {e}'


def add_template(name, price, desc, db_name=default_db_name, table_name=default_table_name_2):
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()

        command = f'SELECT COALESCE(MAX(id), 0) FROM {table_name};'
        cur.execute(command)
        next_item_id = cur.fetchone()[0] + 1
        

        command = f'''INSERT INTO {table_name} VALUES(
                      {next_item_id},
                      '{name}',
                      {price},
                      '{desc}',
                      'images/{next_item_id}.jpg',
                      'files/{next_item_id}.docx');'''
        cur.execute(command)

        con.commit()
        con.close()

        return True, None, next_item_id
    except sqlite3.Error as e:
        return False, e, None


def delete_template(template_id,  db_name=default_db_name, table_name=default_table_name_2):
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()

        command = f'DELETE FROM {table_name} WHERE id = {template_id}'
        cur.execute(command)

        con.commit()
        con.close()
        return True, None
    except sqlite3.Error as e:
        return False, e


def edit_template(item, item_id, changed_item, db_name=default_db_name, table_name=default_table_name_2):
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()

        command = f'UPDATE {table_name} SET "{item}" = "{changed_item}" WHERE id = "{item_id}"'
        cur.execute(command)
        
        con.commit()
        con.close()
        return True, None
    except sqlite3.Error as e:
        return False, e


def get_basic_templates(db_name=default_db_name, table_name=default_table_name_2):
    con = sqlite3.connect(db_name)
    cur = con.cursor()

    command = f'SELECT id, name, price, desc FROM {table_name}'
    cur.execute(command)
    all_templates = cur.fetchall()

    con.close()
    return all_templates


def get_template_cards(template_id, db_name=default_db_name, table_name=default_table_name_2):
    con = sqlite3.connect(db_name)
    cur = con.cursor()

    command = f'SELECT name, price, desc, image_path, file_path FROM {table_name} WHERE id = {template_id}'
    cur.execute(command)
    all_templates = cur.fetchall()

    con.close()
    return all_templates


if __name__ == '__main__':
    create_tables()
