from flask import Flask, render_template, request
import os
import threading
import time
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

status_logs = []
posting_thread = None
is_running = False

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def extract_form_data(session, post_url, cookie):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
        "Cookie": cookie
    }
    try:
        r = session.get(post_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form", method="post")
        if not form or not form.get("action"):
            return None
        data = {}
        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value", "")
            if name:
                data[name] = value
        return form["action"], data
    except:
        return None

def post_comments_loop(post_url, cookies, messages, delay):
    global is_running
    session = requests.Session()
    total_sent = 0
    is_running = True
    while is_running:
        for msg in messages:
            for idx, cookie in enumerate(cookies):
                if not is_running:
                    break
                try:
                    result = extract_form_data(session, post_url, cookie)
                    if not result:
                        log = f"[{idx+1}] ❌ Cookie invalid/form missing — skipping."
                        status_logs.append(log)
                        continue
                    action_url, data = result
                    data["comment_text"] = msg + " #AY9NSH_H3R3"
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
                        "Cookie": cookie
                    }
                    full_url = "https://mbasic.facebook.com" + action_url
                    res = session.post(full_url, data=data, headers=headers)

                    if "Your comment has been added" in res.text:
                        total_sent += 1
                        log = f"[{idx+1}] ✅ Sent: {msg}"
                    else:
                        log = f"[{idx+1}] ⚠️ Tried: {msg}"

                    status_logs.append(log)
                    status_logs.append(f"⏱ Time: {time.strftime('%Y-%m-%d %I:%M:%S %p')} | Total: {total_sent}")
                    time.sleep(delay)
                except Exception as e:
                    status_logs.append(f"[{idx+1}] 🔴 Error: {e}")
                    continue

@app.route("/", methods=["GET", "POST"])
def index():
    global posting_thread, is_running, status_logs

    if request.method == "POST":
        if "start" in request.form:
            cookie_file = request.files["cookies"]
            msg_file = request.files["messages"]
            post_url = request.form["post_url"].strip()
            delay = int(request.form["delay"].strip())

            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            cookie_path = os.path.join(UPLOAD_FOLDER, "cookies.txt")
            msg_path = os.path.join(UPLOAD_FOLDER, "messages.txt")
            cookie_file.save(cookie_path)
            msg_file.save(msg_path)

            cookies = load_file(cookie_path)
            messages = load_file(msg_path)

            status_logs = ["🚀 Posting started..."]
            posting_thread = threading.Thread(target=post_comments_loop, args=(post_url, cookies, messages, delay))
            posting_thread.start()

        elif "stop" in request.form:
            is_running = False
            status_logs.append("⛔ Posting stopped manually.")

    return render_template("index.html", logs=status_logs, running=is_running)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
