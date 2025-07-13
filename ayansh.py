import requests
import time
import re
from requests.exceptions import RequestException

def extract_target_id(url):
    if url.startswith("pfbid"):
        return url.split('/')[0]
    match = re.search(r'pfbid\w+|\d+', url)
    return match.group(0) if match else None

def get_profile_info(token_eaag):
    try:
        response = requests.get(f"https://graph.facebook.com/me?fields=id,name&access_token={token_eaag}")
        profile_info = response.json()
        return profile_info.get("name"), profile_info.get("id")
    except RequestException:
        return None, None

def make_request(url, headers, cookie):
    try:
        response = requests.get(url, headers=headers, cookies={'Cookie': cookie})
        return response.text
    except RequestException:
        return None

def run_bot(cookie_path, comment_path, post_url, commenter_name, delay):
    try:
        with open(cookie_path, 'r') as f:
            cookies_data = f.read().splitlines()
    except FileNotFoundError:
        print("[!] Cookie file not found.")
        return

    try:
        with open(comment_path, 'r') as f:
            comments = f.readlines()
    except FileNotFoundError:
        print("[!] Comment file not found.")
        return

    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; RMX2144 Build/RKQ1.201217.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.71 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/375.1.0.28.111;]'
    }

    valid_cookies = []
    for cookie in cookies_data:
        response = make_request('https://business.facebook.com/business_locations', headers, cookie)
        if response:
            token_eaag_match = re.search(r'(EAAG\w+)', response)
            if token_eaag_match:
                valid_cookies.append((cookie, token_eaag_match.group(1)))

    if not valid_cookies:
        print("[!] No valid tokens found.")
        return

    target_id = extract_target_id(post_url)
    if not target_id:
        print("[!] Invalid Facebook post URL.")
        return

    x, cookie_index = 0, 0
    while True:
        try:
            teks = comments[x].strip()
            comment_with_name = f"{commenter_name}: {teks}"
            current_cookie, token_eaag = valid_cookies[cookie_index]

            profile_name, profile_id = get_profile_info(token_eaag)
            if profile_name and profile_id:
                print(f"Logged in as: {profile_name} (ID: {profile_id})")

            data = {
                'message': comment_with_name,
                'access_token': token_eaag
            }

            response = requests.post(f'https://graph.facebook.com/{target_id}/comments/', data=data, cookies={'Cookie': current_cookie})
            response_json = response.json()

            if 'id' in response_json:
                print(f"[✓] Comment sent: {comment_with_name}")
            else:
                print("[!] Comment failed:", response_json)

            x = (x + 1) % len(comments)
            cookie_index = (cookie_index + 1) % len(valid_cookies)
            time.sleep(delay)

        except Exception as e:
            print("[!] Error:", e)
            time.sleep(5)
