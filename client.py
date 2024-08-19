from __future__ import annotations

import json
import os
import random
import threading
import time
import typing
import urllib.parse
from datetime import datetime
from typing import TYPE_CHECKING

import pytz
import requests
import websocket

import config

if TYPE_CHECKING:
    from gui import AutoBIRDTonGUI


def json_load(filename: str) -> dict:
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    else:
        return {}


def json_save(data, filename: str):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def generate_utc_timestamp():
    utc_now = datetime.now(pytz.UTC)
    return utc_now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def extract_record_from_url(url: str) -> typing.Optional[str]:
    try:
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        record = query_params.get('record', [None])[0]
        return record
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


class GameClient:
    URL = "https://birdton.site/auth"
    WS_URL = "wss://birdton.site/ws?auth={key}"
    ADS_URL = config.ADS_URL

    def __init__(self, tg_data: dict, ui: AutoBIRDTonGUI):
        self.tg_data: dict = tg_data
        self.ui: AutoBIRDTonGUI = ui
        self.is_connected: bool = False
        self.is_playing: bool = False
        self.score: int = 0
        self.game_id: typing.Optional[str] = None
        self.ws: typing.Optional[websocket.WebSocketApp] = None
        self.auth_key: typing.Optional[str] = None
        self.profile: dict = {}
        self.misc_data: dict = {
            "sub_task": None,
            "boost": None,
            "daily_tasks": None,
            "user_task_progress": None,
            "birds": None,
            "update_time": 0.0
        }

    def on_message(self, ws, message: str):
        self.ui.log(f"[RECV] {message}")

        if message == "pong":
            pass
        else:
            data = json.loads(message)
            event_type = data.get("event_type")

            if event_type in self.misc_data:
                self.misc_data[event_type] = json.loads(data.get("data"))
                if event_type == "birds":
                    self.misc_data["update_time"] = time.time()
                    self.save(misc=True)
                    self.ui.log("Saved misc data")

            elif event_type == "game_id":
                self.game_id = data.get("data")
                self.ws_send({"event_type": "game_start", "data": self.game_id})
                threading.Thread(target=self.play_game).start()

            elif event_type == "game_saved":
                d = json.loads(data.get("data"))
                self.profile["energy"] -= 1
                self.profile["high_score"] = d["high_score"]
                self.profile["balance"] = d["balance"]
                self.profile["score"] = d["score"]
                threading.Thread(target=self.finalize_game, kwargs={"watch_ads": self.ui.watch_ads}).start()

    def on_open(self, ws):
        self.ui.log("WebSocket connection opened")
        self.ws_send({"event_type": "auth", "data": json.dumps(self.tg_data, ensure_ascii=False)})
        self.is_connected = True
        threading.Thread(target=self.ping_thread).start()

    def on_error(self, ws, error):
        self.ui.log(f"[WS] Error occurred: {error}\nClosing connection...")
        self.is_connected = False
        self.is_playing = False
        self.ws.close()

    def on_close(self, ws, close_status_code, close_msg):
        self.is_connected = False
        self.ui.log(f"WebSocket connection closed: {close_status_code} - {close_msg}")

    def ws_send(self, data: typing.Union[dict, list, str]):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False)
        self.ws.send(data)
        self.ui.log(f"[SENT] {data}")

    def authorize(self):
        resp = requests.post(self.URL, headers=config.request_headers, json=self.tg_data)
        if resp.status_code != 200:
            raise ValueError(f"Failed to authorize. Status Code: {resp.status_code}\nResponse:\n{resp.content}")

        self.profile = resp.json()

        user = self.tg_data["initDataUnsafe"]["user"]
        self.profile["name"] = f"{user['first_name']} {user['last_name']}"

        self.profile["update_time"] = time.time()
        self.save(profile=True)
        self.ui.log("Authorization successful")
        self.auth_key = self.profile.get("auth_key")
        return self.profile

    def ping_thread(self):
        self.ui.log("[PING_THREAD] Starting")
        while self.is_connected:
            time.sleep(5)
            try:
                self.ws_send("ping")
            except websocket.WebSocketConnectionClosedException:
                break
        self.ui.log("[PING_THREAD] Closing")

    def play_game(self):
        if self.is_connected and self.is_playing:
            for i in range(self.score):
                time.sleep(1.3575)
                self.ws_send({"event_type": "pipe", "data": self.game_id})
                self.ui.update_progress(i + 1)

            time.sleep(0.1)
            self.ws_send({"event_type": "game_end", "data": self.game_id})

    def finalize_game(self, watch_ads: bool = True):
        # TODO: Extract score multiplier
        mult = self.misc_data["boost"]["boosts"][0]["value"] + 1

        if watch_ads and self.is_connected and self.is_playing:
            self.ui.log(f"[ADS] Starting watching 3 ads")
            for _ in range(3):
                self.ui.log(f"[ADS] Starting watching ad #{_ + 1}")

                resp = requests.get(self.ADS_URL, headers=config.ads_headers)
                if resp.status_code != 200:
                    self.ui.log(f"[ADS] Failed to get an ad | <{resp.status_code}>: {resp.content}")
                    break

                data = resp.json()
                if "banner" not in data:
                    self.ui.log("[ADS] Not ready, skipping...")
                    self.ui.log(f"[ADS] response={data}")
                    break

                record = extract_record_from_url(data["banner"]["trackings"][0]["value"])

                if not self.ad_request(record, "start"):
                    break

                if not self.ad_request(record, "render"):
                    break

                time.sleep(2)

                if not self.ad_request(record, "show"):
                    break

                time.sleep(12)

                if not self.ad_request(record, "complete"):
                    break

                time.sleep(5)

                self.ws_send({"event_type": "ad_multiply"})

                time.sleep(2)

                if not self.ad_request(record, "reward"):
                    break

                self.ui.log(f"[ADS] Ad reward {_ + 1} received")
        else:
            self.ui.log(f"[ADS] Skipping watching ads")

        self.is_playing = False
        self.game_id = None
        self.score = 0
        self.ui.log("Game saved")
        self.ui.game_finished()

        if self.ui.infinite_loop:
            rand_sleep = random.randint(15, 30)
            self.ui.log(f"Waiting for {rand_sleep} seconds before starting next loop...")
            time.sleep(rand_sleep)
            self.ui.start_game(randomize_score=True)

    def ad_request(self, record: str, rtype: str):
        tt_id = {
            "start": 2,
            "render": 13,
            "show": 0,
            "complete": 6,
            "reward": 14,
        }[rtype]

        query_params = {
            "record": record,
            "trackingtypeid": tt_id,
            "user_timestamp": generate_utc_timestamp(),
            "mediaplayhead": "00:00:00.000",
            "type": rtype
        }

        if rtype == "reward":
            query_params.pop("user_timestamp")
            query_params.pop("mediaplayhead")

        query = urllib.parse.urlencode(query_params, doseq=True)
        url = f"https://api.adsgram.ai/event?{query}"

        resp = requests.get(url, headers=config.ads_headers)
        if resp.status_code != 200:
            self.ui.log(f"[ADS] {rtype} failed | <{resp.status_code}>: {resp.content}")
            return False

        return True

    def save(self, *, profile: bool = False, misc: bool = False):
        if profile:
            json_save(self.profile, "profile.json")
        if misc:
            json_save(self.misc_data, "misc_data.json")

    def run(self):
        if not self.auth_key:
            raise ValueError("auth_key missing")

        ws_url = self.WS_URL.format(key=self.auth_key)
        self.ui.log(f"Establishing WS connection at:\n\t{ws_url}")

        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            url=ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            header=config.ws_headers,
        )
        self.ws.run_forever()

    def start_game(self, target_score: int):
        self.score = target_score
        self.ws_send({"event_type": "game_id", "data": "std"})
        self.is_playing = True
