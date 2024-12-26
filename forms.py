from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField
from wtforms.validators import DataRequired, URL, Email, NumberRange
from flask_ckeditor import CKEditorField

class SignUpForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label='Sign Up')

class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label='Log In')

class PostCommentForm(FlaskForm):
    text = CKEditorField(label="Your Comment", validators=[DataRequired()])
    rating = IntegerField("Your Rating", validators=[DataRequired(), NumberRange(min=0, max=10, message="Rating must be between 0 and 10")])
    submit = SubmitField(label='Post')

class FindMovieForm(FlaskForm):
    name = StringField(label="Movie Name", validators=[DataRequired()])
    submit = SubmitField(label='Search')

