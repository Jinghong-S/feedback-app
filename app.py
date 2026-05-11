from flask import Flask, request, jsonify, render_template, Response
import sqlite3
from flask_cors import CORS
import csv
from io import StringIO

app = Flask(__name__)
CORS(app)

DB_FILE = 'feedback_v2.db'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            channel TEXT NOT NULL,
            region TEXT NOT NULL,
            store_name TEXT NOT NULL,
            trend TEXT NOT NULL,
            reason TEXT NOT NULL,
            detail TEXT,
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
    period = data.get('period', 'Unknown Period')
    channel = data.get('channel', '')
    region = data.get('region', '')
    store_name = data.get('store_name')
    trend = data.get('trend')
    reason = data.get('reason')
    detail = data.get('detail', '')
    
    if not store_name or not reason:
        return jsonify({'status': 'error', 'message': '缺少必填数据'}), 400
    
    with get_db() as conn:
        conn.execute('''
            INSERT INTO feedback (period, channel, region, store_name, trend, reason, detail) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (period, channel, region, store_name, trend, reason, detail))
        conn.commit()
    return jsonify({'status': 'success'})

@app.route('/api/report', methods=['GET'])
def get_report():
    with get_db() as conn:
        cursor = conn.execute('SELECT * FROM feedback ORDER BY id DESC LIMIT 50')
        rows = cursor.fetchall()
        recent = []
        for r in rows:
            recent.append({
                'time': r['created_at'],
                'period': r['period'],
                'channel': r['channel'],
                'store_name': r['store_name'],
                'trend': r['trend'],
                'reason': r['reason'],
                'detail': r['detail'] if r['detail'] else ''
            })
    return jsonify({'recent': recent})

@app.route('/api/export', methods=['GET'])
def export_feedback():
    with get_db() as conn:
        cursor = conn.execute('SELECT period, channel, region, store_name, trend, reason, detail, created_at FROM feedback ORDER BY id DESC')
        rows = cursor.fetchall()
    
    si = StringIO()
    si.write('\ufeff') # 写入 UTF-8 BOM 头，确保 Excel 打开不乱码
    cw = csv.writer(si)
    # Excel 的表头
    cw.writerow(['周期', '渠道', '大区', '门店名称', '趋势', '反馈原因', '具体解释', '提交时间'])
    for r in rows:
        cw.writerow([r['period'], r['channel'], r['region'], r['store_name'], r['trend'], r['reason'], r['detail'], r['created_at']])
        
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=Store_Feedback_Data.csv"}
    )

if __name__ == '__main__':
    get_db().close()
    app.run(host='0.0.0.0', port=8011)
