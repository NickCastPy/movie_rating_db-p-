from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float
from flask_login import login_required, login_user, logout_user, UserMixin, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor
from os import getenv
from datetime import date
import requests


# APP & KEYS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
app.config['SECRET_KEY'] = getenv("SECRET_KEY")

API_KEY = getenv('API_KEY')
API_SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

# Set the DB

db = SQLAlchemy(app)

# CKEditor
ckeditor = CKEditor(app)

# DB | TABLE DATA

from sqlalchemy import func

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    comments: Mapped[str] = relationship("Comment", back_populates="comment_author")
    movies_added: Mapped[str] = relationship("Movie", back_populates="contributor")

class Movie(db.Model):
    __tablename__ = 'movies'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    comments: Mapped[str] = relationship('Comment', back_populates='parent_movie')
    
    @property
    def average_rating(self):
        ratings = [comment.rating for comment in self.comments]
        if ratings:
            return sum(ratings) / len(ratings)
        return 0  

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'), nullable=False)
    comment_author: Mapped[str] = relationship('User', back_populates='comments')
    movie_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('movies.id'), nullable=False)
    parent_movie: Mapped[str] = relationship('Movie', back_populates='comments')
    text: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)  # Rating added by user

with app.app_context():
    db.create_all()

# ROUTES

@app.route("/")
def render_main():
    return "<h1>Wow</h1>"

if __name__=="__main__":
    app.run(debug=True, port=5004)