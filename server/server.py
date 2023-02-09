from flask import Flask
import h3


app = Flask(__name__)

@app.route("/", endpoint="default")
def active():
    return "Active"

@app.route('/point/<x>/<y>/<res>')
def coord(x,y,res):
    return str(h3.h3_to_geo_boundary(h3.geo_to_h3(float(x), float(y), float(res)),True))

@app.route('/id/<x>/<y>/<res>')
def identifier(x,y,res):
    return h3.geo_to_h3(float(x), float(y), float(res))

@app.route('/value/<string>')
def value(string):
    return str(5)

if __name__ == "__main__":

    app.run(ssl_context=("cert.pem", "key.pem"))
