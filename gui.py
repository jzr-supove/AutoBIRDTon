import json
import random
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk, font, scrolledtext
from typing import Optional

from client import GameClient


def open_link(url: str):
    import webbrowser
    webbrowser.open(url)


class AutoBIRDTonGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("AutoBIRDTon")
        self.master.geometry("700x650")

        # Set up custom font
        custom_font = font.Font(family="Cascadia Code", size=12)
        title_font = font.Font(family="Montserrat Black", size=28, weight="bold")
        button_font = font.Font(family="Montserrat Black", size=14, weight="bold")

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
        self.content_frame.pack(fill="both", expand=True, pady=(20, 5))
        self.content_frame.columnconfigure(0, weight=2)
        self.content_frame.columnconfigure(1, weight=1)

        # Profile Info View (left side)
        self.profile_frame = ttk.LabelFrame(self.content_frame, text="Profile Info")
        self.profile_frame.grid(row=0, column=0, padx=(0, 7.5), sticky="nsew")

        self.profile_labels = {}
        profile_info = [
            "name", "balance", "high_score", "energy",
            "recharges_left", "is_combo_completed"
        ]
        for i, info in enumerate(profile_info):
            if info == "is_combo_completed":
                label_text = "Combo Done:"
            else:
                label_text = f"{info.replace('_', ' ').title()}:"

            label = ttk.Label(self.profile_frame, text=label_text)
            label.grid(row=i, column=0, sticky="w", padx=(10, 5), pady=5)
            value_label = ttk.Label(self.profile_frame, text="N/A")
            value_label.grid(row=i, column=1, sticky="w", padx=10, pady=5)
            self.profile_labels[info] = value_label

        # Game Control Frame (right side)
        game_control_frame = ttk.Frame(self.content_frame)
        game_control_frame.grid(row=0, column=1, sticky="nsew")

        # Score Input (centered)
        self.score_frame = ttk.Frame(game_control_frame)
        self.score_frame.pack(fill="x", pady=10)
        ttk.Label(self.score_frame, text="Target Score:").pack(anchor="center")
        self.score_entry = ttk.Entry(self.score_frame, width=10, font=custom_font)
        self.score_entry.pack(anchor="center", pady=10)

        # Checkboxes frame
        checkbox_frame = ttk.Frame(game_control_frame)
        checkbox_frame.pack(fill="x", pady=10)

        # Center the checkboxes within the checkbox_frame
        checkbox_frame.columnconfigure(0, weight=1)  # Left padding column
        checkbox_frame.columnconfigure(3, weight=1)  # Right padding column

        # Infinite Loop Checkbox
        self.infinite_loop_var = tk.BooleanVar()
        self.infinite_loop_check = ttk.Checkbutton(checkbox_frame, text="Infinite Loop",
                                                   variable=self.infinite_loop_var, command=self.toggle_infinite_loop)
        self.infinite_loop_check.grid(row=0, column=1, padx=(0, 10))

        # Watch Ads Checkbox
        self.watch_ads_var = tk.BooleanVar()
        self.watch_ads_check = ttk.Checkbutton(checkbox_frame, text="Watch Ads", variable=self.watch_ads_var,
                                               command=self.toggle_watch_ads)
        self.watch_ads_check.grid(row=0, column=2)

        # Start Game Button
        style = ttk.Style()
        style.configure('Large.TButton', font=button_font, padding=10)
        self.start_button = ttk.Button(game_control_frame, text="Start Game", command=self.start_game,
                                       style='Large.TButton')
        self.start_button.pack(pady=15)

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(game_control_frame, variable=self.progress_var, maximum=100, length=300,
                                            mode='determinate')
        self.progress_bar.pack(pady=10)

        # Collapsible Console
        self.console_frame = ttk.Frame(self.main_frame)
        self.console_frame.pack(fill="x", pady=(0, 0))

        # Console header with label and collapse button
        self.console_header = ttk.Frame(self.console_frame)
        self.console_header.pack(fill="x")

        self.console_label = ttk.Label(self.console_header, text="Console")
        self.console_label.pack(side="left", padx=(0, 5))

        self.collapse_button = ttk.Button(self.console_header, text="▼", width=3, command=self.toggle_console)
        self.collapse_button.pack(side="left")

        # Console text widget
        console_font = font.Font(family="Consolas", size=10)
        self.console = scrolledtext.ScrolledText(self.console_frame, height=10, wrap="word", font=console_font)
        self.console.pack(fill="both", expand=True, pady=(5, 0))

        self.console_visible = True
        self.auto_scroll = True

        # Bind the user scroll event
        self.console.bind("<MouseWheel>", self.on_console_scroll)

        # Footer with social links
        footer_frame = ttk.Frame(self.master)
        footer_frame.pack(side="bottom", fill="x", pady=(5, 10))
        ttk.Label(footer_frame, text="Author: JZR SUPOVE").pack(side="left", padx=15)
        ttk.Button(footer_frame, text="Telegram",
                   command=lambda: open_link("https://t.me/jzrlog")).pack(side="left", padx=5)
        ttk.Button(footer_frame, text="GitHub",
                   command=lambda: open_link("https://github.com/jzr-supove")).pack(side="left", padx=5)
        ttk.Button(footer_frame, text="Instagram",
                   command=lambda: open_link("https://instagram.com/jzr_yusupov")).pack(side="left", padx=5)

        # Initially hide content and console
        # self.auth_frame.pack_forget()
        self.content_frame.pack_forget()
        # self.console_frame.pack_forget()

        # Game variables
        self.target_score = 0
        self.current_score = 0
        self.game_active = False
        self.infinite_loop = False
        self.watch_ads = False
        self.game_client: Optional[GameClient] = None

    def toggle_console(self):
        if self.console_visible:
            self.console.pack_forget()
            self.collapse_button.config(text="▶")
        else:
            self.console.pack(fill="both", expand=True, pady=(5, 0))
            self.collapse_button.config(text="▼")
        self.console_visible = not self.console_visible

    def on_console_scroll(self, event):
        # If the user scrolls up, disable auto-scroll
        if event.delta > 0:
            self.auto_scroll = False
        # If the user scrolls to the bottom, re-enable auto-scroll
        elif self.console.yview()[1] == 1.0:
            self.auto_scroll = True

    def log(self, message):
        self.console.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]} | {message}\n")
        if self.auto_scroll:
            self.console.see(tk.END)

    def toggle_infinite_loop(self):
        self.infinite_loop = self.infinite_loop_var.get()
        if self.infinite_loop:
            self.score_entry.state(['disabled'])
            self.log("Infinite loop mode activated. Game will continue indefinitely.")
        else:
            self.score_entry.state(['!disabled'])
            self.log("Infinite loop mode deactivated. Game will stop at target score.")

    def toggle_watch_ads(self):
        self.watch_ads = self.watch_ads_var.get()
        if self.watch_ads:
            self.log("Ad watcher is enabled. 3 ads will be watched at the end of the game")
        else:
            self.log("Ad watcher is disabled. Ad-watching will be skipped at the end of the game")

    def connect_websocket(self):
        auth_key = self.auth_entry.get().strip("'").strip('"')
        try:
            auth_key_dict = json.loads(auth_key)
        except Exception as e:
            self.log(f"Invalid auth key format, provide valid JSON string!\nException: {e}")
            return

        if auth_key_dict.get("platform") != "android":
            auth_key_dict["platform"] = "android"

        self.log(f"Attempting to connect with key: {auth_key_dict}")

        self.game_client = GameClient(tg_data=auth_key_dict, ui=self)
        try:
            profile = self.game_client.authorize()
            self.update_profile_info(profile)

            # Hide auth frame and show content
            self.auth_frame.pack_forget()
            self.console_frame.pack_forget()
            self.content_frame.pack(fill="both", expand=True, pady=10)
            self.console_frame.pack(fill="x", pady=(5, 0))

            # Start WebSocket connection in a separate thread
            threading.Thread(target=self.game_client.run, daemon=True).start()
        except Exception as e:
            self.log(f"Failed to connect: {str(e)}")

    def update_profile_info(self, info: dict):
        for key, value in info.items():
            if key in self.profile_labels:
                self.profile_labels[key].config(text=str(value))

    def start_game(self, randomize_score=False):
        if not self.game_active and self.game_client and self.game_client.is_connected:
            try:
                self.target_score = int(self.score_entry.get())

                if randomize_score:
                    self.target_score = random.randint(abs(self.target_score - 100), self.target_score + 50)

                # if self.game_client.profile["energy"] < 1:
                #     self.log("Not enough energy to start the game.")
                #     return

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
