import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'UtilitySplit.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('UTILITYSPLIT_SETTINGS', silent=True)

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

# def merge():
#     db = get_db()
#     cur = db.execute('select username, billname from users')
#     db.execute('join users_bills on users_bills.username = users.username')
#     db.execute('join bills on bills.billname = users_bills.billname')
    
@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/show_bills')
def show_bills():
    db = get_db()
    cur = db.execute('select username, billname, category, frequency, cost from bills order by username desc')
    bills = cur.fetchall()
    return render_template('show_bills.html', entries=bills)

@app.route('/add_bill', methods=['GET','POST'])
def add_bill():
    if not session.get('logged_in'):
        abort(401)
    if request.method == 'POST':
        db = get_db()
        db.execute('insert into users_bills (username, billname, paid) values (?, ?, ?)',
               [app.config['USERNAME'], request.form['billname'], False])
        db.execute('insert into bills (username, billname, category, frequency, cost) values (?, ?, ?, ?, ?)',
               [app.config['USERNAME'], request.form['billname'], request.form['category'], \
               request.form['frequency'], request.form['cost']])
        db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('show_bills'))
    return render_template('add_bill.html')

@app.route('/show_people', methods=['GET'])
def show_people():
    db = get_db()
    people = db.execute('select username from users order by username') 
    people_list = people.fetchall()

    people_bills = db.execute('select username from users_bills order by username').fetchall()

    return render_template('show_people.html', people=people_list, bills = people_bills)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = query_db('select * from users where username = ?',[request.form['username']])
        password = query_db('select * from users where password = ?', [request.form['password']])
        if user == []:
            error = 'Invalid username'
        elif password == []:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            app.config['USERNAME'] = request.form['username']
            app.config['PASSWORD'] = request.form['password']
            return redirect(url_for('show_bills'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))

@app.route('/change', methods=['GET', 'POST'])
def change():
    if request.method == 'POST':
        app.config['PASSWORD'] = request.form['password']
        db = get_db()
        db.execute('update users set password = ? where username = ?', [app.config['PASSWORD'], app.config['USERNAME']])
        db.commit()
        flash('Password successfully changed')
        return redirect(url_for('show_bills'))
    return render_template('change.html')


@app.route('/', methods=['GET', 'POST'])
def add_user():
    error = None
    if request.method == 'POST':
        db = get_db()
        user = query_db('select * from users where username = ?',[request.form['username']])
        if user == []:
            db.execute('insert into users (username, password) values (?, ?)', [request.form['username'], \
                request.form['password']])
            db.commit()
            app.config['USERNAME'] = request.form['username']
            app.config['PASSWORD'] = request.form['password']
            session['logged_in'] = True
            flash('New user was successfully added and logged in')
            return redirect(url_for('show_bills'))
        else:
            error = 'Username already taken'
    return render_template('add_user.html', error = error)
