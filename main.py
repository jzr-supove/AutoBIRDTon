import json
import logging
import os
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import ttk, font
from typing import Optional

import requests
import websocket
from dotenv import load_dotenv

load_dotenv()
logging.getLogger('websocket').setLevel(logging.ERROR)

USER_AGENT = os.getenv('USER_AGENT')
SEC_CH_UA = os.getenv('SEC_CH_UA')


class GameClient:
    URL = "https://birdton.site/auth"
    WS_URL = "wss://birdton.site/ws?auth={key}"

    def __init__(self, tg_data: str, ui):
        self.tg_data = tg_data
        self.ui = ui
        self.is_connected = False
        self.is_playing = False
        self.score = 0
        self.game_id = None
        self.ws = None
        self.auth_key = None
        self.profile = {"auth_key": None, "update_time": 0.0}
        self.misc_data = {
            "sub_task": None, "boost": None, "daily_tasks": None,
            "user_task_progress": None, "birds": None, "update_time": 0.0
        }

    def on_message(self, ws, message):
        self.ui.log(f"[RECV] {message}")

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
                    self.ui.log("Saved misc data")

            elif event_type == "game_id":
                self.game_id = data.get("data")
                d = json.dumps({"event_type": "game_start", "data": self.game_id})
                self.ws.send(d)
                self.ui.log(f"[SENT] {d}")
                threading.Thread(target=self.play_game).start()

            elif event_type == "game_saved":
                d = json.loads(data.get("data"))
                self.profile["energy"] -= 1
                self.profile["high_score"] = d["high_score"]
                self.profile["balance"] = d["balance"]
                self.profile["score"] = d["score"]

                self.is_playing = False
                self.game_id = None
                self.score = 0
                self.ui.log("Game saved")
                self.ui.game_finished()

    def on_open(self, ws):
        self.ui.log("WebSocket connection opened")
        auth_data = json.dumps({"event_type": "auth", "data": self.tg_data})
        self.is_connected = True
        self.ws.send(auth_data)
        self.ui.log(f"[SENT] {auth_data}")
        threading.Thread(target=self.ping_thread).start()

    def on_close(self, ws, close_status_code, close_msg):
        self.is_connected = False
        self.ui.log(f"WebSocket connection closed: {close_status_code} - {close_msg}")

    def authorize(self):
        resp = requests.post(self.URL, headers=request_headers, data=self.tg_data)
        if resp.status_code != 200:
            raise ValueError(f"Failed to authorize. Status Code: {resp.status_code}\nResponse:\n{resp.content}")

        self.profile = resp.json()

        user = json.loads(self.tg_data)["initDataUnsafe"]["user"]
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
                self.ws.send("ping")
                self.ui.log("[SENT] ping")
            except websocket.WebSocketConnectionClosedException:
                break
        self.ui.log("[PING_THREAD] Closing")

    def play_game(self):
        if self.is_connected and self.is_playing:
            for i in range(self.score):
                time.sleep(1.3575)
                data = json.dumps({"event_type": "pipe", "data": self.game_id})
                self.ui.log(f"[SENT] {data}")
                self.ws.send(data)
                self.ui.update_progress(i + 1)

            time.sleep(0.1)
            data = json.dumps({"event_type": "game_end", "data": self.game_id})
            self.ui.log(f"[SENT] {data}")
            self.ws.send(data)

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
        self.ui.log(f"Establishing WS connection at:\n\t{ws_url}")

        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=lambda ws, error: self.ui.log(f"[WS] Error occurred: {error}"),
            on_close=self.on_close,
            header=ws_headers,
        )
        self.ws.run_forever()

    def start_game(self, target_score: int):
        self.score = target_score
        self.ws.send(json.dumps({"event_type": "game_id", "data": "std"}))
        self.is_playing = True


