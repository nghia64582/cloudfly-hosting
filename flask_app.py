# flask_app.py

from flask import Flask, jsonify, request # Import request to get data from incoming requests
import mysql.connector # Import the MySQL Connector library
import os # To potentially read environment variables

app = Flask(__name__)

# --- Database Configuration ---
# IMPORTANT: For production, store these in environment variables or a secure config file.
# For simplicity in this example, they are hardcoded.
# Replace with your actual cPanel database credentials.
DB_HOST = 'localhost' # Often 'localhost' on cPanel, but check your hosting provider
DB_USER = 'bxnalgz_nghia64582' # e.g., 'myuser_mydbuser'
DB_PASSWORD = 'Nghi@131299'
DB_NAME = 'bxnalgz_nghia64582-db' # e.g., 'myuser_mydbname'

# Example of how you might get credentials from environment variables (recommended for production):
# DB_HOST = os.environ.get('DB_HOST', 'localhost')
# DB_USER = os.environ.get('DB_USER', 'default_user')
# DB_PASSWORD = os.environ.get('DB_PASSWORD', 'default_password')
# DB_NAME = os.environ.get('DB_NAME', 'default_db')


# Helper function to get a database connection
def get_db_connection():
    """Establishes and returns a new database connection."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# Define the root route as before
@app.route('/')
def hello_world():
    """
    Returns a simple greeting message.
    """
    return 'Hello, World!'

# Route to test database connection
@app.route('/db_test')
def db_test():
    """
    Attempts to connect to the MySQL database and fetch the MySQL server version.
    Returns the version or an error message.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()") # Execute a simple query
            db_version = cursor.fetchone() # Fetch the result

            if db_version:
                return jsonify({
                    "status": "success",
                    "message": "Successfully connected to database!",
                    "mysql_version": db_version[0]
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Connected but could not fetch database version."
                }), 500
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to connect to the database."
            }), 500

    except mysql.connector.Error as err:
        return jsonify({
            "status": "error",
            "message": f"Database connection error: {err}",
            "error_code": err.errno
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred: {e}"
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# New route to create the key_value_store table
@app.route('/create_table', methods=['GET'])
def create_table():
    """
    Creates the 'key_value_store' table if it doesn't already exist.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS `key_value_store` (
            `id` INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY, -- Added AUTO_INCREMENT and PRIMARY KEY
            `key` VARCHAR(255) NOT NULL UNIQUE, -- Increased length and added UNIQUE constraint for 'key'
            `value` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL, -- Changed to utf8mb4 for broader character support
            KEY `key_index` (`key`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; -- Changed engine to InnoDB for better transaction support
        """
        cursor.execute(create_table_sql)
        conn.commit() # Commit the changes to the database

        return jsonify({
            "status": "success",
            "message": "Table 'key_value_store' created or already exists."
        })

    except mysql.connector.Error as err:
        conn.rollback() # Rollback in case of error
        return jsonify({
            "status": "error",
            "message": f"Error creating table: {err}",
            "error_code": err.errno
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred: {e}"
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Route to store a key-value pair (create or update)
@app.route('/store/<string:key>', methods=['POST', 'PUT'])
def store_value(key):
    """
    Stores a new key-value pair or updates an existing one.
    Expects a JSON body with 'value' field: {"value": "your_value_here"}
    """
    data = request.get_json()
    if not data or 'value' not in data:
        return jsonify({"status": "error", "message": "Missing 'value' in request body."}), 400

    value = data['value']
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if key already exists
        cursor.execute("SELECT `key` FROM `key_value_store` WHERE `key` = %s", (key,))
        existing_key = cursor.fetchone()

        if existing_key:
            # Update existing value
            sql = "UPDATE `key_value_store` SET `value` = %s WHERE `key` = %s"
            cursor.execute(sql, (value, key))
            message = "Key-value pair updated successfully."
        else:
            # Insert new key-value pair
            sql = "INSERT INTO `key_value_store` (`key`, `value`) VALUES (%s, %s)"
            cursor.execute(sql, (key, value))
            message = "Key-value pair stored successfully."

        conn.commit()
        return jsonify({"status": "success", "message": message, "key": key, "value": value})

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({
            "status": "error",
            "message": f"Database operation error: {err}",
            "error_code": err.errno
        }), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Route to retrieve a value by key
@app.route('/retrieve/<string:key>', methods=['GET'])
def retrieve_value(key):
    """
    Retrieves the value associated with a given key.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "SELECT `value` FROM `key_value_store` WHERE `key` = %s"
        cursor.execute(sql, (key,))
        result = cursor.fetchone()

        if result:
            return jsonify({"status": "success", "key": key, "value": result[0]})
        else:
            return jsonify({"status": "error", "message": f"Key '{key}' not found."}), 404

    except mysql.connector.Error as err:
        return jsonify({
            "status": "error",
            "message": f"Database query error: {err}",
            "error_code": err.errno
        }), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Route to delete a key-value pair
@app.route('/delete/<string:key>', methods=['DELETE'])
def delete_value(key):
    """
    Deletes a key-value pair from the store.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "DELETE FROM `key_value_store` WHERE `key` = %s"
        cursor.execute(sql, (key,))
        conn.commit()

        if cursor.rowcount > 0:
            return jsonify({"status": "success", "message": f"Key '{key}' deleted successfully."})
        else:
            return jsonify({"status": "error", "message": f"Key '{key}' not found or already deleted."}), 404

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({
            "status": "error",
            "message": f"Database deletion error: {err}",
            "error_code": err.errno
        }), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

@app.route("/hello")
def index():
    return "Hello, World! This is 2.0"

@app.route("/ip")
def show_ip():
    """
    Retrieves and displays the client's IP address.
    It attempts to get the IP from X-Forwarded-For header (common for proxies/load balancers)
    and falls back to request.remote_addr.
    """
    # Check for X-Forwarded-For header, which is typically used by proxies (like those in cPanel)
    # to pass the original client's IP address.
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    # If there are multiple IPs in X-Forwarded-For (e.g., comma-separated list), take the first one.
    if ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()

    return jsonify({
        "status": "success",
        "message": "Your IP address is:",
        "ip_address": ip_address
    })

# This block is for running the app locally during development.
# On cPanel, the web server (like Phusion Passenger) handles running your app.
if __name__ == '__main__':
    app.run(debug=True) # debug=True is for local development only
