import json
import logging
import os
import threading
import time

import requests
import websocket
from dotenv import load_dotenv

load_dotenv()
logging.getLogger('websocket').setLevel(logging.ERROR)

USER_AGENT = os.getenv('USER_AGENT')
SEC_CH_UA = os.getenv('SEC_CH_UA')

request_headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "pragma": "no-cache",
    "user-agent": USER_AGENT,
    "sec-ch-ua": SEC_CH_UA,
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin"
}

ws_headers = {
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
    "Sec-WebSocket-Version": "13"
}


def json_load(filename: str) -> dict:
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    else:
        return {}


def json_save(data, filename: str):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def on_error(ws, error):
    print(f"[WS] Error occurred: {error}")


class GameClient:
    URL = "https://birdton.site/auth"
    WS_URL = "wss://birdton.site/ws?auth={key}"

    def __init__(self, tg_data: str):
        self.tg_data = tg_data
        self.is_connected = False
        self.is_playing = False
        self.score = 0
        self.game_id = None

        self.ws = None
        self.auth_key = None

        self.profile = {
            "auth_key": None,
            "update_time": 0.0
        }
        self.misc_data = {
            "sub_task": None,
            "boost": None,
            "daily_tasks": None,
            "user_task_progress": None,
            "birds": None,
            "update_time": 0.0
        }

        self.load_data()
        self.authorize()

        if self.profile.get("auth_key"):
            self.auth_key = self.profile["auth_key"]

    def on_message(self, ws, message):
        print(f"[RECV] {message}")

        if message == "pong":
            pass
        else:
            data = json.loads(message)
            event_type = data.get("event_type")

            if event_type in self.misc_data:
                self.misc_data[event_type] = data.get("data")
                if event_type == "birds":
                    self.misc_data["update_time"] = time.time()
                    self.save(misc=True)
                    print("Saved misc data")

            elif event_type == "game_id":
                self.game_id = data.get("data")
                d = json.dumps({"event_type": "game_start", "data": self.game_id})
                self.ws.send(d)
                print(f"[SENT] {d}")
                threading.Thread(target=self.play_game).start()

            elif event_type == "game_saved":
                self.is_playing = False
                self.game_id = None
                self.score = 0
                print("Game saved")

    def on_open(self, ws):
        print("Connection opened")
        auth_data = json.dumps({"event_type": "auth", "data": self.tg_data})
        self.is_connected = True
        self.ws.send(auth_data)
        print(f"[SENT] {auth_data}")
        threading.Thread(target=self.ping_thread).start()
        threading.Thread(target=self.start_game).start()

    def on_close(self, ws, close_status_code, close_msg):
        self.is_connected = False
        print(f"[WS] Connection closed: {close_status_code} - {close_msg}")

    def authorize(self):
        resp = requests.post(self.URL, headers=request_headers, data=self.tg_data)

        if resp.status_code != 200:
            raise ValueError(f"Failed to authorize. Status Code: {resp.status_code}\nResponse:\n{resp.content}")

        self.profile = resp.json()
        self.profile["update_time"] = time.time()
        self.save(profile=True)
        print(f"Authorization successful")

    def ping_thread(self):
        print("[PING_THREAD] Starting")
        while self.is_connected:
            time.sleep(5)
            try:
                self.ws.send("ping")
                print("[SENT] ping")
            except websocket.WebSocketConnectionClosedException:
                break
        print("[PING_THREAD] Closing")

    def start_game(self):
        while self.is_connected:
            user_input = input("Enter desired score (0 to stop playing): ")

            if user_input.isnumeric():
                score = int(user_input)
                if score < 0:
                    break
            else:
                print("Invalid input. Please enter an integer")
                continue

            self.score = score
            d = json.dumps({"event_type": "game_id", "data": "std"})
            self.ws.send(d)
            print(f"[SENT] {d}")
            self.is_playing = True

            while self.is_playing:
                time.sleep(1)
        else:
            print("[WS] StartGame | Connection closed")

    def play_game(self):
        if self.is_playing:
            for i in range(self.score):
                time.sleep(1.3575)
                d = json.dumps({"event_type": "pipe", "data": self.game_id})
                self.ws.send(d)
                print(f"[SENT] {d}")

            time.sleep(0.1)
            d = json.dumps({"event_type": "game_end", "data": self.game_id})
            self.ws.send(d)
            print(f"[SENT] {d}")

    def save(self, *, profile: bool = False, misc: bool = False):
        if profile:
            json_save(self.profile, "profile.json")
        if misc:
            json_save(self.misc_data, "misc_data.json")

    def load_data(self):
        self.profile = json_load("profile.json")
        self.misc_data = json_load("misc_data.json")

    def run(self):
        if not self.auth_key:
            raise ValueError("auth_key missing")

        ws_url = self.WS_URL.format(key=self.auth_key)
        print(f"Opening ws connection at\n\t{ws_url}")

        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=on_error,
            on_close=self.on_close,
            header=ws_headers,
        )
        self.ws.run_forever()


def main():
    tg_data = input("Paste Telegram Data: ")
    client = GameClient(tg_data)
    client.run()


if __name__ == "__main__":
    main()
