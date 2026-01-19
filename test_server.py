from flask import Flask

app = Flask(__name__)

@app.get("/")
def home():
    return "OK - servidor funcionando"

if __name__ == "__main__":
    print("Arrancando en http://127.0.0.1:5050")
    app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False)
    