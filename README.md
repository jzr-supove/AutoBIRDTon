# AutoBIRDTon 🐦

AutoBIRDTon automates playing flappy-bird like game BIRDTon in Telegram.

Its a Python application with a graphical user interface that automates playing BIRDTon. 
It provides a user-friendly interface for connecting to a game, setting target scores, and monitoring progress.

[![Project Banner](https://img.youtube.com/vi/tl7pHg4YPRA/maxresdefault.jpg)](https://www.youtube.com/watch?v=tl7pHg4YPRA)
(Click the image to watch the showcase video)

## ⭐️ Features

- User-friendly GUI
- Profile information display
- Game control with target score setting
- Real-time progress tracking
- Collapsible console for logging game events
- Infinite game mode
- Emulate watching ads

## 📖 Requirements

- Python 3.8+

## 📥 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/jzr-supove/autobirdton.git
   ```
2. Navigate to the project directory:
   ```bash
   cd autobirdton
   ```
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Specify your `user-agent` and `sec-ch-ua` in `.env` file (optional, but recommended):
   - Create `.env` file from `.env.example`:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` file and populate it with your header values 
     
     You can get your header values by visiting this site from inside Telegram on your phone https://modheader.com/headers 

## 🎮 Usage

1. Run the application:
   ```bash
   python main.py
   ```
2. Enter your **authentication key** in the provided field.
3. Click "Connect" to establish a connection with the game server.
4. Once connected, your profile information will be displayed.
5. Enter your desired target score in the "Target Score" field.
6. Click "Start Game" to begin the automated gameplay.
7. Monitor the progress bar and console for real-time updates.

## 🔑 How to obtain authentication key

1. Login to web version of Telegram: https://web.telegram.org
2. Launch BIRDTon game
3. Open DevTools tab (F12)
4. Select Console tab, switch console context from `top` to `birdton.site`
5. Execute this command:
   ```javascript
   JSON.stringify(window.Telegram.WebApp)
   ```
       

6. Copy the resulting JSON as string (Right-click, select "Copy string contents")

## 💻 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Please support the project by giving it a star ⭐️

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📨 Reach out

- Telegram: [@JZRLog](https://t.me/jzrlog)

## ⚠️ Disclaimer

This project is for educational purposes only. Please use responsibly and in accordance with the terms of service of any games you may use it with.