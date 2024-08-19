from os import getenv
from dotenv import load_dotenv

load_dotenv()

USER_AGENT = getenv('USER_AGENT')
SEC_CH_UA = getenv('SEC_CH_UA')
ADS_URL = getenv('ADS_URL')


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
    "sec-fetch-site": "same-origin",
    "Referer": "https://birdton.site/",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}

ads_headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,ru;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
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