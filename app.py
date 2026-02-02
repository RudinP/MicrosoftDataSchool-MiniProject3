import os
import psycopg2
from psycopg2.extras import DictCursor
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from dotenv import load_dotenv
from datetime import datetime
import json
import folium

# 로컬 환경에서는 .env를 읽고, Azure에서는 패스.
if os.path.exists('.env'):
    load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

# 데이터베이스 연결 함수
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        sslmode='require', #Azure를 위해 반드시 추가
        options='-c timezone=Asia/Seoul'
    )
    print('get_db_connection', conn)
    conn.autocommit = True
    return conn


@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # KPIs
    # 1. Total Stations
    cur.execute("SELECT COUNT(*) FROM miniproject3.station_info")
    total_stations = cur.fetchone()[0]
    
    # 2. Total Boarding Count (Latest Date)
    cur.execute("SELECT SUM(boarding_count) FROM miniproject3.station_boarding")
    total_boarding = cur.fetchone()[0]
    
    # 3. Total Restaurants
    cur.execute("SELECT COUNT(*) FROM miniproject3.restaurant_info")
    total_restaurants = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', 
                           total_stations=total_stations, 
                           total_boarding=total_boarding, 
                           total_restaurants=total_restaurants)

@app.route('/map')
def map_view():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Fetch station location and total boarding info
    query = """
    SELECT 
        si.station_name, 
        si.line_name, 
        si.latitude, 
        si.longitude, 
        COALESCE(SUM(sb.boarding_count), 0) as total_boarding
    FROM miniproject3.station_info si
    LEFT JOIN miniproject3.station_boarding sb 
        ON si.station_name = sb.station_name AND si.line_name = sb.line_name
    GROUP BY si.station_name, si.line_name, si.latitude, si.longitude
    """
    cur.execute(query)
    stations = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Create Map centered on Seoul
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
    
    for station in stations:
        if station['latitude'] and station['longitude']:
             # CircleMarker size based on boarding count
            radius = min(station['total_boarding'] / 100000, 20) 
            radius = max(radius, 3) # minimum size
            
            folium.CircleMarker(
                location=[station['latitude'], station['longitude']],
                radius=radius,
                popup=f"{station['station_name']} ({station['line_name']}): {station['total_boarding']:,} Boarding",
                color='blue',
                fill=True,
                fill_color='blue'
            ).add_to(m)
            
    map_html = m._repr_html_()
    return render_template('map.html', map_html=map_html)

@app.route('/api/stats')
def api_stats():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Top 10 Stations by Boarding
    cur.execute("""
        SELECT station_name, SUM(boarding_count) as total 
        FROM miniproject3.station_boarding 
        GROUP BY station_name 
        ORDER BY total DESC 
        LIMIT 10
    """)
    top_stations = cur.fetchall()
    
    # Restaurant Types
    cur.execute("""
        SELECT business_type_name, COUNT(*) as count 
        FROM miniproject3.restaurant_info 
        GROUP BY business_type_name
        ORDER BY count DESC
    """)
    restaurant_types = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        'top_stations': [{'name': row['station_name'], 'value': row['total']} for row in top_stations],
        'restaurant_types': [{'name': row['business_type_name'], 'value': row['count']} for row in restaurant_types]
    })

if __name__ == '__main__':
    app.run(debug=True)

