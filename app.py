#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys 
import traceback
from datetime import datetime
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import exc, or_ 
from wtforms import ValidationError



#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO-DONE: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable = False)
    city = db.Column(db.String(120), nullable = False)
    state = db.Column(db.String(120), nullable = False)
    address = db.Column(db.String(120), nullable = False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String), nullable = False)
    shows = db.relationship('Show', cascade="all, delete-orphan", backref='venue', lazy=True)

    # genre = db.relationship('Genre', secondary=venue_genre, backref=db.backref('Venue', lazy=True))

    # TODO-DONE: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable = False)
    city = db.Column(db.String(120), nullable = False)
    state = db.Column(db.String(120), nullable = False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable = False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', cascade="all, delete-orphan", backref=db.backref('artist', single_parent=True, cascade="all, delete-orphan"), lazy=True)
    # genre = db.relationship('Genre', secondary=artist_genre, backref=db.backref('Artist', lazy=True))

    # TODO-DONE: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime())
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id',ondelete="CASCADE"), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id',ondelete="CASCADE"), nullable=False)

# TODO-DONE Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  # Implemented Bonus Challenge: Show Recently Listed Artists and Venues
  venue = Venue.query.order_by(Venue.id.desc()).limit(10)
  artist = Artist.query.order_by(Artist.id.desc()).limit(10)
  return render_template('pages/home.html', venues=venue, artists=artist)

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO-DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  
  # get the list of cities (which has venues in DB) to group venues 
  areas = Venue.query.distinct('state', 'city')
  data = []

  for area in areas:
    # Under a specified area, get all venues in it
    venues = Venue.query.filter(Venue.city == area.city, Venue.state == area.state).all()
    for venue in venues:
      shows = Show.query.filter_by(venue_id=venue.id).all()
      upcoming_shows = []
      for show in shows:
        if show.start_time > datetime.now():
          upcoming_shows.append({"show_id": show.id})
          # upcoming_shows = Show.query.join(Venue, Show.venue_id == Venue.id).filter(Show.start_time >= datetime.now()).count()
  
    entry = {
      'city': area.city,
      'state' : area.state,
      'venues' : venues,
      'num_upcoming_shows' : len(upcoming_shows)
    }
    data.append(entry)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO-DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  search_term=request.form.get('search_term', '') # get the requested search term from the user input

  # Implemented the bonus challenge - searching by name, city or state
  venue = Venue.query.filter(or_(Venue.name.ilike('%{}%'.format(search_term)),Venue.city.ilike('%{}%'.format(search_term)),Venue.state.ilike('%{}%'.format(search_term)))).all()
  
  response = {
    "count" : len(venue),
    "data" : venue
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO-DONE: replace with real venue data from the venues table, using venue_id

  venue = Venue.query.filter(Venue.id == venue_id).one_or_none() # get the venue details in list form 
  if venue is None:
    abort(404)
  else:
    data = venue.__dict__ # converting list into dictionary 

    # Get the past shows, and join with Venue & Artist to get their names and details 
    past_shows = Show.query.join(Venue, Show.venue_id == Venue.id).join(Artist, Artist.id == Show.artist_id).add_columns(Show.start_time.label('start_time'), Artist.id.label(
          'artist_id'), Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link')).filter(Show.venue_id == venue_id,Show.start_time < datetime.now())

    past_shows_count = past_shows.count() # Count how many past shows for the venue 

    # Get the upcoming shows, and join with Venue & Artist to get their names and details 
    upcoming_shows = Show.query.join(Venue, Show.venue_id == Venue.id).join(Artist, Artist.id == Show.artist_id).add_columns(Show.start_time.label('start_time'), Artist.id.label(
          'artist_id'), Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link')).filter(Show.venue_id == venue_id,Show.start_time >= datetime.now())
    
    upcoming_shows_count= upcoming_shows.count() # Count how many upcoming shows for the venue 
    
    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = past_shows_count
    data['upcoming_shows_count'] = upcoming_shows_count

  
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO-DONE: insert form data as a new Venue record in the db, instead
  # TODO-DONE: modify data to be the data object returned from db insertion

  form = VenueForm(request.form) 
  if form.validate(): # check the validations defined in forms.py
    try: 
      seeking_talent = False # initialize the variable with a default value 
      seeking_description = '' # initialize the variable with a default value 
      if 'seeking_talent' in request.form: # check the checkbox in form 
            seeking_talent = True
            seeking_description = request.form['seeking_description']
      # submitting the form with the data entered by user
      new_venue = Venue( 
        name=request.form['name'],
        genres=request.form.getlist('genres'),
        address=request.form['address'],
        city=request.form['city'],
        state=request.form['state'],
        phone=request.form['phone'],
        website=request.form['website'],
        facebook_link=request.form['facebook_link'],
        image_link=request.form['image_link'],
        seeking_talent=seeking_talent,
        seeking_description=seeking_description,
      )
      db.session.add(new_venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # Handle exceptions 
    except exc.SQLAlchemyError as e:
      db.session.rollback()
      flash('Error occurred (exc).    Venue ' + request.form['name'] + ' could not be listed.')
    except ValueError:
      db.session.rollback()
      flash('Value Error.    Venue ' + request.form['name'] + ' could not be listed.')
    except:
      db.session.rollback()
      flash('Error occurred. Venue ' +request.form['name'] + ' could not be listed.')
      print(sys.exc_info())
      full_traceback = traceback.format_exc()
      print(full_traceback)
    finally:
      db.session.close() # close connection 
  else: 
      flash('Form validation error.    Venue ' + request.form['name'] + ' could not be listed.')
  # on successful db insert, flash success

  # TODO-DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO-DONE: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue= Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully deleted!')
  # Handle exceptions if venue can't be deleted 
  except:
    db.session.rollback()
    flash('Venue ' + request.form['name'] + ' could not be deleted.')
  finally:
    db.session.close()
  
  # BONUS CHALLENGE - DONE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO-DONE: replace with real data returned from querying the database

  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO-DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  # Implemented the bonus challenge - searching by name, city or state 
  search_term = request.form.get('search_term','')
  artist = Artist.query.filter(or_(Artist.name.ilike('%{}%'.format(search_term)),Artist.city.ilike('%{}%'.format(search_term)),Artist.state.ilike('%{}%'.format(search_term)))).all()
  
  response={
    "count": len(artist),
    "data": artist
  }
  
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO-DONE: replace with real venue data from the venues table, using venue_id

  artist = Artist.query.get(artist_id)
  data = artist.__dict__ # converting list to dictionary 

  # Get the past shows, and join with Venue & Artist to get their names and details 
  past_shows = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Show.venue_id == Venue.id).add_columns(Show.start_time.label('start_time'), Venue.id.label(
        'venue_id'), Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link')).filter(Show.artist_id == artist_id,Show.start_time < datetime.now())

  past_shows_count = past_shows.count()

  # Get the upcoming shows, and join with Venue & Artist to get their names and details 
  upcoming_shows = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Show.venue_id == Venue.id).add_columns(Show.start_time.label('start_time'), Venue.id.label(
        'venue_id'), Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link')).filter(Show.artist_id == artist_id,Show.start_time >= datetime.now())
  
  upcoming_shows_count= upcoming_shows.count()
  
  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = past_shows_count
  data['upcoming_shows_count'] = upcoming_shows_count

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  
  # TODO-DONE: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO-DONE: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm()

  try: 
    # get the new values for editing the entry (if any)
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    if 'seeking_venue' in request.form:
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  # Handle exceptions 
  except ValidationError as e:
    db.session.rollback()
    flash('An error occurred in validation. Artist ' + request.form['name'] + ' could not be updated. ' + str(e))
  except:
    db.session.rollback()
    flash('An error occurred in exception. Artist ' +request.form['name'] + ' could not be updated.')
    print(sys.exc_info())
    full_traceback = traceback.format_exc()
    print(full_traceback)
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)

  # TODO-DONE: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO-DONE: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm()

  try:
    # get the new values for editing the entry (if any)
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.genres = request.form.getlist('genres')
    venue.address = request.form['address']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.phone = request.form['phone']
    venue.website = request.form['website']
    venue.facebook_link = request.form['facebook_link']
    if 'seeking_talent' in request.form:
      venue.seeking_talent = True
    else:
      venue.seeking_talent = False
    venue.seeking_description = request.form['seeking_description']
    venue.image_link = request.form['image_link']
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except ValidationError as e:
    db.session.rollback()
    flash('An error occurred (validation). Venue ' + request.form['name'] + ' could not be updated. ' + str(e))
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' +request.form['name'] + ' could not be updated.')
    print(sys.exc_info())
    full_traceback = traceback.format_exc()
    print(full_traceback)
  finally:
    db.session.close()


  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO-DONE: insert form data as a new Venue record in the db, instead
  # TODO-DONE: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  if form.validate(): # Validate the form using the validations in forms.py
    try: 
      seeking_venue = False
      seeking_description = ''
      if 'seeking_venue' in request.form:
            seeking_venue = True
            seeking_description = request.form['seeking_description']
      new_artist = Artist(
        name=request.form['name'],
        city=request.form['city'],
        state=request.form['state'],
        phone=request.form['phone'],
        genres=request.form.getlist('genres'),
        image_link=request.form['image_link'],
        facebook_link=request.form['facebook_link'],
        website=request.form['website'],
        seeking_venue=seeking_venue,
        seeking_description=seeking_description,
      )
      db.session.add(new_artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')

    except exc.SQLAlchemyError as e:
      db.session.rollback()
      flash('An error occurred (exc). Artist ' + request.form['name'] + ' could not be listed.')
    except:
      db.session.rollback()
      flash('An error occurred. Artist ' +request.form['name'] + ' could not be listed.')
      print(sys.exc_info())
      full_traceback = traceback.format_exc()
      print(full_traceback)
    finally:
      db.session.close()
  else: 
      flash('Form validation error.    Venue ' + request.form['name'] + ' could not be listed.')

  # on successful db insert, flash success
  
  # TODO-DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO-DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # Get the data from models Show,Venue,Artist. link models using join to get all the required fields
  data = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Show.venue_id == Venue.id).add_columns(Venue.id.label('venue_id'), 
  Venue.name.label('venue_name'), Artist.id.label('artist_id'),Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), 
  Show.start_time.label('start_time')).order_by(Show.start_time)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)
  if form.validate(): # Validate the form using validations from forms.py
    try: 
      new_show = Show(
        artist_id=request.form['artist_id'],
        venue_id=request.form['venue_id'],
        start_time=request.form['start_time'],
      )
      db.session.add(new_show)
      db.session.commit()
      flash('Show was successfully listed!')

    except exc.SQLAlchemyError as e:
      db.session.rollback()
      flash('Show could not be listed.')
    except:
      db.session.rollback()
      flash('An error occurred. Show could not be listed.')
      print(sys.exc_info())
      full_traceback = traceback.format_exc()
      print(full_traceback)
    finally:
      db.session.close()

  # on successful db insert, flash success
  
  # TODO-DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
