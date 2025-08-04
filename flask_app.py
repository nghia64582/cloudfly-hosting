# flask_app.py

from flask import Flask, jsonify, request
import mysql.connector
import os
from datetime import datetime
from mysql.connector import Error

app = Flask(__name__)

DB_HOST = 'nghia64582.online'
DB_USER = 'qrucoqmt_nghia64582'
DB_PASSWORD = 'Nghi@131299'
DB_NAME = 'qrucoqmt_nghia64582'

if os.getenv('FLASK_ENV') == 'development':
    DB_HOST = 'nghia64582.online'
    DB_USER = 'qrucoqmt_nghia64582'
    DB_PASSWORD = 'Nghi@131299'
    DB_NAME = 'qrucoqmt_nghia64582'
    print('Enviroment')

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

@app.route("/all_keys")
def all_keys():
    """
    Retrieves all keys from the key_value_store table.
    Returns a JSON list of keys.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "SELECT `key` FROM `key_value_store`"
        cursor.execute(sql)
        keys = [row[0] for row in cursor.fetchall()]

        return jsonify({"status": "success", "keys": keys})

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

def connect_to_database():
    """
    Establishes a single connection to the MySQL database.
    This function is called once when the application starts.
    """
    print("Start connecting to MySQL database...")
    print(f"Using DB_HOST: {DB_HOST}, DB_USER: {DB_USER}, DB_NAME: {DB_NAME}")
    global db_connection, db_cursor
    try:
        db_connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if db_connection.is_connected():
            print("Successfully connected to MySQL database")
            db_cursor = db_connection.cursor(dictionary=True)
        else:
            print("Failed to connect to MySQL database")
            db_connection = None
            db_cursor = None
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        db_connection = None
        db_cursor = None

@app.route('/record', methods=['GET'])
def get_records_by_date_range():
    """
    GET /record?start-time=dd-mm-yyyy&end-time=dd-mm-yyyy
    Fetches all records where created_at is between the specified dates.
    Returns a JSON list of matching records.
    """
    if not db_cursor:
        return jsonify({"error": "Database connection not available."}), 500

    start_time_str = request.args.get('start-time')
    end_time_str = request.args.get('end-time')

    if not start_time_str or not end_time_str:
        return jsonify({"error": "Missing 'start-time' or 'end-time' parameters."}), 400

    try:
        # Convert string dates to a format MySQL can understand (YYYY-MM-DD)
        start_date = datetime.strptime(start_time_str, '%d-%m-%Y').strftime('%Y-%m-%d 00:00:00')
        end_date = datetime.strptime(end_time_str, '%d-%m-%Y').strftime('%Y-%m-%d 23:59:59')
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use 'dd-mm-yyyy'."}), 400

    try:
        sql_query = "SELECT id, name, score, created_at FROM extraunary WHERE created_at BETWEEN %s AND %s"
        db_cursor.execute(sql_query, (start_date, end_date))
        records = db_cursor.fetchall()
        # The cursor is configured to return dictionaries, so no further formatting is needed.
        return jsonify(records), 200
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "An error occurred while fetching records."}), 500

@app.route('/record-by-name', methods=['GET'])
def get_records_by_name():
    """
    GET /record-by-name?name=<name>
    Fetches all records with a specific name.
    Returns a JSON list of matching records.
    """
    if not db_cursor:
        return jsonify({"error": "Database connection not available."}), 500

    name_to_search = request.args.get('name')

    if not name_to_search:
        return jsonify({"error": "Missing 'name' parameter."}), 400

    try:
        sql_query = "SELECT id, name, score, created_at FROM extraunary WHERE name = %s"
        db_cursor.execute(sql_query, (name_to_search,))
        records = db_cursor.fetchall()
        return jsonify(records), 200
    except Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "An error occurred while fetching records."}), 500

@app.route('/record', methods=['POST'])
def add_new_record():
    """
    POST /record
    Adds a new record to the table.
    Expects a JSON body with 'name', 'score', and 'created_at' in 'dd-mm-yyyy' format.
    Returns a success message with the new record's ID.
    """
    if not db_connection or not db_cursor:
        return jsonify({"error": "Database connection not available."}), 500

    data = request.get_json()
    if not data or 'name' not in data or 'score' not in data or 'created_at' not in data:
        return jsonify({"error": "Invalid JSON body. Required fields: 'name', 'score', 'created_at'."}), 400

    name = data['name']
    score = data['score']
    created_at_str = data['created_at']

    try:
        # Convert string date to a datetime object
        created_at_dt = datetime.strptime(created_at_str, '%d-%m-%Y')
    except ValueError:
        return jsonify({"error": "Invalid 'created_at' date format. Please use 'dd-mm-yyyy'."}), 400
    
    # Ensure score is an integer
    try:
        score = int(score)
    except ValueError:
        return jsonify({"error": "'score' must be an integer."}), 400

    try:
        sql_query = "INSERT INTO extraunary (name, score, created_at) VALUES (%s, %s, %s)"
        db_cursor.execute(sql_query, (name, score, created_at_dt))
        db_connection.commit()
        new_record_id = db_cursor.lastrowid
        return jsonify({"message": "Record added successfully", "id": new_record_id}), 201
    except Error as e:
        print(f"Database error: {e}")
        # Rollback the transaction in case of error
        db_connection.rollback()
        return jsonify({"error": "An error occurred while adding the record."}), 500


connect_to_database()
# This block is for running the app locally during development.
# On cPanel, the web server (like Phusion Passenger) handles running your app.
if __name__ == '__main__':
    app.run(debug=True) # debug=True is for local development only
