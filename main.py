from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float
from flask_login import login_required, login_user, logout_user, UserMixin, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from forms import FindMovieForm, LoginForm, SignUpForm, PostCommentForm
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
    img_url: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    contributor_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'), nullable=False)
    contributor: Mapped["User"] = relationship("User", back_populates="movies_added")
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
def home():
    movies = db.session.execute(db.select(Movie)).scalars()
    return render_template('index.html', movies=movies)

@app.route("/add", methods=["POST", "GET"])
def add_movie():
    find_movie_form = FindMovieForm()
    if request.method=="POST" and find_movie_form.validate_on_submit():
        title = find_movie_form.name.data
        response = requests.get(API_SEARCH_URL, params={"api_key": API_KEY, "query":title})
        data = response.json()["results"]
        return render_template("find_movie.html", data=data)
    return render_template("add_movie.html", form=find_movie_form)

@app.route("/select", methods=["POST", "GET"])
def select():
    movie_api_id = request.args.get('id')
    movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
    response = requests.get(movie_api_url, params={"api_key": API_KEY, "language": "en-US"})
    data = response.json()
    new_movie = Movie(
        title=data["title"],
        year=data["release_date"].split("-")[0],
        img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
        description=data["overview"]
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect('/')

@app.route('/delete/<movie_id>')
def delete(movie_id):
    selected_movie = db.session.execute(db.select('Movie').where(Movie.id==movie_id)).scalar()
    db.session.delete(selected_movie)
    db.session.commit()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True, port=5004)