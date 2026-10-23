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
            stress INTEGER,
            sleep REAL,
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
        stress = int(stress) if stress not in (None, '') else None
        sleep = float(sleep) if sleep not in (None, '') else None
    except (TypeError, ValueError):
        return jsonify({
            'error': 'Stress must be an integer and sleep must be a number'
        }), 400

    if stress is not None and not 1 <= stress <= 10:
        return jsonify({'error': 'Stress must be between 1 and 10'}), 400

    if sleep is not None and not 0 <= sleep <= 24:
        return jsonify({'error': 'Sleep must be between 0 and 24'}), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            '''INSERT INTO mood_entries (mood, stress, sleep)
               VALUES (?, ?, ?)''',
            (mood, stress, sleep)
        )

        # Fetch the inserted row BEFORE closing the connection
        entry = conn.execute(
            '''SELECT id, mood, stress, sleep, timestamp
               FROM mood_entries WHERE id = ?''',
            (cursor.lastrowid,)
        ).fetchone()

        conn.commit()
        result = dict(entry)

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    if request.is_json:
        return jsonify(result), 201

    return redirect(url_for('index'))

@app.route('/latest_checkin', methods=['GET'])
def latest_checkin():
    try: 
        conn = get_db_connection()
        entry = conn.execute(
            'SELECT * FROM mood_entries ORDER BY id DESC LIMIT 1'
        ).fetchone()
    finally:
        conn.close()

    if entry is None:
        return jsonify({'error': 'No mood entries found'}), 404

    return jsonify(dict(entry)), 200

@app.route('/get_mood_data', methods=['GET'])
def get_mood_data():
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT mood, COUNT(*) as count FROM mood_entries GROUP BY mood').fetchall()
    finally:
        conn.close()

    return jsonify({row['mood']: row['count'] for row in rows}), 200

@app.route('/get_mood_entries', methods=['GET'])
def get_mood_entries():
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT * FROM mood_entries ORDER BY id DESC').fetchall()
    finally:
        conn.close()

    return jsonify([dict(row) for row in rows]), 200

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)