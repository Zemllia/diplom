import asyncio
import websockets
import json
import DataBaseWork
import config


class Server:
    ip = ""
    port = 0

    sessions = []

    USERS = set()

    repair_rules = {
        "break": "disable",
        "lost": "enable",
        "break_io": "refresh"
    }

    async def hello(self, ws, path):
        while True:
            json_string = await ws.recv()

            self.USERS.add(ws)
            print(self.USERS)

            json_object = json.loads(json_string)

            try:
                type_request = json_object['type']
                print(type_request)
                answers = await self.deploy_command(type_request, json_object, ws.remote_address, self.USERS)
            except Exception as e:
                print(e)
                answers = str(json_object).replace("'", '"')

            for answer in answers:
                await ws.send(answer)
                print("sent> %s" % str(answer))

    async def deploy_command(self, type_request, json_object, remote_address, USERS):
        if type_request == 'new user':
            f = open("lockers.json", "r", encoding='UTF-8')
            json_string = f.read()
            f.close()
            new_session = self.Session(json_object['body']['fio'],
                                       json.loads(json_string),
                                       remote_address[0],
                                       remote_address[1])
            new_session.session_id = len(self.sessions)
            self.sessions.append(new_session)

            message_for_admin = '{"type": "notification", "body":' \
                                ' {"type": "login", "header": "%s", "info": "Присоединился к системе"}}'\
                                % json_object['body']['fio']

            await asyncio.wait([user.send(message_for_admin) for user in USERS])

            return ['{ "type": "new user", "body": { "id": %d, "fio": "%s"} }'
                    % (new_session.session_id, json_object['body']['fio']),
                    '{"type": "lockers", "target": %s, "body": %s}' % (str(new_session.session_id), json_string)]

        if type_request == 'login admin':
            data = json_object['body']
            print(data)
            try:
                if data['username'] is None or data['password'] is None:
                    return ['{"ERROR": "Username or password are empty"}']
                token = DataBaseWork.login_user(username=data['username'], password=data["password"])
                if token is None:
                    return ['{"ERROR": "Username or password are invalid"}']
                final_send_users = []
                for user in self.sessions:
                    final_send_users.append(json.loads(json.dumps(user.__dict__)))
                return ['{"type": "token", "body": {"token": "%s"}}' % token,
                        '{"type": "active users", "body": %s}'
                        % str(final_send_users).replace("'", '"').replace("True", 'true').replace('None', 'null')]
            except Exception as e:
                print(e)
                return ['{"Error": "%s"}' % str(e)]

        if type_request == 'get lockers':
            token = json_object['token']
            data = json_object['body']
            if not DataBaseWork.check_permission(token):
                return ['{"ERROR": "User dont have permission to this request"}']

            session_id = data['session_id']
            locker = self.sessions[int(session_id)].lockers
            return ['{"type": "lockers", "target": "admin", "body": %s}' %
                    str(locker).replace("'", '"').replace("True", 'true').replace('None', 'null')]

        if type_request == 'active users':
            token = json_object['token']
            if not DataBaseWork.check_permission(token):
                return ['{"ERROR": "User dont have permission to this request"}']

            final_send_users = []
            for user in self.sessions:
                final_send_users.append(json.loads(json.dumps(user.__dict__)))

            return ['{"type": "active users", "body": %s}'
                    % str(final_send_users).replace("'", '"').replace("True", 'true').replace('None', 'null')]

        if type_request == 'change cell':
            token = json_object['token']
            data = json_object['body']
            if not DataBaseWork.check_permission(token):
                return ['{"ERROR": "User dont have permission to this request"}']

            session_id = data['session_id']
            cell_id = data['cell_id']
            state = data['state']

            cur_session = self.sessions[int(session_id)]
            cur_locker = cur_session.lockers

            for locker in cur_locker:
                for rack in locker["racks"]:
                    for half_rack in rack:
                        for element in half_rack["elements"]:
                            if element["id"] == cell_id:
                                element["state"] = state
                                break
            self.sessions[int(session_id)].lockers = cur_locker
            message_for_admin = '{"type": "lockers", "target": %s, "body": %s}'\
                                % (
                                   '"admin"',
                                   str(cur_locker).replace("'", '"').replace("True", 'true').replace('None', 'null')
                                   )
            message_for_user = '{"type": "lockers", "target": %s, "body": %s}'\
                               % (
                                   str(session_id),
                                   str(cur_locker).replace("'", '"').replace("True", 'true').replace('None', 'null')
                                  )
            await asyncio.wait([user.send(message_for_user) for user in USERS])
            return [message_for_admin]

        if type_request == 'repair cell':
            data = json_object['body']

            session_id = data['session_id']
            cell_id = data['cell_id']
            action = data['action']

            cur_session = self.sessions[int(session_id)]
            cur_locker = cur_session.lockers

            is_fixed = False

            for locker in cur_locker:
                for rack in locker["racks"]:
                    for half_rack in rack:
                        for element in half_rack["elements"]:
                            if element["id"] == cell_id:
                                if action == 'reboot_os':
                                    element["state"] = "active"
                                    is_fixed = True
                                else:
                                    if self.repair_rules[element["state"]] == action:
                                        element["state"] = "active"
                                        is_fixed = True
                                    else:
                                        is_fixed = False
                                break
            self.sessions[int(session_id)].lockers = cur_locker
            print(session_id)
            if is_fixed:
                message_for_admin = '{"type": "lockers", "session_id": %s, "target": %s, "body": %s}'\
                                    % (str(session_id),
                                       '"admin"',
                                       str(cur_locker).replace("'", '"').replace("True", 'true').replace('None', 'null')
                                       )
                message_for_user = '{"type": "lockers", "target": %s, "body": %s}'\
                                   % (str(session_id),
                                      str(cur_locker).replace("'", '"').replace("True", 'true').replace('None', 'null')
                                      )
            else:
                message_for_admin = '{"Error": "No result"}'
                message_for_user = '{"Error": "No result"}'
            print(message_for_admin)
            await asyncio.wait([user.send(message_for_user) for user in USERS])
            return [message_for_admin]

    def start(self):
        print("Starting server on {}:{}".format(config.ip, config.port))
        start_server = websockets.serve(self.hello, config.ip, config.port)
        print("Started server")
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
        print("Server closed")

    class Session:
        session_id = 0
        fio = ''
        user_ip = ''
        user_port = 0
        lockers = {}

        def __init__(self, fio, lockers, user_ip, user_port, session_id=None):
            self.session_id = session_id
            self.fio = fio
            self.lockers = lockers
            self.user_ip = user_ip
            self.user_port = user_port


if __name__ == '__main__':

    ip = "192.168.0.4"
    port = 27015

    server = Server()
    server.start()
