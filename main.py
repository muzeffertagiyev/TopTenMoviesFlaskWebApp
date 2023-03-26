from flask import Flask, render_template, redirect, url_for, flash, abort, request, jsonify
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import RegisterForm, LoginForm, RateMovieForm, AddMovieForm


# Api for addresses and key for getting data from the movie database api website
MOVIE_DATABASE_API_KEY = "e426388127dc3ada71fcd97938f7c904"
SEARCH_MOVIE_ENDPOINT ="https://api.themoviedb.org/3/search/movie"
GETTING_MOVIE_DETAILS_API = "https://api.themoviedb.org/3/movie/"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)




# LOGIN 
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.unauthorized_handler
def unauthorized():
    # Redirect the user to the login page if they are not authenticated
    flash('You must be logged in to view ,add ,update and delete your movies.')
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# CREATING DATA BASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///new-books-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


with app.app_context():

    class User(UserMixin,db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(200), nullable=False, unique=True)
        email = db.Column(db.String(300), nullable=False, unique=True)
        password = db.Column(db.String(300), nullable=False)
        movies = relationship("Movie", back_populates='user')


    class Movie(db.Model):
        __tablename__ = 'movies'
        id = db.Column(db.Integer, primary_key=True)

        user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
        user = relationship("User", back_populates="movies")

        title = db.Column(db.String(200), nullable=False)
        year = db.Column(db.Integer, nullable=False)
        description = db.Column(db.String(1000), nullable=False)
        rating = db.Column(db.Float)
        ranking = db.Column(db.Integer)
        review = db.Column(db.String(500))
        img_url = db.Column(db.String(500), nullable=False)

    db.create_all()
    """#this is the way to add data into our data base manually
    # new_movie = Movie(
    # title="Phone Booth",
    # year=2002,
    # description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    # rating=7.3,
    # ranking=10,
    # review="My favourite character was the caller.",
    # img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
    # )
    # db.session.add(new_movie)
    # db.session.commit()   
    """
    

@app.route("/")
@login_required
def home():
    current = current_user
    all_movies = Movie.query.filter_by(user_id=current.id).order_by(Movie.rating.desc())
    rank = 1
    for movie in all_movies:
        if movie.rating:
            movie.ranking = rank
            rank += 1
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route('/register/', methods=["GET","POST"])
def register():
    register_form = RegisterForm()

    if register_form.validate_on_submit():

        if User.query.filter_by(name=register_form.name.data).first():
            flash('There is user with the same name. Please enter another name')
            return redirect(url_for('register'))

        if User.query.filter_by(email=register_form.email.data).first():
            flash('You have already signed up with that email.Log in instead')
            return redirect(url_for('login'))

        hashed_and_salted_password = generate_password_hash(
            password=register_form.password.data, 
            method="pbkdf2:sha256",salt_length=8)

        new_user = User(
            name=register_form.name.data,
            email=register_form.email.data,
            password=hashed_and_salted_password
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))


    return render_template("register.html",form=register_form)


@app.route('/login/', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    
    if login_form.validate_on_submit():
        entered_email = login_form.email.data
        entered_password = login_form.password.data
        user = User.query.filter_by(email=entered_email).first()

        if not user :
            flash('That email does not exist,please try again Or Register')
            return redirect(url_for('login'))

        elif not check_password_hash(pwhash=user.password, password=entered_password):
            flash('The password is incorrect,please try again')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))


    return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You logged out.You can login again')
    return redirect(url_for('login'))
    



@app.route('/add_movie/', methods=["GET", "POST"])
@login_required
def add_movie():
    add_form = AddMovieForm()

    if add_form.validate_on_submit():
        movie_name = add_form.title.data
        parameters = {
            "api_key":MOVIE_DATABASE_API_KEY,
            "query":movie_name
        }
        response = requests.get(url=SEARCH_MOVIE_ENDPOINT, params=parameters)
        data = response.json()['results']
        return render_template('select.html', options=data)

    return render_template('add.html', form=add_form)


@app.route('/find/')
@login_required
def find_movie():
    # it gets id when we click to movie name
    movie_id = request.args.get('id')
    if movie_id:
        parameters = {
            "api_key":MOVIE_DATABASE_API_KEY,
            "language":"en-US"
        }
        response = requests.get(url=f"{GETTING_MOVIE_DETAILS_API}{movie_id}", params=parameters)
        data = response.json()
        current = current_user
        new_movie = Movie(
            title=data["title"],
            year = data['release_date'].split('-')[0],
            description=data['overview'],
            img_url=f"https://image.tmdb.org/t/p/w500/{data['poster_path']}",
            user_id = current.id
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))

@app.route('/edit/movie_id/<int:id>', methods=["GET", "POST"])
@login_required
def edit(id):
    edit_form = RateMovieForm()
    movie = Movie.query.get(id)
    if edit_form.validate_on_submit():
        movie.rating = float(edit_form.movie_rating.data)
        movie.review = edit_form.movie_review.data
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('edit.html', form=edit_form, movie=movie)


@app.route('/delete/')
@login_required
def delete_movie():
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
