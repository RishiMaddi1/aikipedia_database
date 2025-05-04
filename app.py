from flask import Flask, request, jsonify
import psycopg2
import os
from decimal import Decimal

app = Flask(__name__)

# Replace these with your actual Supabase database credentials
DB_CONFIG = {
    "host": "db.xafjwlnacwbghwjeibwc.supabase.co",
    "dbname": "postgres",  # this is from the end of the URL
    "user": "postgres",
    "password": "N3p4MJeSYUit4Oae",  # replace [YOUR-PASSWORD] with actual password
    "port": 5432
}


def get_db_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG["port"]
    )

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "User registered successfully"}), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "Username already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and user[0] == password:
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_credits', methods=['POST'])
def get_credits():
    data = request.get_json()
    username = data.get("username")

    if not username:
        return jsonify({"error": "Username is required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, money_left FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            user_id, money_left = result
            return jsonify({
                "user_id": str(user_id),
                "money_left": float(money_left)
            }), 200
        else:
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/subtract_credits', methods=['POST'])
def subtract_credits():
    data = request.get_json()
    user_id = data.get("user_id")
    amount = data.get("amount")

    if not user_id or amount is None:
        return jsonify({"error": "user_id and amount are required"}), 400

    try:
        amount_decimal = Decimal(str(amount))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT money_left FROM users WHERE id = %s", (user_id,))
        result = cur.fetchone()

        if not result:
            cur.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404

        current_balance = result[0]

        if current_balance < amount_decimal:
            cur.close()
            conn.close()
            return jsonify({"error": "Insufficient funds"}), 400

        new_balance = current_balance - amount_decimal

        cur.execute("UPDATE users SET money_left = %s WHERE id = %s", (new_balance, user_id))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "message": "Amount subtracted successfully",
            "new_balance": float(new_balance)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
