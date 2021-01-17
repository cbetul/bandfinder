from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, SelectField, PasswordField, validators
from flask_login import login_user, logout_user, current_user, login_required
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/adverts')
def adverts():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM advert")
    adverts = cur.fetchall()
    result2 = cur.execute("SELECT COUNT(title) AS total FROM advert")
    total_ad = cur.fetchone()
    if result > 0:
        return render_template('adverts.html', adverts=adverts, total_ad=total_ad)

    else:
        msg = 'No Advert Found'
        return render_template('adverts.html', msg=msg)
    cur.close()




@app.route('/user/<string:username>/')
def get_user(username):
  
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
    user = cur.fetchone()
    result3 = cur.execute("SELECT * FROM advert WHERE author = %s", [username])
    adverts = cur.fetchall()

    result3 = cur.execute("SELECT * FROM biography WHERE username = %s", [username])
    biography = cur.fetchall()

    return render_template('user.html', user=user, adverts=adverts,biography=biography )
    cur.close()

@app.route('/bands')
def bands():
    
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM users WHERE usertype = %s", ['Band'])
    bands = cur.fetchall()
    result2 = cur.execute("SELECT COUNT(id) AS total FROM users WHERE usertype = %s", ['Band'])
    total_band = cur.fetchone()

    if result > 0:
        return render_template('bands.html', bands=bands, total_band=total_band)

    else:
        msg = 'No Bands Found'
        return render_template('bands.html', msg=msg)
   
    cur.close()

@app.route('/musicians')
def musicians():
    
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM users WHERE usertype = %s", ['Musician'])
    musicians = cur.fetchall()

    result2 = cur.execute("SELECT COUNT(id) AS total FROM users WHERE usertype = %s", ['Musician'])
    total_musician = cur.fetchone()


    if result > 0:
        return render_template('musicians.html', musicians=musicians, total_musician=total_musician)

    else:
        msg = 'No Musician Found'
        return render_template('musicians.html', msg=msg)
   
    cur.close()

@app.route('/advert/<string:id>/')
def advert(id):
    
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM advert WHERE id = %s", [id])
    advert = cur.fetchone()
    result2 = cur.execute("SELECT * FROM comments WHERE advert_id = %s", [id])
    comments = cur.fetchall()
    result2 = cur.execute("SELECT COUNT(id) AS total FROM comments WHERE advert_id = %s", [id])
    total_comments = cur.fetchone()
    
    if result2 > 0:
        return render_template('advert.html', advert=advert, comments=comments, total_comments=total_comments)
        
    return render_template('advert.html', advert=advert)


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
        exists= cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if exists> 0:
            error = 'Username is already exists!'
            return render_template('register.html', error=error,form=form)
            
        else:
            cur.execute("INSERT INTO users(name, email, username,usertype, password) VALUES(%s, %s, %s, %s, %s)", (name, email, username,usertype, password))

            mysql.connection.commit()

            cur.close()

            flash('You are successfully registered.', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
     
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
       
            data = cur.fetchone()
            password = data['password']

            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash('Logged in', 'success')
                return redirect(url_for('profile'))
            else:
                error = 'Please try again.'
                return render_template('login.html', error=error)
         
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You must login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('login'))


@app.route('/profile')
@is_logged_in
def profile():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM advert WHERE author = %s", [session['username']])
    adverts = cur.fetchall()

    result3 = cur.execute("SELECT COUNT(id) AS total FROM advert WHERE author = %s", [session['username']])
    total_posts = cur.fetchone()

    result2 = cur.execute("SELECT * FROM biography WHERE username = %s", [session['username']])
    biography = cur.fetchall()
    
    if result > 0:
        return render_template('profile.html', adverts=adverts, biography=biography, total_posts=total_posts)
    else:
        return render_template('profile.html', biography=biography, total_posts=total_posts)
  
    cur.close()

class AdvertForm(Form):
    title = StringField('Title', [validators.DataRequired(),validators.Length(min=1, max=200)])
    location = StringField('Location', [validators.DataRequired(),validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.DataRequired(),validators.Length(min=20)])

class CommentForm(Form):
    body = TextAreaField('Body', [validators.DataRequired(),validators.Length(min=5)])
    location = StringField('Location', [validators.DataRequired(),validators.Length(min=1, max=100)])

@app.route('/add_advert/', methods=['GET', 'POST'])
@is_logged_in
def add_advert():
    form = AdvertForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        location = form.location.data
        body = form.body.data

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT id FROM users WHERE username = %s", [session['username']])
        user = cur.fetchone()
        user_id = user['id']
        cur.execute("INSERT INTO advert(title, location, body, author, user_id) VALUES(%s, %s, %s, %s, %s)",(title, location, body, session['username'],user_id))

        mysql.connection.commit()

        cur.close()

        flash('Advert Published', 'success')

        return redirect(url_for('profile'))

    return render_template('add_advert.html', form=form)


