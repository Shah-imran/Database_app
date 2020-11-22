from flask import render_template, redirect, request, url_for, flash, current_app, jsonify
from . import main
from .. import config, db
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime


@main.route('/')
@main.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('section_1.edit'))
    else:
        return redirect(url_for('auth.login'))


@main.route('/section_1')
@login_required
def section_1():
    return render_template('section_1.html')

@main.route('/section_2')
@login_required
def section_2():
    return render_template('section_2.html')

@main.route('/section_3')
@login_required
def section_3():
    return render_template('section_3.html')


