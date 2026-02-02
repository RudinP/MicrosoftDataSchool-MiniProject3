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
    
    # 1. Station Data (Traffic & Location) & Extract District
    query_stations = """
    SELECT 
        si.station_name, 
        si.line_name, 
        si.latitude, 
        si.longitude, 
        COALESCE(SUM(sb.boarding_count), 0) as total_boarding,
        substring(sa.road_address FROM '([가-힣]+구)') as district
    FROM miniproject3.station_info si
    LEFT JOIN miniproject3.station_boarding sb 
        ON si.station_name = sb.station_name AND si.line_name = sb.line_name
    LEFT JOIN miniproject3.station_address sa
        ON si.station_name = sa.station_name AND si.line_name = sa.line_name
    GROUP BY si.station_name, si.line_name, si.latitude, si.longitude, sa.road_address
    """
    cur.execute(query_stations)
    stations = cur.fetchall()
    
    # 2. Restaurant Count by District (using the View)
    query_restaurants = """
    SELECT district, COUNT(*) as cnt 
    FROM miniproject3.v_restaurant_with_district 
    WHERE district IS NOT NULL 
    GROUP BY district
    """
    cur.execute(query_restaurants)
    restaurant_counts = {row['district']: row['cnt'] for row in cur.fetchall()}

    # Calculate District Centroids for Restaurant Bubbles
    district_coords = {}
    district_stat_counts = {}
    
    for s in stations:
        d = s['district']
        if d:
            if d not in district_coords:
                district_coords[d] = {'lat': 0, 'lon': 0, 'count': 0}
            district_coords[d]['lat'] += s['latitude']
            district_coords[d]['lon'] += s['longitude']
            district_coords[d]['count'] += 1
            
    for d in district_coords:
        district_coords[d]['lat'] /= district_coords[d]['count']
        district_coords[d]['lon'] /= district_coords[d]['count']
    
    cur.close()
    conn.close()
    
    # Create Map centered on Seoul
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
    
    # Layer 1: Subway Stations (Blue) - Size ~ Traffic
    for station in stations:
        if station['latitude'] and station['longitude']:
            # Radius scaling
            radius = min(station['total_boarding'] / 50000, 15) 
            radius = max(radius, 2)
            
            folium.CircleMarker(
                location=[station['latitude'], station['longitude']],
                radius=radius,
                popup=f"{station['station_name']}: {station['total_boarding']:,}명 (유동인구)",
                color='#3388ff',
                fill=True,
                fill_color='#3388ff',
                fill_opacity=0.6,
                tooltip=f"{station['station_name']} 유동인구"
            ).add_to(m)

    # Layer 2: District Restaurants (Red) - Size ~ Restaurant Count
    for district, coords in district_coords.items():
        count = restaurant_counts.get(district, 0)
        if count > 0:
            # Radius scaling
            radius = min(count / 1000, 40)
            radius = max(radius, 5)
            
            folium.CircleMarker(
                location=[coords['lat'], coords['lon']],
                radius=radius,
                popup=f"{district}: {count:,}개소 (음식점)",
                color='#ff3333',
                fill=True,
                fill_color='#ff3333',
                fill_opacity=0.4,
                tooltip=f"{district} 음식점 수"
            ).add_to(m)
            
    map_html = m._repr_html_()
    return render_template('map.html', map_html=map_html)

@app.route('/api/advanced_stats')
def api_advanced_stats():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Data 1: Stations per District
    cur.execute("""
        SELECT substring(road_address FROM '([가-힣]+구)') as district, COUNT(*) as cnt
        FROM miniproject3.station_address
        WHERE road_address IS NOT NULL
        GROUP BY district
        ORDER BY cnt DESC
    """)
    stations_per_district = cur.fetchall()
    
    # Data 2: Closed Restaurants vs Traffic by District
    # Join logic: District extracted from both sides
    cur.execute("""
        WITH district_traffic AS (
            SELECT 
                substring(sa.road_address FROM '([가-힣]+구)') as district,
                SUM(sb.boarding_count + sb.alighting_count) as total_traffic
            FROM miniproject3.station_info si
            JOIN miniproject3.station_address sa ON si.station_name = sa.station_name AND si.line_name = sa.line_name
            JOIN miniproject3.station_boarding sb ON si.station_name = sb.station_name AND si.line_name = sb.line_name
            GROUP BY district
        ),
        district_closed_restaurants AS (
            SELECT district, COUNT(*) as closed_cnt
            FROM miniproject3.v_restaurant_with_district
            WHERE business_status_name = '폐업'
            GROUP BY district
        )
        SELECT 
            dt.district,
            dt.total_traffic,
            COALESCE(dcr.closed_cnt, 0) as closed_cnt
        FROM district_traffic dt
        JOIN district_closed_restaurants dcr ON dt.district = dcr.district
    """)
    closed_vs_traffic = cur.fetchall()
    
    # Data 3: Top Business Types by District (Correlation traffic vs type)
    # Simplified: Get Top 5 types overall, then count per district
    cur.execute("""
        SELECT business_type_name 
        FROM miniproject3.v_restaurant_with_district 
        GROUP BY business_type_name 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    """)
    top_types = [row[0] for row in cur.fetchall()]
    
    # Get counts per district for these top types + Traffic
    # This query might be complex, doing it in Python post-processing might be easier if dataset small, 
    # but let's try SQL for key metrics.
    # Actually, let's just send Traffic and Type Counts per district to frontend.
    
    type_columns = ", ".join([f"COUNT(CASE WHEN business_type_name = '{t}' THEN 1 END) as \"{t}\"" for t in top_types])
    
    cur.execute(f"""
        WITH district_traffic AS (
            SELECT 
                substring(sa.road_address FROM '([가-힣]+구)') as district,
                SUM(sb.boarding_count) as total_boarding
            FROM miniproject3.station_info si
            JOIN miniproject3.station_address sa ON si.station_name = sa.station_name AND si.line_name = sa.line_name
            JOIN miniproject3.station_boarding sb ON si.station_name = sb.station_name AND si.line_name = sb.line_name
            GROUP BY district
        ),
        district_types AS (
            SELECT district, {type_columns}
            FROM miniproject3.v_restaurant_with_district
            WHERE district IS NOT NULL
            GROUP BY district
        )
        SELECT 
            dt.district,
            dt.total_boarding,
            dt2.*
        FROM district_traffic dt
        JOIN district_types dt2 ON dt.district = dt2.district
        ORDER BY dt.total_boarding DESC
    """)
    traffic_vs_types = cur.fetchall() # Returns district, traffic, district_again, type1, type2...
    
    cur.close()
    conn.close()
    
    # Format traffic_vs_types
    formatted_traffic_types = []
    for row in traffic_vs_types:
        item = {
            'district': row['district'],
            'traffic': row['total_boarding'],
            'types': {t: row[t] for t in top_types}
        }
        formatted_traffic_types.append(item)

    return jsonify({
        'stations_per_district': [{'district': r['district'], 'count': r['cnt']} for r in stations_per_district if r['district']],
        'closed_vs_traffic': [{'district': r['district'], 'traffic': r['total_traffic'], 'closed': r['closed_cnt']} for r in closed_vs_traffic if r['district']],
        'traffic_vs_types': formatted_traffic_types
    })

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

