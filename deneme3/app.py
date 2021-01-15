from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, SelectField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps




app = Flask(__name__)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# Articles
@app.route('/adverts')
def adverts():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM advert")
    adverts = cur.fetchall()

    if result > 0:
        return render_template('adverts.html', adverts=adverts)

    else:
        msg = 'No Articles Found'
        return render_template('adverts.html', msg=msg)
    # Close connection
    cur.close()


#Single Article
@app.route('/advert/<string:id>/')
def advert(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM advert WHERE id = %s", [id])
    advert = cur.fetchone()
    result2 = cur.execute("SELECT * FROM comments WHERE advert_id = %s", [id])
    comments = cur.fetchall()
    
    if result2 > 0:
        return render_template('advert.html', advert=advert, comments=comments)
        

    return render_template('advert.html', advert=advert)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.DataRequired(),validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.DataRequired(),validators.Length(min=2, max=25)])
    email = StringField('Email', [validators.DataRequired(),validators.Length(min=5, max=50)])
    usertype = SelectField(u'User Type', choices=[('Band', 'Band'), ('Musician', 'Musician') ])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        usertype = form.usertype.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username,usertype, password) VALUES(%s, %s, %s, %s, %s)", (name, email, username,usertype, password))

        mysql.connection.commit()

        cur.close()

        flash('You are successfully registered.', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('Logged in', 'success')
                return redirect(url_for('profile'))
            else:
                error = 'Please try again.'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You must login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('login'))

# Profile
@app.route('/profile')
@is_logged_in
def profile():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    #result = cur.execute("SELECT * FROM advert")
    # Show articles only from the user logged in 
    result = cur.execute("SELECT * FROM advert WHERE author = %s", [session['username']])

    adverts = cur.fetchall()

    result2 = cur.execute("SELECT * FROM biography WHERE username = %s", [session['username']])
    biography = cur.fetchall()
    

    if result > 0:
        return render_template('profile.html', adverts=adverts, biography=biography)
    else:
        msg = 'No Adverts Found'
        return render_template('profile.html', msg=msg)
    # Close connection
    cur.close()

# Article Form Class
class AdvertForm(Form):
    title = StringField('Title', [validators.DataRequired(),validators.Length(min=1, max=200)])
    location = StringField('Location', [validators.DataRequired(),validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.DataRequired(),validators.Length(min=20)])

class CommentForm(Form):
    body = TextAreaField('Body', [validators.DataRequired(),validators.Length(min=5)])

# Add Article
@app.route('/add_advert', methods=['GET', 'POST'])
@is_logged_in
def add_advert():
    form = AdvertForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        location = form.location.data
        body = form.body.data

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO advert(title, location, body, author) VALUES(%s, %s, %s, %s)",(title, location, body, session['username']))

        mysql.connection.commit()

        cur.close()

        flash('Advert Published', 'success')

        return redirect(url_for('profile'))

    return render_template('add_advert.html', form=form)


# Edit Article
@app.route('/edit_advert/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_advert(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM advert WHERE id = %s", [id])

    advert = cur.fetchone()
    cur.close()
    # Get form
    form = AdvertForm(request.form)

    # Populate article form fields
    form.title.data = advert['title']
    form.location.data = advert['location']
    form.body.data = advert['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        location = request.form['location']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE advert SET title=%s, location=%s, body=%s WHERE id=%s",(title, location, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Advert Updated', 'success')

        return redirect(url_for('profile'))

    return render_template('edit_advert.html', form=form)

@app.route('/add_comment/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def add_comment(id):
    
    form = CommentForm(request.form)
    
    if request.method == 'POST' and form.validate():

        body = form.body.data

        cur = mysql.connection.cursor()
    
        cur.execute("INSERT INTO comments(author, advert_id, body) VALUES(%s, %s, %s)",(session['username'], id, body))
  
        mysql.connection.commit()

        cur.close()

        flash('Comment Published', 'success')

        return redirect(url_for('advert', id = id))

    return render_template('add_comment.html', form=form)

    from app.forms import EditProfileForm

class EditProfileForm(Form):

    instrument = StringField('Instrument',[validators.DataRequired(),validators.Length(min=0, max=50)])
    exp_level = SelectField(u'Experience Level', choices=[('beginner', 'beginner'),('intermediate', 'intermediate'), ('pro', 'pro') ])
    location = StringField('Location',[validators.DataRequired(),validators.Length(min=0, max=50)])
    body = TextAreaField('About me', [validators.DataRequired(),validators.Length(min=0, max=300)])


# Add Article
@app.route('/edit_profile/', methods=['GET', 'POST'])
@is_logged_in
def edit_profile():
    form = EditProfileForm(request.form)

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM biography WHERE username = %s", [session['username']])
    cur.close()
    if result > 0:
        if request.method == 'POST' and form.validate():
            instrument = form.instrument.data
            exp_level = form.exp_level.data
            location = form.location.data
            body = form.body.data
            cur = mysql.connection.cursor()
            cur.execute ("UPDATE biography SET instrument=%s, exp_level=%s, location=%s, body=%s WHERE username=%s",(instrument, exp_level, location, body, session['username']))

            mysql.connection.commit()

            cur.close()

            flash('Profile updated.', 'success')

            return redirect(url_for('profile'))

    else:
        if request.method == 'POST' and form.validate():
            instrument = form.instrument.data
            exp_level = form.exp_level.data
            location = form.location.data
            body = form.body.data
            cur = mysql.connection.cursor()

            cur.execute("INSERT INTO biography(username, instrument, exp_level, location, body) VALUES(%s, %s, %s, %s, %s)",(session['username'],instrument,exp_level, location, body))

            mysql.connection.commit()

            cur.close()

            flash('Profile updated.', 'success')

            return redirect(url_for('profile'))

    return render_template('edit_profile.html', form=form)

    
# Delete Article
@app.route('/delete_advert/<string:id>', methods=['POST'])
@is_logged_in
def delete_advert(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM advert WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Advert Deleted', 'success')

    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