class FlappyBirdAutoPlayerUI:
    def __init__(self, master):
        self.master = master
        self.master.title("AutoBIRDTon")
        self.master.geometry("1000x700")

        # Set up custom font
        custom_font = font.Font(family="Comic Sans MS", size=12)
        title_font = font.Font(family="Comic Sans MS", size=28, weight="bold")
        button_font = font.Font(family="Comic Sans MS", size=14, weight="bold")

        # Apply custom font to all widgets
        self.master.option_add("*Font", custom_font)

        # Main frame
        self.main_frame = ttk.Frame(self.master, padding="20")
        self.main_frame.pack(expand=True, fill="both")

        # Title and Icon
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(pady=20)

        icon_label = ttk.Label(title_frame, text="🐦", font=("Arial", 36))
        icon_label.pack(side="left", padx=(0, 20))

        title_label = ttk.Label(title_frame, text="AutoBIRDTon", font=title_font)
        title_label.pack(side="left")

        # Auth Key Input (centered)
        self.auth_frame = ttk.Frame(self.main_frame)
        self.auth_frame.pack(fill="x", pady=30)

        auth_inner_frame = ttk.Frame(self.auth_frame)
        auth_inner_frame.pack(expand=True)

        ttk.Label(auth_inner_frame, text="Enter Auth Key:").pack(side="left")
        self.auth_entry = ttk.Entry(auth_inner_frame, width=40, font=custom_font)
        self.auth_entry.pack(side="left", padx=(10, 20))
        self.auth_button = ttk.Button(auth_inner_frame, text="Connect", command=self.connect_websocket,
                                      style='Large.TButton')
        self.auth_button.pack(side="left")

        # Content frame (for profile info and game controls)
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, pady=20)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=1)

        # Profile Info View (left side)
        self.profile_frame = ttk.LabelFrame(self.content_frame, text="Profile Info")
        self.profile_frame.grid(row=0, column=0, padx=(0, 20), sticky="nsew")

        self.profile_labels = {}
        profile_info = [
            "name", "balance", "high_score", "energy",
            "recharges_left", "is_combo_completed"
        ]
        for i, info in enumerate(profile_info):
            label = ttk.Label(self.profile_frame, text=f"{info.replace("_", " ").title()}:")
            label.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            value_label = ttk.Label(self.profile_frame, text="N/A")
            value_label.grid(row=i, column=1, sticky="w", padx=10, pady=5)
            self.profile_labels[info] = value_label

        # Game Control Frame (right side)
        game_control_frame = ttk.Frame(self.content_frame)
        game_control_frame.grid(row=0, column=1, sticky="nsew")

        # Score Input (centered)
        self.score_frame = ttk.Frame(game_control_frame)
        self.score_frame.pack(fill="x", pady=20)
        ttk.Label(self.score_frame, text="Target Score:").pack(anchor="center")
        self.score_entry = ttk.Entry(self.score_frame, width=10, font=custom_font)
        self.score_entry.pack(anchor="center", pady=10)

        # Start Game Button (larger and more prominent)
        style = ttk.Style()
        style.configure('Large.TButton', font=button_font, padding=10)
        self.start_button = ttk.Button(game_control_frame, text="Start Game", command=self.start_game,
                                       style='Large.TButton')
        self.start_button.pack(pady=20)

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(game_control_frame, variable=self.progress_var, maximum=100, length=300,
                                            mode='determinate')
        self.progress_bar.pack(pady=20)

        # Collapsible Console
        self.console_frame = ttk.LabelFrame(self.main_frame, text="Console")
        self.console_frame.pack(fill="x", pady=(20, 0))

        self.console = tk.Text(self.console_frame, height=5, wrap="word", font=custom_font)
        self.console.pack(fill="x", expand=True)

        # Footer with social links
        footer_frame = ttk.Frame(self.master)
        footer_frame.pack(side="bottom", fill="x", pady=10)
        ttk.Label(footer_frame, text="Author: Jasur Yusupov").pack(side="left", padx=10)
        ttk.Button(footer_frame, text="Instagram",
                   command=lambda: open_link("https://instagram.com/jzr_yusupov")).pack(side="left", padx=5)
        ttk.Button(footer_frame, text="Telegram",
                   command=lambda: open_link("https://t.me/jzrlog")).pack(side="left", padx=5)
        ttk.Button(footer_frame, text="GitHub",
                   command=lambda: open_link("https://github.com/goodeejay")).pack(side="left", padx=5)

        # Initially hide content and console
        self.content_frame.pack_forget()
        # self.console_frame.pack_forget()

        # Game variables
        self.target_score = 0
        self.current_score = 0
        self.game_active = False
        self.game_client: Optional[GameClient] = None

    def log(self, message):
        self.console.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]} | {message}\n")
        self.console.see(tk.END)

    def connect_websocket(self):
        auth_key = self.auth_entry.get()
        self.log(f"Attempting to connect with key: {auth_key}")

        self.game_client = GameClient(auth_key, self)
        try:
            profile = self.game_client.authorize()
            self.update_profile_info(profile)

            # Hide auth frame and show content
            self.auth_frame.pack_forget()
            self.content_frame.pack(fill="both", expand=True, pady=20)
            self.console_frame.pack(fill="x", pady=(20, 0))

            # Start WebSocket connection in a separate thread
            threading.Thread(target=self.game_client.run, daemon=True).start()
        except Exception as e:
            self.log(f"Failed to connect: {str(e)}")

    def update_profile_info(self, info: dict):
        for key, value in info.items():
            if key in self.profile_labels:
                self.profile_labels[key].config(text=str(value))

    def start_game(self):
        if not self.game_active and self.game_client and self.game_client.is_connected:
            try:
                self.target_score = int(self.score_entry.get())

                if self.game_client.profile["energy"] < 1:
                    self.log("Not enough energy to start the game.")
                    return

                self.log(f"Starting game. Target score: {self.target_score}")
                self.current_score = 0
                self.game_active = True
                self.start_button.state(['disabled'])
                self.score_entry.state(['disabled'])
                self.progress_var.set(0)

                # Start the game in the GameClient
                self.game_client.start_game(self.target_score)
            except ValueError:
                self.log("Please enter a valid number for the target score.")
        else:
            self.log("Game is not ready or already in progress.")

    def update_progress(self, current_score):
        self.current_score = current_score
        progress = (self.current_score / self.target_score) * 100
        self.progress_var.set(progress)
        self.log(f"Passed pipe {self.current_score}/{self.target_score}")

    def game_finished(self):
        self.game_active = False
        self.start_button.state(['!disabled'])
        self.score_entry.state(['!disabled'])
        self.log("Game finished!")

        # Update profile info
        if self.game_client:
            self.update_profile_info(self.game_client.profile)


def open_link(url: str):
    import webbrowser
    webbrowser.open(url)


def json_load(filename: str) -> dict:
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    else:
        return {}


def json_save(data, filename: str):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


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

if __name__ == "__main__":
    root = tk.Tk()
    app = FlappyBirdAutoPlayerUI(root)
    root.mainloop()
