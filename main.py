from flask import Flask

app = Flask(__name__)

@app.route("/")
def render_main():
    return "<h1>Wow</h1>"

if __name__=="__main__":
    app.run(debug=True, port=5004)