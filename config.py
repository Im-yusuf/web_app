import os

#config settings for the application 
#db location setting aswell 
basedir = os.path.abspath(os.path.dirname(__file__))
SECRET_KEY = 'supersecretkey'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = True
WTF_CSRF_ENABLED = True

