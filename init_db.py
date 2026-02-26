import psycopg2
from psycopg2 import sql
import config

def init_db():
    """
    Initialize the database structure for bank risk management.
    Ensures PostGIS extension is enabled and creates the necessary tables.
    """
    try:
        # 1. Connect to the default 'postgres' database to create our target database if it doesn't exist
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            dbname="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{config.DB_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database {config.DB_NAME}...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(config.DB_NAME)))
        else:
            print(f"Database {config.DB_NAME} already exists.")
        
        cursor.close()
        conn.close()

        # 2. Connect to the specific database to create tables
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            dbname=config.DB_NAME
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Enable PostGIS extension
        print("Enabling PostGIS extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

        # Create the results table
        print("Creating table bank_risk_results...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS bank_risk_results (
            id SERIAL PRIMARY KEY,
            case_id VARCHAR(50) NOT NULL, -- 关联任务ID
            region_code VARCHAR(50),      -- 区域代码 (Mzs)
            segment_index INTEGER,        -- 岸段序号 (1, 2...)
            segment_name VARCHAR(100),    -- 完整名称 (Mzs_Seg006_...)
            run_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 计算时间
            risk_level INTEGER,           -- 风险等级
            indicators JSONB,             -- 子指标详情 (JSON)
            geom GEOMETRY(LineString, 4326) -- 空间几何 (WGS84)
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_bank_results_region ON bank_risk_results(region_code);
        CREATE INDEX IF NOT EXISTS idx_bank_results_geom ON bank_risk_results USING GIST(geom);
        """
        cursor.execute(create_table_sql)
        
        print("Database initialization completed successfully.")
        
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    init_db()
