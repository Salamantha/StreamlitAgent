# Agentic Data Explorer

This project provides an interactive Streamlit dashboard driven by LLM-based data analysis.  
You first run an automated agent to analyze your data, then explore the results in the dashboard.

---

## Requirements

### 1. Install Python
Python 3.9 or higher is recommended.

### 2. (Optional) Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate          # Mac / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set environment variables
Create a `.env` file in the project root containing at least:
```bash
OPENAI_API_KEY=your_key_here
```

---

## Data Setup

Place your CSV files inside the `data/` folder.  
The analysis will only work if this folder contains the datasets you want to explore.

Example:
```
data/
  axess-attersee-1-2025-11-03T07-55-46-data.csv
  bernard-direction-hallstatt-diff-2025-11-03T09-37-29-data.csv
```

---

## Running the Application

### Step 1 — Launch Streamlit
```bash
streamlit run main.py
```

### Step 2 — Run the Analysis
On the main page:
- Click **"Run Agent Analysis"**
- Wait until you see a confirmation message

### Step 3 — Open the Dashboard
Once analysis completes:
- Navigate to the **app** page in the Streamlit sidebar

If the app page shows a warning that analysis is missing, return to the main page and run the analysis.

---

## Project Structure

```
src/
  agents/
    data_analyser.py
    code_reviewer.py
  pages/
    app.py        # Dashboard UI
main.py           # Launch + runs agent analysis
data/             # Place .csv data files here
```

---

## Troubleshooting

| Problem | Solution |
|--------|----------|
| Dashboard says "No analysis found" | Go back to main page and press **Run Agent Analysis** |
| Charts are empty | Ensure your CSV files are correctly formatted and in `data/` |
| KeyError or missing columns | Check column names and timestamp formats |
| API errors | Make sure your `.env` contains a valid OpenAI API key |

---

## License
MIT License
