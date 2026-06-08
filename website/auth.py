from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from .functions import create_user

auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
def login():
    data = request.form
    return render_template("login.html")

@auth.route('/logout')
def logout():
    return "<p>Logout</p>"

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        upper_char = False
        for char in password1:
            if char.isupper():
                upper_char=True
            
        if len(email) < 5:
            flash('Invalid Email.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(last_name) < 2:
            flash('Last name must be greater than 1 character.', category='error')
        elif not len(password1) >= 8:
            flash('Password must be at least 8 characters', category='error')
        elif not upper_char:
            flash('Password does not contain a capital letter.', category='error')
        elif password1 != password2:
            flash('Passwords do not match.', category='error')
        else:
            create_user(email,first_name,last_name,password1)
            flash('Account successfully created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("signup.html")
