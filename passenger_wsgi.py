# passenger_wsgi.py

import os
import sys

# Define the path to your application's directory.
# This assumes passenger_wsgi.py is in the same directory as flask_app.py
sys.path.insert(0, os.path.dirname(__file__))

# Import the 'app' Flask application instance from your 'flask_app' module.
# The 'app' object itself is the WSGI callable for Flask applications.
from flask_app import app

# For Phusion Passenger (which cPanel often uses), the WSGI callable is typically
# expected to be named 'application'. So, we assign our Flask 'app' to 'application'.
application = app