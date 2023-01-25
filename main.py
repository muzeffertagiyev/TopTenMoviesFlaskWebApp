from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

# Api for addresses and key for getting data from the movie database api website
MOVIE_DATABASE_API_KEY = "e426388127dc3ada71fcd97938f7c904"
SEARCH_MOVIE_ENDPOINT ="https://api.themoviedb.org/3/search/movie/"
GETTING_MOVIE_DETAILS_API = "https://api.themoviedb.org/3/movie/"


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)


# Creating Modules
class RateMovieForm(FlaskForm):
    movie_rating = StringField(label='Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    movie_review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class AddMovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label='Add movie')


# CREATING DATA BASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///new-books-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


with app.app_context():
    class Movie(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(200), unique=True, nullable=False)
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
def home():
     # The best way to get data 
    all_movies = Movie.query.order_by(Movie.rating).all()
    # all_movies = db.session.query(Movie).all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i

    return render_template("index.html", movies=all_movies)


@app.route('/add_movie/', methods=["GET", "POST"])
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

@app.route('/find')
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
        new_movie = Movie(
            title=data["title"],
            year = data['release_date'].split('-')[0],
            description=data['overview'],
            img_url=f"https://image.tmdb.org/t/p/w500/{data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))

@app.route('/edit/movie_id/<int:id>', methods=["GET", "POST"])
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
def delete_movie():
    movie_id = request.args.get('id')
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
