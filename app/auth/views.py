from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required
from . import auth
from ..models import User
from .forms import LoginForm, PasswordReset
from .. import config, db


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('Invalid email or password.')
    else:
        flash('Enter email and password')

    return render_template('auth/login.html', form=form)

@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = PasswordReset()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.old_password.data):
            if form.new_password.data == form.new_password_again.data and form.new_password.data!="":
                user.password = form.new_password.data
                db.session.add(user)
                db.session.commit()
                flash("Succesfully changed the password.")
            else:
                flash("Passwords doesn't match.")
        else:
            flash('Invalid email or password.')
    else:
        flash('Fill up all the fields then submit.')

    return render_template('auth/reset_password.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))