@app.route('/edit_advert/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_advert(id):
   
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM advert WHERE id = %s", [id])

    advert = cur.fetchone()
    cur.close()
   
    form = AdvertForm(request.form)

    form.title.data = advert['title']
    form.location.data = advert['location']
    form.body.data = advert['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        location = request.form['location']
        body = request.form['body']

        cur = mysql.connection.cursor()
        app.logger.info(title)
        
        cur.execute ("UPDATE advert SET title=%s, location=%s, body=%s WHERE id=%s",(title, location, body, id))
        
        mysql.connection.commit()

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
        location = form.location.data
        cur = mysql.connection.cursor()

        result = cur.execute("SELECT id FROM users WHERE username = %s", [session['username']])
        user = cur.fetchone()
        user_id = user['id']
    
        cur.execute("INSERT INTO comments(author, advert_id, body, user_id,location) VALUES(%s, %s, %s, %s, %s)",(session['username'], id, body, user_id, location))
  
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
    result2 = cur.execute("SELECT id FROM users WHERE username = %s", [session['username']])
    user = cur.fetchone()
    user_id = user['id']
    cur.close()
    if result > 0:
        if request.method == 'POST' and form.validate():
            instrument = form.instrument.data
            exp_level = form.exp_level.data
            location = form.location.data
            body = form.body.data
            cur = mysql.connection.cursor()
            cur.execute ("UPDATE biography SET instrument=%s, exp_level=%s, location=%s, body=%s, user_id=%s WHERE username=%s",(instrument, exp_level, location, body,user_id, session['username']))

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

            cur.execute("INSERT INTO biography(username, instrument, exp_level, location, body, user_id) VALUES(%s, %s, %s, %s, %s, %s)",(session['username'],instrument,exp_level, location, body, user_id))

            mysql.connection.commit()

            cur.close()

            flash('Profile updated.', 'success')

            return redirect(url_for('profile'))

    return render_template('edit_profile.html', form=form)


@app.route('/delete_biography/<string:id>', methods=['POST'])
@is_logged_in
def delete_biography(id):
   
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM biography WHERE id = %s", [id])

    mysql.connection.commit()

    cur.close()

    flash('Biography Deleted', 'success')

    return redirect(url_for('profile'))

@app.route('/delete_user/<string:username>', methods=['POST'])
@is_logged_in
def delete_user(username):
   
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM users WHERE username = %s", [username])

    mysql.connection.commit()

    cur.close()

    flash('User Deleted', 'success')

    return redirect(url_for('logout'))

class EditUserForm(Form):

    name = StringField('Name', [validators.DataRequired(),validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.DataRequired(),validators.Length(min=5, max=50)])
    usertype = SelectField(u'User Type', choices=[('Band', 'Band'), ('Musician', 'Musician') ])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/edit_user/<string:username>', methods=['GET', 'POST'])
def edit_user(username):
    form = EditUserForm(request.form)
    cur = mysql.connection.cursor()
    result2 = cur.execute("SELECT id FROM users WHERE username = %s", [username])
    user = cur.fetchone()
    user_id = user['id']    
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data  
        usertype = form.usertype.data
        password = sha256_crypt.encrypt(str(form.password.data))
        cur.execute("UPDATE users SET name=%s, email=%s, password=%s,username=%s, usertype=%s WHERE id=%s",(name, email,password,username,usertype, user_id))
        mysql.connection.commit()

        cur.close()

        flash('Your informations updated.', 'success')

        return redirect(url_for('profile'))
    return render_template('edit_user.html', form=form)


@app.route('/delete_comment/<string:id>', methods=['POST'])
@is_logged_in
def delete_comment(id):
   
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM comments WHERE id = %s", [id])

    comment = cur.fetchone()
    advert_id = comment['advert_id']
    cur.execute("DELETE FROM comments WHERE id = %s", [id])

    mysql.connection.commit()

    cur.close()

    flash('Comment Deleted', 'success')

    return redirect(url_for('advert', id = advert_id))

@app.route('/edit_comment/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_comment(id):
   
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM comments WHERE id = %s", [id])

    comment = cur.fetchone()
    advert_id = comment['advert_id']
    cur.close()
   
    form = CommentForm(request.form)

    form.location.data = comment['location']
    form.body.data = comment['body']

    if request.method == 'POST' and form.validate():
        location = request.form['location']
        body = request.form['body']

        cur = mysql.connection.cursor()
        
        cur.execute ("UPDATE comments SET location=%s, body=%s WHERE id=%s",(location, body, id))
        
        mysql.connection.commit()

        cur.close()

        flash('Comment Updated', 'success')

        return redirect(url_for('advert', id = advert_id))

    return render_template('edit_comment.html', form=form)


@app.route('/all_users')
def all_users():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT users.id, users.name, users.usertype, biography.location, biography.instrument FROM biography INNER JOIN users ON biography.user_id=users.id")
    users = cur.fetchall()

    result2 = cur.execute("SELECT COUNT(usertype) as total, usertype FROM users GROUP BY usertype")
    types = cur.fetchall()

    return render_template('all_users.html',users=users, types=types)
    cur.close()

@app.route('/all_posts')
def all_posts():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM advert UNION SELECT * FROM comments")
    posts = cur.fetchall()
    return render_template('all_posts.html',posts=posts)
    cur.close()

@app.route('/all_comments')
def all_comments():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT comments.id, users.usertype, advert.location FROM comments INNER JOIN users ON comments.user_id=users.id INNER JOIN advert ON comments.advert_id=advert.id")
    comments = cur.fetchall()
    return render_template('all_comments.html',comments=comments)
    cur.close()

@app.route('/all_ads')
def all_ads():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT advert.id, advert.location, users.name, users.usertype FROM advert INNER JOIN users ON advert.user_id=users.id")
    ads = cur.fetchall()
    return render_template('all_ads.html',ads=ads)
    cur.close()

@app.route('/delete_advert/<string:id>', methods=['POST'])
@is_logged_in
def delete_advert(id):
   
    cur = mysql.connection.cursor()

    
    cur.execute("DELETE FROM advert WHERE id = %s", [id])

  
    mysql.connection.commit()

   
    cur.close()

    flash('Advert Deleted', 'success')

    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
