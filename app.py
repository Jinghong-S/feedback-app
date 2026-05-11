from flask import Flask, request, jsonify, render_template
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # 允许跨域请求

DB_FILE = 'feedback.db'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# 默认访问，显示门店提交页面
@app.route('/')
def index():
    return render_template('submit.html')

# 访问 /dashboard 显示管理层看板
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# 接口：接收门店提交的反馈数据
@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    store_name = data.get('store_name')
    content = data.get('content')
    
    if not store_name or not content:
        return jsonify({'status': 'error', 'message': '缺少数据'}), 400
    
    # 将数据存入数据库
    with get_db() as conn:
        conn.execute('INSERT INTO feedback (store_name, content) VALUES (?, ?)', (store_name, content))
        conn.commit()
    return jsonify({'status': 'success'})

# 接口：为看板提供统计数据
@app.route('/api/report', methods=['GET'])
def get_report():
    with get_db() as conn:
        # 统计每个门店的反馈总数
        cursor = conn.execute('SELECT store_name, COUNT(*) as count FROM feedback GROUP BY store_name')
        counts = [{'store_name': row['store_name'], 'count': row['count']} for row in cursor.fetchall()]
        
        # 获取最新提交的10条反馈
        cursor = conn.execute('SELECT store_name, content, created_at FROM feedback ORDER BY id DESC LIMIT 10')
        recent = [{'store_name': row['store_name'], 'content': row['content'], 'time': row['created_at']} for row in cursor.fetchall()]
        
    return jsonify({'counts': counts, 'recent': recent})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8011)
