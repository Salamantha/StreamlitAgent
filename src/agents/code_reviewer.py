from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def review_and_suggest_improvements(code_text):
    prompt = f"""
You are a Streamlit improvement agent.

Here is the current Streamlit code:
{code_text}
 
For each csv there is ("descriptions") to visialize the data and ("recommandations") to make charts

Your task:
- Rewrite the Streamlit code to include the recommended charts / KPIs.
- Keep it clean and readable.
- Also avoid ValueError: Cannot pass a datetime or Timestamp with tzinfo with the tz parameter. Use tz_convert instead.  happens here: axess_df['ts_utc'] >= pd.Timestamp(start_ts, tz='UTC'))
- file paths are under data/name.csv
- Return output **as a Python dict** with keys:
  "patch": full improved Streamlit code
"""

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": prompt}]
    )

    return eval(response.choices[0].message.content)
