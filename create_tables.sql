-- Table: station_info
-- Source: 서울 지하철 노선별 역 정보.csv
-- Columns: 역사_ID, 역사명, 호선, 위도, 경도
CREATE TABLE miniproject3.station_info (
    station_id INT PRIMARY KEY,
    station_name VARCHAR(100),
    line_name VARCHAR(50),
    latitude FLOAT,
    longitude FLOAT
);

-- Table: station_address
-- Source: 서울교통공사_역주소.csv
-- Note: Schema inferred/estimated. Please verify columns match the CSV.
CREATE TABLE miniproject3.station_address (
    station_name VARCHAR(100),
    line_name VARCHAR(50),
    road_address VARCHAR(255),
    parcel_address VARCHAR(255)
);

-- Table: station_boarding
-- Source: 역별승하차인원.csv
-- Columns: 사용일자, 노선명, 역명, 승차총승객수, 하차총승객수, 등록일자
CREATE TABLE miniproject3.station_boarding (
    use_date VARCHAR(8), -- Format: YYYYMMDD
    line_name VARCHAR(50),
    station_name VARCHAR(100),
    boarding_count INT,
    alighting_count INT,
    registration_date VARCHAR(8)
);

-- Table: restaurant_info
-- Source: 휴게음식점 인허가 정보.csv
-- Note: Schema based on standard "LocalData" (Saveiro) structure. 
-- Adjust columns if the CSV differs (e.g. fewer columns or different order).
CREATE TABLE miniproject3.restaurant_info (
    -- Common columns in license data
    management_number VARCHAR(100), -- 관리번호
    business_status_name VARCHAR(50), -- 영업상태명
    road_address TEXT,              -- 도로명전체주소
    business_name VARCHAR(200),     -- 사업장명
    business_type_name VARCHAR(100), -- 업태구분명
    x_coordinate FLOAT,             -- 좌표정보(X)
    y_coordinate FLOAT              -- 좌표정보(Y)
);

CREATE OR REPLACE VIEW v_station_summary AS
SELECT
    si.station_id,
    si.station_name,
    si.line_name,
    si.latitude,
    si.longitude,
    sa.road_address

FROM station_info si
LEFT JOIN station_address sa
    ON si.station_name = sa.station_name
   AND si.line_name = sa.line_name
LEFT JOIN station_boarding sb
    ON si.station_name = sb.station_name
   AND si.line_name = sb.line_name;

CREATE OR REPLACE VIEW miniproject3.v_restaurant_with_district AS
SELECT
    management_number,
    business_status_name,
    business_name,
    business_type_name,
    substring(road_address FROM '([가-힣]+구)') AS district
FROM miniproject3.restaurant_info;