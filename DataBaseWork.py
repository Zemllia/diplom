import sqlite3

import utils


def register_user(username, password):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users(username, password, user_token)"
                   " VALUES('{}', '{}', '{}')".format(username, password, utils.generate_token()))
    conn.commit()
    conn.close()


def login_user(username, password):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_token FROM users WHERE username = '{}' AND password = '{}'".format(username, password))
    token = cursor.fetchone()
    conn.commit()
    conn.close()
    return token


def check_if_user_exists(username):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = '{}'".format(username))
    user = cursor.fetchone()
    conn.commit()
    conn.close()
    return user


def check_permission(token):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_token = '%s'" % token)
    user = cursor.fetchone()
    conn.commit()
    conn.close()
    if user is None:
        return False
    return True
