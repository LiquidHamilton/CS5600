from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import register_user, check_user_login, db

#TESTING

auth = Blueprint('auth', __name__)

# Route for user registration
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        if db.users.find_one({"username": username}):
            flash('Username already exists!', 'danger')
            return redirect(url_for('auth.register'))

        # Register the user
        register_user(username, password)

        # Log the user in by creating a session
        user = db.users.find_one({"username": username})
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']

        flash('Account created successfully!', 'success')
        return redirect(url_for('routes.home'))
    return render_template('register.html')


# Route for user login
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = check_user_login(username, password)

        if user:
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('routes.home'))
        else:
            flash('Login failed! Please check your credentials.', 'danger')

    return render_template('login.html')


# Route for user logout
@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'info')
    return redirect(url_for('auth.login'))

