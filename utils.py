import random
import string
import json

letters = string.ascii_letters + string.digits


def generate_token():
    token = ""
    for i in range(16):
        token += random.choice(letters)
    return token


# Запускать только отсюда и только при изменении json
def change_json():
    f = open("lockers.json", "r", encoding='UTF-8')
    json_string = f.read()
    f.close()
    json_obj = json.loads(json_string)
    counter = 0
    for locker in json_obj:
        for rack in locker["racks"]:
            for half_rack in rack:
                for element in half_rack["elements"]:
                    element["id"] = counter
                    counter += 1
    f = open("lockers.json", "w", encoding='UTF-8')
    json_string = str(json_obj).replace("'", '"').replace("True", 'true')
    f.write(json_string.replace('None', 'null'))
    f.close()
