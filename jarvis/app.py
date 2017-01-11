import os
from   flask              import Flask

app = Flask(__name__)

@app.route('/')
def Welcome():
    return app.send_static_file('index.html')

if __name__ == "__main__":
    port = os.getenv('PORT', '5000')
    app.run(host='0.0.0.0', port=int(port))
