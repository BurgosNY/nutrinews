from flask import Flask, render_template, flash, redirect, url_for, request
from flask_pymongo import PyMongo
from pymongo import DESCENDING, ASCENDING
from link_analysis import link_check
import settings
from flask_wtf import FlaskForm


# Initialize app:
app = Flask(__name__)
app.config["MONGO_URI"] = settings.MONGODB_URI
mongo = PyMongo(app)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        result = request.form
        url = result['url']
        print(url)
        data = link_check(url)
        print(data)
        return render_template('index.html', **data)
    else:
        return render_template('home.html')
