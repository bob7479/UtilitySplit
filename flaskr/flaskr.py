import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'

))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.execute('insert into users (username, password) values (?, ?)',
               (app.config['USERNAME'], app.config['PASSWORD']))    
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select title, text from entries order by id desc')
    entries = cur.fetchall()
    # print(entries)
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',
               [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

# @app.route('/signup', methods=['POST'])
# def signup():
# 	db = get_db()
# 	db.execute('insert into users (username, password) values (?, ?',
# 				request.form['username'], request.form['password'])
# 	db.commit()
# 	flash('New user successfully added')
# 	return redirect(url_for('show_entries'))
@app.route('/login', methods=['GET', 'POST'])
def login():
	db = get_db()
	username = request.form['username']
	password = request.form['password']
	validLogin = db.execute('select * from users where username = ?', (username,))
	validPassword = db.execute('select * from users where password = ?', (password,))
	
	cur = db.execute('select username, password from users order by id desc')
	entries = cur.fetchall()
	print entries
	# print validLogin
	# print validPassword
	error = None
	if request.method == 'POST':
	    if validLogin == None:
	        error = 'Invalid username'
	    elif validPassword == None:
	        error = 'Invalid password'
	    else:
	        session['logged_in'] = True
	        flash('You were logged in')
	        return redirect(url_for('show_entries'))
	return render_template('login.html', error=error)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error = None
#     if request.method == 'POST':
#         if request.form['username'] != app.config['USERNAME']:
#             error = 'Invalid username'
#         elif request.form['password'] != app.config['PASSWORD']:
#             error = 'Invalid password'
#         else:
#             session['logged_in'] = True
#             flash('You were logged in')
#             return redirect(url_for('show_entries'))
#     return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))