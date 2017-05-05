import os
basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
CSRF_ENABLED = True
SECRET_KEY = "SUPER SECRET KEY"

RECAPTCHA_PUBLIC_KEY = 'publickey'
RECAPTCHA_PRIVATE_KEY = 'very secretive'

SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password@localhost/TestDB'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
