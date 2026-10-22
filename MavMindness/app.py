from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import json

app = Flask(__name__)
DATABASE = 'mavmindness.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    conn = get_db_connection()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS mood_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mood TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Check which columns already exist
    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(mood_entries)"
        ).fetchall()
    }

    # Add the stress column if it doesn't exist
    if "stress" not in columns:
        conn.execute(
            "ALTER TABLE mood_entries ADD COLUMN stress INTEGER"
        )

    # Add the sleep column if it doesn't exist
    if "sleep" not in columns:
        conn.execute(
            "ALTER TABLE mood_entries ADD COLUMN sleep REAL"
        )

    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_mood', methods=['POST'])
def submit_mood():
    data = request.get_json(silent=True) or request.form
    mood = data.get('mood')
    stress = data.get('stress')
    sleep = data.get('sleep')

    if not mood:
        return jsonify({'error': 'Mood is required'}), 400

    try:
        stress = int(stress) if stress is not None else None
        sleep = float(sleep) if sleep is not None else None
    except ValueError:
        return jsonify({'error': 'Stress must be an integer and sleep must be a number'}), 400

    if stress is not None and (stress < 1 or stress > 10):
        return jsonify({'error': 'Stress must be between 1 and 10'}), 400

    if sleep is not None and (sleep < 0 or sleep > 24):
        return jsonify({'error': 'Sleep must be a number between 0 and 24'}), 400  

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO mood_entries (mood, stress, sleep) VALUES (?, ?, ?)', (mood, stress, sleep))

    conn.commit()
    conn.close()

    result = [dict(entry) for entry in cursor.execute('SELECT * FROM mood_entries ORDER BY timestamp DESC LIMIT 1')]

    if request.is_json:
        return jsonify(result[0]), 200

    return redirect(url_for('index'))

@app.route('/get_latest_mood', methods=['GET'])
def get_latest_mood():
    conn = get_db_connection()
    entry = conn.execute('SELECT * FROM mood_entries ORDER BY timestamp DESC LIMIT 1').fetchone()
    conn.close()

    if entry is None:
        return jsonify({'error': 'No mood entries found'}), 404

    return jsonify(dict(entry)), 200

@app.route('/get_mood_data', methods=['GET'])
def get_mood_data():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM mood_entries ORDER BY timestamp DESC').fetchall()
    conn.close()

    return jsonify({row['mood']: row['count'] for row in rows}), 200

@app.route('/get_mood_entries', methods=['GET'])
def get_mood_entries():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM mood_entries ORDER BY timestamp DESC').fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows]), 200

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)