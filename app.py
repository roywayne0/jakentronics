from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "SITE FIXED ✅"

if __name__ == "__main__":
    app.run()