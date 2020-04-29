import sys
from SocketServer import Server
import DataBaseWork


def run_server():
    try:
        server = Server()
        server.start()
    except Exception as e:
        print("You have some error: {}".format(e))


def create_admin():
    try:
        login = input("Введите логин \n")
        password = input("Введите пароль \n")
        DataBaseWork.register_user(login, password)
        print("Пользователь успешно создан")
    except Exception as e:
        print("You have some error: {}".format(e))


if __name__ == "__main__":
    try:
        arg = sys.argv[1]
    except Exception as e:
        print("Кажется вы не указали ниодного аргумента. Поставьте аргумент help, чтобы увидеть все доступные аргументы")
        exit(0)
    if arg == "runserver":
        run_server()
    elif arg == "createadmin":
        create_admin()
    elif arg == "help":
        print("runserver - запуск сервера, createadmin - создать нового админа")
    else:
        print("Неизвестная команда. Поставьте аргумент help, чтобы увидеть все доступные аргументы")
