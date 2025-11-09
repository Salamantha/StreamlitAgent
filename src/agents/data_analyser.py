import pandas as pd
import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()  # Loads .env variables into environment
client = OpenAI()  # Automatically picks up OPENAI_API_KEY

def analyze_data(data_folder):
    summaries = {}
    
    for file in os.listdir(data_folder):
        if file.endswith('.csv'):
            path = os.path.join(data_folder, file)
            df = pd.read_csv(path)

            structure = f"Columns: {df.columns.tolist()}\n"
            structure += "Sample rows:\n" + df.head().to_csv(index=False)

            prompt = f"""
        You are a data analysis agent. The user has provided the following dataset sample:

        {structure}

        Your tasks:
        1. Describe what the dataset likely represents.
        2. Suggest visualization components for a Streamlit dashboard.
        Components allowed: table, line_chart, bar_chart, scatter_plot, kpi
        Also avoid ValueError: Cannot pass a datetime or Timestamp with tzinfo with the tz parameter. Use tz_convert instead.  happens here:axess_df['ts_utc'] >= pd.Timestamp(start_ts, tz='UTC'))
        Give a possible description of what the data might display and change the column names if you find better ones.
        3. Return response **as a Python dict literal**, e.g.:

        
        "description": "...",
        "recommendations": [
            "component": "table",
            "component": "line_chart", "x": "date", "y": "value"
        ]
        
"""

            response = client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": prompt}]
            )

            summaries[file] = json.loads(response.choices[0].message.content)

    return summaries
