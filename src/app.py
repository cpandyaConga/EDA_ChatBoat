from flask import Flask, jsonify, make_response, send_file
from connector import connector
from snowpark import snowpark

app = Flask(__name__)
app.register_blueprint(connector, url_prefix='/connector')
app.register_blueprint(snowpark, url_prefix='/snowpark')

@app.route("/")
def default():
    return make_response(jsonify(result='Nothing to see here'))

@app.route("/test")
def tester():
    return send_file("index.html")


#app = Flask(__name__, static_folder='static')
# @app.route("/test")
# def tester():
#     return send_file("index.html")

# @app.route("/test")
# def tester():
#     return send_file("index.html")


# @app.route("/chat")
# def tester():
#     return send_file("api_test.html")

@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)

if __name__ == '__main__':
    app.run(port=8001, host='127.0.0.1')
