from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>TEST</1>"


@app.route("/<num>")
def number(num):
    return f"<h1> TEST {num}</h1>"


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8080, debug=True)
    # app.run()