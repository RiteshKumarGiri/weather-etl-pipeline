import pandas as pd
import requests
import logging
import os
from sqlalchemy import create_engine,text
from urllib.parse import quote_plus
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

db_password = os.getenv("DB_PASSWORD")
db_user = os.getenv("DB_USER")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

def extract(latitude,longitude):
    try:
        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m",
            "forecast_days": 1,
            "timezone" :"Asia/Kolkata"
        }       
        response = requests.get(url,params=params)
        response.raise_for_status()        
        data = response.json()

        hourly_data = data['hourly']
        df = pd.DataFrame(hourly_data)
        logging.info(f"Extracted {len(df)} rows from weather API")
        # print(df.head())
        # print(df.shape)
        return df
    except Exception as e:
        logging.error(f'Api extraction failed : {e}')
        raise
    

def transform(df):
    try:
        # Step 1: convert time column to datetime
        df['time'] = pd.to_datetime(df['time'])
        #Step 2: compute summary stats
        max_temp = df['temperature_2m'].max()
        min_temp = df['temperature_2m'].min()
        avg_temp = round(df['temperature_2m'].mean(), 2)
        
        # summary dataFrame
        summary_df = pd.DataFrame([
            {
                "Date" : df['time'].dt.date.iloc[0], #date part from the first row only
                "max_temp" :max_temp, 
                "min_temp" :min_temp,
                "avg_temp" :avg_temp
            }
        ])
        logging.info(f"Data transformed successfully max temp : {max_temp}, min temp : {min_temp} and avg temp : {avg_temp}")
        return df,summary_df
    except Exception as e:
        logging.error(f'Data not transformed: {e}')
        raise
    
def load(hourly_df,daily_df,engine  ):
    try:
        
        # for weather daily
        today = daily_df['Date'].iloc[0]
        try:
            existing = pd.read_sql(f"select * from weather_daily where \"Date\" = '{today}'",engine)
        except:
            existing = []
            
        if len(existing)>0:
            with engine.connect() as conn:
                conn.execute(text(f"delete from weather_daily where \"Date\" = '{today}'"))
                conn.commit()
            daily_df.to_sql('weather_daily',engine,if_exists='append', index=False)
            # hourly_df.to_sql('weather_hourly',engine,if_exists='append', index=False)
            logging.info(f"Updated existing weather_daily record for {today}")
        else:
            daily_df.to_sql('weather_daily',engine,if_exists='append', index=False)
            # hourly_df.to_sql('weather_hourly',engine,if_exists='append', index=False)
            logging.info(f"Inserted new weather_daily record for {today}")
            
        # for weather hourly
        try:
            existing1 = pd.read_sql(f"select * from weather_hourly where time::date = '{today}'",engine)
        except:
            existing1 = []
            
        if len(existing1)>0:
            with engine.connect() as conn:
                conn.execute(text(f"delete from weather_hourly where time::date = '{today}'"))
                conn.commit()
            hourly_df.to_sql('weather_hourly',engine,if_exists='append', index=False)
            logging.info(f"Updated existing weather_hourly record for {today}")
        else:
            hourly_df.to_sql('weather_hourly',engine,if_exists='append', index=False)
            logging.info(f"Inserted new weather_hourly record for {today}")
        return
    except Exception as e:
        logging.error(f'Data not loaded successfully :- {e}')
        raise
    

if __name__ == "__main__" :
    try:
        password = db_password
        encoded_pass = quote_plus(password)
        engine = create_engine(f'postgresql+psycopg://{db_user}:{encoded_pass}@{db_host}:{db_port}/{db_name}')
        
        raw_df = extract(28.44,77.33)
        hourly_df,daily_df = transform(raw_df)
        load(hourly_df,daily_df,engine)
        logging.info(f'Pipeline Completed Successfully')
    except Exception as e:
        logging.error(f'Pipeline failed : {e}')
        raise

