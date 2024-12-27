from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Integer, String, Float
from flask_login import login_required, login_user, logout_user, UserMixin, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from forms import FindMovieForm, LoginForm, SignUpForm, PostCommentForm
from flask_ckeditor import CKEditor
from os import getenv
from datetime import date
from psycopg2 import *
import requests


# APP & KEYS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = getenv("DB_URI")
app.config['SECRET_KEY'] = getenv("SECRET_KEY")

API_KEY = getenv('API_KEY')
API_SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

# INITIALISE THE DB

db = SQLAlchemy(app)

# CKEditor
ckeditor = CKEditor(app)

# LOGIN MANAGER

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# DB | TABLE DATA

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
    contributor = relationship("User", back_populates="movies_added")
    comments = relationship('Comment', back_populates='parent_movie', cascade="all, delete-orphan")  # Remove Mapped[str]
    
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
    comment_author = relationship('User', back_populates='comments')  # Remove Mapped[str]
    movie_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('movies.id'), nullable=False)
    parent_movie = relationship('Movie', back_populates='comments')  # Remove Mapped[str]
    text: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[int] = mapped_column(Integer(), nullable=True)

# with app.app_context():
#     db.create_all()

# ROUTES

@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie)).scalars().all()
    return render_template('index.html', movies=movies, current_user=current_user)

@app.route("/add", methods=["POST", "GET"])
@login_required
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
    try:
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"], 
            contributor_id=current_user.id
        )
        db.session.add(new_movie)
        db.session.commit()
    except IntegrityError:
        flash("You have already added this movie.", "warning")
    return redirect(url_for('home'))

@app.route('/delete/<movie_id>')
@login_required
def delete(movie_id):
    selected_movie = db.session.execute(db.select(Movie).where(Movie.id==movie_id)).scalar()
    db.session.delete(selected_movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/movie/<movie_id>", methods=["POST", "GET"])
def movie(movie_id):
    selected_movie = db.session.execute(db.select(Movie).where(Movie.id==movie_id)).scalar()
    comment_form = PostCommentForm()
    if request.method=="POST" and comment_form.validate_on_submit():
        existing_comment = db.session.execute(
            db.select(Comment).where(
                Comment.author_id == current_user.id,
                Comment.movie_id == selected_movie.id
            )
        ).scalar()

        if existing_comment:
            flash("You have already commented on this movie.", "warning")
        else:
            new_comment = Comment(
                author_id=current_user.id,
                movie_id=selected_movie.id,
                text=request.form["text"],
                rating=request.form["rating"]
            )
            db.session.add(new_comment)
            db.session.commit()
    return render_template("movie.html", movie=selected_movie, form=comment_form)

@app.route("/delete_comment/<comment_id>")
def delete_comment(comment_id):
    selected_comment = db.session.execute(db.select(Comment).where(Comment.id==comment_id)).scalar()
    db.session.delete(selected_comment)
    db.session.commit()
    return redirect(url_for('home'))

# LOGIN / LOGOUT SYSTEMS

@app.route("/signup", methods=["POST", "GET"])
def signup():
    signup_form = SignUpForm()
    if request.method=="POST" and signup_form.validate_on_submit():
        new_user = User(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"], method="pbkdf2:sha256", salt_length=8)
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template('signup.html', form=signup_form)

@app.route("/login", methods=["POST", "GET"])
def login():
    login_form = LoginForm()
    if request.method=="POST" and login_form.validate_on_submit():
        email = request.form["email"]
        password = request.form["password"]
        selected_user = db.session.execute(db.select(User).where(User.email==email)).scalar()
        if selected_user:
            if(check_password_hash(selected_user.password, password)):
                login_user(selected_user)
                return redirect(url_for('home'))
            else:
                flash("Incorrect email or password. Please try again.", "error")
        else:
            flash("The email does not exist. Please try again.", "error")
    return render_template("login.html", form=login_form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(debug=True, port=5004)