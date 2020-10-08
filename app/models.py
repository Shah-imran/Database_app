from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager
import datetime


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
    company_name = db.Column(db.String(128), unique=True, index=True)
    linkedin_presence = db.Column(db.Integer)
    industry = db.Column(db.String(128))
    note = db.Column(db.Text)
    email_format = db.Column(db.String(64))
    format_name = db.Column(db.String(128))
    format_type = db.Column(db.String(128))
    other_email_format = db.Column(db.String(64))
    total_count = db.Column(db.Integer)
    domain = db.Column(db.String(128), unique=True, index=True)
    research_date = db.Column(db.Date)
    scrap_dates = db.relationship('ScrapDate', backref='research', lazy='dynamic')
    countries = db.Column(db.Text)

    def __repr__(self):
        return '<Entry %r>' % self.company_name


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
