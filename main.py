from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor
from os import getenv
from datetime import date
import requests


# APP & KEYS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
app.config['SECRET_KEY'] = getenv("SECRET_KEY")
Bootstrap5(app)

API_KEY = getenv('API_KEY')
API_SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

# Set the DB

db = SQLAlchemy(app)

# CKEditor
ckeditor = CKEditor(app)

# ROUTES

@app.route("/")
def render_main():
    return "<h1>Wow</h1>"

if __name__=="__main__":
    app.run(debug=True, port=5004)