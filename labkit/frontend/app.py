from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template(
        'dashboard.html', 
        tensorboard=app.data.get('tensorboard', None))
