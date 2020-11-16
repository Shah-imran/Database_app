from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
import redis
from rq import Queue

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    print(config[config_name].SQLALCHEMY_DATABASE_URI)
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    app.redis = redis.Redis()
    app.worker_q = Queue(connection=app.redis)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .section_1 import section_1
    app.register_blueprint(section_1, url_prefix='/section_1')

    from .section_2 import section_2
    app.register_blueprint(section_2, url_prefix='/section_2')

    from .section_3 import section_3
    app.register_blueprint(section_3, url_prefix='/section_3')


    return app

