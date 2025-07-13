from flask import Flask, render_template, request, redirect
import threading
from bot import run_bot

app = Flask(__name__)
bg_thread = None

@app.route("/", methods=["GET", "POST"])
def index():
    global bg_thread
    if request.method == "POST":
        cookie_file = request.files["cookie_file"]
        comment_file = request.files["comment_file"]
        post_url = request.form["post_url"]
        name = request.form["name"]
        delay = int(request.form["delay"])

        cookie_path = "cookies.txt"
        comment_path = "comments.txt"
        cookie_file.save(cookie_path)
        comment_file.save(comment_path)

        if bg_thread is None or not bg_thread.is_alive():
            bg_thread = threading.Thread(
                target=run_bot,
                args=(cookie_path, comment_path, post_url, name, delay)
            )
            bg_thread.start()

        return redirect("/")
    return render_template("index.html")

@app.route("/ping")
def ping():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
