import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
scheduler = BackgroundScheduler()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24))
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Add FMP API key to config
app.config["FMP_API_KEY"] = os.environ.get("FMP_API_KEY", "")
app.config["FMP_API_BASE_URL"] = "https://financialmodelingprep.com/api/v3"

# Initialize the app with extensions
db.init_app(app)

# Start the scheduler
scheduler.start()

with app.app_context():
    # Import models to ensure they are registered with SQLAlchemy
    import models  # noqa: F401

    # Create tables if they don't exist
    db.create_all()
    
    # Import scheduler jobs after models are created
    from scheduler import register_jobs
    register_jobs(scheduler)
    
    logging.info("Application initialized with database and scheduler")
