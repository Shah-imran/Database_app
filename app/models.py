from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager
import datetime
from flask import current_app


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username



class ScrapDate(db.Model):
    __tablename__ = 'scrap_date'
    id = db.Column(db.Integer, primary_key=True)
    dates = db.Column(db.Date)
    research_id = db.Column(db.Integer, db.ForeignKey('research.id'))



class Research(db.Model):
    __tablename__ = 'research'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    linkedin_presence = db.Column(db.Integer, default=0, nullable=False)
    industry = db.Column(db.String(128), default="", nullable=False)
    note = db.Column(db.Text, default="", nullable=False)
    email_format = db.Column(db.String(64), default="", nullable=False)
    format_name = db.Column(db.String(128), default="", nullable=False)
    format_type = db.Column(db.String(128), default="", nullable=False)
    other_email_format = db.Column(db.String(64), default="", nullable=False)
    total_count = db.Column(db.Integer, default=0, nullable=False)
    domain = db.Column(db.String(128), default="", nullable=False)
    research_date = db.Column(db.Date, default=datetime.datetime.utcnow().date, nullable=False)
    scrap_dates = db.relationship('ScrapDate', backref='research', lazy='dynamic')
    # scrap = db.relationship('Scrap', backref='research', lazy='dynamic')
    countries = db.Column(db.Text)

    def __repr__(self):
        return '<Entry %r>' % self.company_name

class Scrap(db.Model):
    __tablename__ = 'scrap'
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(64), default="", index=True, nullable=False)
    email = db.Column(db.String(64), default="", nullable=False)
    first_name = db.Column(db.String(128), default="", nullable=False)
    last_name = db.Column(db.String(128), default="", nullable=False)
    industry = db.Column(db.String(128), default="", nullable=False)
    validity_grade = db.Column(db.String(64), default="", nullable=False)
    link = db.Column(db.Text, default="", nullable=False)
    position = db.Column(db.Text, default="", nullable=False)
    blast_date = db.Column(db.Date, nullable=True)
    # filename = db.Column(db.Text, default="{}.csv".format(str(datetime.datetime.utcnow())), nullable=False)
    upload_date = db.Column(db.Date, default=datetime.datetime.utcnow().date ,nullable=False)
    percentage = db.Column(db.Integer, nullable=False)
    unblasted = db.Column(db.Boolean, default=True, nullable=False)
    sent = db.Column(db.Boolean, default=False, nullable=False)
    delivered = db.Column(db.Boolean, default=False, nullable=False)
    soft_bonus = db.Column(db.Boolean, default=False, nullable=False)
    hard_bonus = db.Column(db.Boolean, default=False, nullable=False)
    opened = db.Column(db.Boolean, default=False, nullable=False)
    unsubscribed = db.Column(db.Boolean, default=False, nullable=False)
    company_name = db.Column(db.Text, index=True, nullable=False)
    # research_id = db.Column(db.Integer, db.ForeignKey('research.id'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
