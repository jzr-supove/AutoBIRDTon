from os import getenv
from dotenv import load_dotenv

load_dotenv()

USER_AGENT = getenv('USER_AGENT') or "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
SEC_CH_UA = getenv('SEC_CH_UA') or "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"116\", \"Google Chrome\";v=\"116\""
ADS_URL = "https://api.adsgram.ai/adv?blockId=801&tg_id={user_id}&tg_platform=android&platform=Android&language=en&chat_type=sender&chat_instance={chat_instance}"


request_headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "user-agent": USER_AGENT,
    "sec-ch-ua": SEC_CH_UA,
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "Referer": "https://birdton.site/",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}

ads_headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,ru;q=0.8",
    "sec-ch-ua": SEC_CH_UA,
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "Referer": "https://birdton.site/",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}

ws_headers = {
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
    "Sec-WebSocket-Version": "13"
}