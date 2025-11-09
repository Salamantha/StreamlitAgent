import streamlit as st
import os
from agents.data_analyser import analyze_data
from agents.code_reviewer import review_and_suggest_improvements




def patch_app_file(patch_code: str, app_path: str = "src/pages/app.py"):
    """
    Writes the provided patch code into the app.py file.
    Appends or replaces a specific section if desired.
    """
    if not os.path.exists(app_path):
        st.error(f"{app_path} does not exist!")
        return
    
    try:
        # Read the current app.py
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Option 1: Replace a placeholder in the app.py
        # For example, if you have a marker like:
        # # --PATCH AREA--
        if "# --PATCH AREA--" in content:
            new_content = content.replace("# --PATCH AREA--", patch_code)
        else:
            # Option 2: Append at the end
            new_content = content + "\n\n" + patch_code

        # Write back to app.py
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        st.success(f"Patched {app_path} successfully!")

    except Exception as e:
        st.error(f"Failed to patch {app_path}: {e}")




st.set_page_config(page_title="Agentic Dashboard", layout="wide")

st.title("Welcome to the Agentic Data Explorer")

st.write("Select a dataset and let the LLM agents analyze it. When ready, proceed to the dashboard.")

data_folder = "data"

if "analysis" not in st.session_state:
    st.session_state.analysis = None
    st.session_state.improved = None

if st.button("Run Agent Analysis"):
    st.session_state.analysis = analyze_data(data_folder)
    st.session_state.improved = review_and_suggest_improvements(st.session_state.analysis)
    st.success("Analysis complete. You can now open the dashboard.")
    patch_app_file(st.session_state.improved["patch"])


