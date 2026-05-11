from flask import Flask, request, jsonify, render_template
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_FILE = 'feedback.db'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # 修复 Bug：在每次连接数据库时，确保表存在。如果不存在（被清空或刚启动）就自动建表。
    conn.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

@app.route('/')
def index():
    return render_template('submit.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    store_name = data.get('store_name')
    content = data.get('content')
    
    if not store_name or not content:
        return jsonify({'status': 'error', 'message': '缺少数据'}), 400
    
    with get_db() as conn:
        conn.execute('INSERT INTO feedback (store_name, content) VALUES (?, ?)', (store_name, content))
        conn.commit()
        
    return jsonify({'status': 'success'})

@app.route('/api/report', methods=['GET'])
def get_report():
    with get_db() as conn:
        cursor = conn.execute('SELECT store_name, COUNT(*) as count FROM feedback GROUP BY store_name')
        counts = [{'store_name': row['store_name'], 'count': row['count']} for row in cursor.fetchall()]
        
        cursor = conn.execute('SELECT store_name, content, created_at FROM feedback ORDER BY id DESC LIMIT 10')
        recent = [{'store_name': row['store_name'], 'content': row['content'], 'time': row['created_at']} for row in cursor.fetchall()]
        
    return jsonify({'counts': counts, 'recent': recent})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8011)
