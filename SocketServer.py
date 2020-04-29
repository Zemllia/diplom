import socket
import asyncio
import websockets
import json
import DataBaseWork
import config


class Server:
    ip = ""
    port = 0

    sessions = []

    async def hello(self, ws, path):
        json_string = await ws.recv()

        json_object = json.loads(json_string)

        try:
            type_request = json_object['type']
            answers = self.deploy_command(type_request, json_object)
        except Exception as e:
            print(e)
            answers = str(json_object).replace("'", '"')

        for answer in answers:
            await ws.send(answer)
            print(f"sent> {answer}")

    def deploy_command(self, type_request, json_object):
        if type_request == 'new user':
            self.sessions.append(self.Session(json_object['body']['fio']))
            f = open("lockers.json", "r", encoding='UTF-8')
            json_string = f.read()
            f.close()
            return ['{ "type": "new user", "body": { "id": %d, "fio": "%s"} }' % (len(self.sessions) - 1, json_object['body']['fio']),
                    '{"type": "lockers", "body": %s}' % json_string]
        if type_request == 'login admin':
            data = json_object['body']
            print(data)
            try:
                if data['username'] is None or data['password'] is None:
                    return ['{"ERROR": "Username or password are empty"}']
                token = DataBaseWork.login_user(username=data['username'], password=data["password"])
                if token is None:
                    return ['{"ERROR": "Username or password are invalid"}']
                return ['{"Token": "%s"}' % token]
            except Exception as e:
                print(e)
                return ['{"Error": "%s"}' % str(e)]

    def start(self):
        print("Starting server on {}:{}".format(config.ip, config.port))
        start_server = websockets.serve(self.hello, config.ip, config.port)
        print("Started server")
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
        print("Server closed")


    class Session:
        fio = ''
        lockers = {}

        def __init__(self, fio):
            self.fio = fio


if __name__ == '__main__':

    ip = "192.168.0.4"
    port = 27015

    server = Server(ip, port)
    server.start()



