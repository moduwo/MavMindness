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
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mood_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mood TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_mood', methods=['POST'])
def submit_mood():
    mood = request.form.get('mood')
    if mood:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO mood_entries (mood) VALUES (?)', (mood,))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    else:
        return "Mood not provided", 400

@app.route('/get_mood_data', methods=['GET'])
def get_mood_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT mood, COUNT(*) as count FROM mood_entries GROUP BY mood')
    data = cursor.fetchall()
    conn.close()

    mood_data = {row['mood']: row['count'] for row in data}
    return jsonify(mood_data)

@app.route('/get_mood_entries', methods=['GET'])
def get_mood_entries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM mood_entries ORDER BY timestamp DESC')
    entries = cursor.fetchall()
    conn.close()

    entries_list = [{'id': row['id'], 'mood': row['mood'], 'timestamp': row['timestamp']} for row in entries]
    return jsonify(entries_list)

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)