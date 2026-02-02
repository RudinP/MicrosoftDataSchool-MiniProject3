# 서울시 지하철 유동인구 수와 휴게업소 데이터 시각화

서울시 지하철 역별 유동인구 데이터와 휴게음식점 인허가 정보를 분석하여 시각화하는 웹 애플리케이션입니다.
지하철 이용객 수와 주변 상권(휴게 음식점) 데이터를 결합하여 유의미한 인사이트를 제공합니다.

## 🚀 기술 스택 (Tech Stack)

본 프로젝트는 최신 AI 기술과 클라우드 데브옵스 환경을 적극 활용하여 개발되었습니다.

*   **AI Pair Programming:** **Antigravity Gemini 3 Pro**
    *   개발 전 과정에서 코드 생성, 디버깅, 최적화에 Google의 최신 Agentic AI 모델을 사용하였습니다.
*   **Web Framework:** Python Flask
*   **Database:** PostgreSQL
*   **CI/CD:** **GitHub Actions**
    *   main 브랜치 푸시 시 자동 빌드 및 배포 파이프라인 구축
*   **Deployment:** **Azure Web App**
    *   Azure PaaS 환경을 이용한 안정적인 서비스 호스팅

## 📊 데이터베이스 구조 (Database Schema)

수집된 공공 데이터는 전처리 후 PostgreSQL 데이터베이스에 저장되어 관리됩니다.

### 주요 테이블 (Tables)
*   **`miniproject3.station_info`**:
    *   서울시 지하철 역의 기본 정보 (ID, 역사명, 호선, 위도/경도)를 저장합니다.
*   **`miniproject3.station_address`**:
    *   각 지하철 역의 도로명 주소 및 지번 주소 정보를 저장합니다.
*   **`miniproject3.station_boarding`**:
    *   일자별, 역별 승하차 승객 수 데이터를 저장합니다. (유동인구 분석의 핵심 데이터)
*   **`miniproject3.restaurant_info`**:
    *   서울시 내 휴게음식점의 인허가 정보, 영업 상태(영업/폐업), 좌표 등을 포함합니다.

### 주요 뷰 (Views)
*   **`v_station_summary`**:
    *   역 정보, 주소, 승하차 인원을 결합하여 역별 종합 데이터를 조회하기 쉽게 만든 뷰입니다.
*   **`miniproject3.v_restaurant_with_district`**:
    *   음식점 주소에서 '구(District)' 정보를 추출하여 지역별 통계 분석을 용이하게 만든 뷰입니다.

## 📈 시각화 기능 (Visualizations)

웹 대시보드에서는 다음과 같은 데이터 시각화 정보를 제공합니다.

### 1. 인터랙티브 지도 (Interactive Map) - Folium
서울시 지도를 기반으로 두 가지 레이어를 시각화합니다.
*   **지하철 역 유동인구 (Blue Circles):** 각 역의 위치에 파란 원으로 표시되며, **승하차 승객 수가 많을수록 원의 크기가 커집니다.**
*   **구별 휴게음식점 밀집도 (Red Circles):** 각 구(District)의 중심에 빨간 원으로 표시되며, **해당 구에 위치한 휴게음식점 수가 많을수록 원의 크기가 커집니다.**

### 2. 통계 대시보드 (Dashboard Charts)
*   **지하철 유동인구 TOP 10 역 (Top 10 Stations):** 가장 유동인구가 많은 상위 10개 역을 막대 그래프로 보여줍니다.
*   **구별 지하철 역 분포 (Stations per District):** 각 자치구별로 지하철 역이 얼마나 위치해 있는지 시각화합니다.
*   **유동인구 vs 폐업 음식점 상관관계 (Traffic vs Closed Restaurants):** 지역별 유동인구 수와 폐업한 음식점 수의 관계를 분석하여 보여줍니다.
*   **지역별 트래픽 및 주요 업종 분포 (District Traffic & Top Business Types):** 각 구별 유동인구 규모와 해당 지역에서 가장 흔한 상위 5개 음식점 업종의 분포를 비교합니다.
*   **업종별 비율 (Restaurant Types):** 전체 데이터 내에서 카페, 패스트푸드 등 음식점 업종별 비율을 파이/도넛 차트로 제공합니다.
