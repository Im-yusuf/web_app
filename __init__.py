from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os

# initialising extensions
db = SQLAlchemy()
migrate=Migrate()
logs = LoginManager()
# function to initialise the flask app and the db
def initialise_apps():
    app = Flask(__name__, template_folder='templates')
    app.config.from_pyfile('config.py')
 
    db.init_app(app)
    migrate.init_app(app, db)
    logs.init_app(app)
    logs.login_view = 'login'  

    # got an error if i did this before intialisation 
    from app.models import User

    @logs.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id)) 
    
    with app.app_context():
        from . import views
        views.register_routes(app)  
        db.create_all()  #creating the db
    return app
