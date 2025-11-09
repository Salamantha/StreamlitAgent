

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path
from datetime import date, timedelta

st.set_page_config(page_title="Telemetry Dashboard", layout="wide")
st.title("Telemetry Dashboard")

DATA_DIR = Path("data")
FILES = {
    "Axess Attersee telemetry": DATA_DIR / "axess-attersee-1-2025-11-03T07-55-46-data.csv",
    "Bernard Hallstatt diff": DATA_DIR / "bernard-direction-hallstatt-diff-2025-11-03T09-37-29-data.csv",
}

@st.cache_data(show_spinner=False)
def load_axess(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Rename to clearer names
    rename_map = {"installationId": "site_id", "timestamp": "ts_utc", "value": "metric"}
    df = df.rename(columns=rename_map)
    # Parse timestamps as timezone-aware UTC
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True, errors="coerce")
    # Ensure numeric metric
    df["metric"] = pd.to_numeric(df["metric"], errors="coerce")
    # Drop rows with bad timestamps
    df = df.dropna(subset=["ts_utc"]).sort_values("ts_utc").reset_index(drop=True)
    # Derivations
    df["ts_local"] = df["ts_utc"].dt.tz_convert("Europe/Vienna")
    df["date"] = df["ts_utc"].dt.date
    df["hour"] = df["ts_utc"].dt.hour
    return df

@st.cache_data(show_spinner=False)
def load_bernard(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    rename_map = {"installationId": "installation_id", "timestamp": "ts_utc", "value": "diff"}
    df = df.rename(columns=rename_map)
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True, errors="coerce")
    df["diff"] = pd.to_numeric(df["diff"], errors="coerce")
    df = df.dropna(subset=["ts_utc"]).sort_values("ts_utc").reset_index(drop=True)
    df["ts_local"] = df["ts_utc"].dt.tz_convert("Europe/Vienna")
    df["date"] = df["ts_utc"].dt.date
    return df


def fill_gaps_15min(df: pd.DataFrame, time_col: str, group_col: str, value_cols: list[str]) -> pd.DataFrame:
    if df.empty:
        return df
    out = []
    for key, g in df.groupby(group_col):
        g = g.set_index(time_col).sort_index()
        # Resample ~15-minute grid; keep all value columns
        r = g[value_cols].resample("15T").mean()
        # Bring back the group column value
        r[group_col] = key
        r = r.reset_index()
        out.append(r)
    filled = pd.concat(out, ignore_index=True)
    # Preserve local/time-derived helpers if present
    if "ts_local" in df.columns:
        try:
            filled["ts_local"] = filled[time_col].dt.tz_convert("Europe/Vienna")
        except Exception:
            pass
    if "hour" in df.columns and value_cols[0] == "metric":
        filled["hour"] = filled[time_col].dt.hour
    if "date" in df.columns:
        filled["date"] = filled[time_col].dt.date
    return filled

with st.sidebar:
    dataset = st.radio("Dataset", list(FILES.keys()))
    show_local_time = st.toggle("Show local time (Europe/Vienna)", value=False, help="Only affects chart/table display; data stays in UTC internally.")

if dataset == "Axess Attersee telemetry":
    df = load_axess(FILES[dataset])
    if df.empty:
        st.warning("No data loaded for Axess.")
        st.stop()

    # Filters
    site_options = sorted(df["site_id"].astype(str).unique()) if "site_id" in df.columns else []
    selected_sites = st.sidebar.multiselect("Site(s)", site_options, default=site_options)

    min_d, max_d = df["date"].min(), df["date"].max()
    default_range = (min_d, max_d)
    picked_range = st.sidebar.date_input("Date range (UTC dates)", value=default_range, min_value=min_d, max_value=max_d)
    if isinstance(picked_range, tuple):
        start_date, end_date = picked_range
    else:
        start_date, end_date = picked_range, picked_range
    # Ensure proper order
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    fill_gaps = st.sidebar.checkbox("Fill missing ~15 min intervals (charts only)", value=False)

    # Apply filters using date (avoids tz pitfalls)
    filtered = df.copy()
    if selected_sites:
        filtered = filtered[filtered["site_id"].astype(str).isin(selected_sites)]
    filtered = filtered[(filtered["date"] >= start_date) & (filtered["date"] <= end_date)]

    if filtered.empty:
        st.info("No rows match the current filters.")
        st.stop()

    # Optionally fill gaps for smoother charts
    chart_df = fill_gaps_15min(filtered, "ts_utc", "site_id", ["metric"]) if fill_gaps else filtered

    time_col = "ts_local" if show_local_time else "ts_utc"

    # KPIs
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    # Latest metric
    latest_val = filtered.sort_values("ts_utc").groupby("site_id")["metric"].last()
    if len(selected_sites) == 1:
        kpi_col1.metric("Latest metric", f"{latest_val.iloc[0]:,.2f}" if not latest_val.empty else "—")
    else:
        kpi_col1.metric("Latest metric (avg across selected sites)", f"{latest_val.mean():,.2f}" if not latest_val.empty else "—")
    # Daily total over range
    total_val = filtered["metric"].sum()
    kpi_col2.metric("Total in range", f"{total_val:,.0f}")
    # Active ratio
    active_ratio = float((filtered["metric"] > 0).mean()) if len(filtered) else 0.0
    kpi_col3.metric("Active ratio", f"{active_ratio*100:.1f}%")

    st.subheader("Metric over time")
    line = alt.Chart(chart_df).mark_line(point=False).encode(
        x=alt.X(f"{time_col}:T", title="Time"),
        y=alt.Y("metric:Q", title="Metric"),
        color=alt.Color("site_id:N", title="Site"),
        tooltip=["site_id:N", alt.Tooltip(f"{time_col}:T", title="Time"), alt.Tooltip("metric:Q", format=",.2f")],
    ).properties(height=320)
    st.altair_chart(line, use_container_width=True)

    # Daily aggregates (sum)
    st.subheader("Daily aggregates (sum)")
    daily = filtered.groupby(["date", "site_id"], as_index=False)["metric"].sum()
    bar = alt.Chart(daily).mark_bar().encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("metric:Q", title="Total"),
        color=alt.Color("site_id:N", title="Site"),
        tooltip=["site_id:N", alt.Tooltip("date:T", title="Date"), alt.Tooltip("metric:Q", title="Total", format=",.0f")],
    ).properties(height=260)
    st.altair_chart(bar, use_container_width=True)

    # Time-of-day pattern (scatter with jitter)
    st.subheader("Time-of-day pattern")
    tod_df = filtered.copy()
    if show_local_time:
        tod_df["hour"] = tod_df["ts_local"].dt.hour
    else:
        tod_df["hour"] = tod_df["ts_utc"].dt.hour
    # Add light jitter
    rng = np.random.default_rng(0)
    tod_df["hour_jitter"] = tod_df["hour"] + rng.normal(0, 0.2, size=len(tod_df))
    scatter = alt.Chart(tod_df).mark_circle(opacity=0.6).encode(
        x=alt.X("hour_jitter:Q", title="Hour of day"),
        y=alt.Y("metric:Q", title="Metric"),
        color=alt.Color("site_id:N", title="Site"),
        tooltip=["site_id:N", "hour:Q", alt.Tooltip("metric:Q", format=",.2f"), alt.Tooltip(f"{time_col}:T", title="Sample time")],
    ).properties(height=300)
    st.altair_chart(scatter, use_container_width=True)

    # Recent readings table
    st.subheader("Recent readings")
    display_cols = ["site_id", time_col, "metric"]
    recent = filtered.sort_values("ts_utc", ascending=False).head(200).copy()
    recent = recent.rename(columns={time_col: "timestamp"})
    st.dataframe(recent[["site_id", "timestamp", "metric"]], use_container_width=True)

else:
    df = load_bernard(FILES[dataset])
    if df.empty:
        st.warning("No data loaded for Bernard diff.")
        st.stop()

    # Filters
    inst_options = sorted(df["installation_id"].astype(str).unique()) if "installation_id" in df.columns else []
    selected_insts = st.sidebar.multiselect("Installation(s)", inst_options, default=inst_options)

    min_d, max_d = df["date"].min(), df["date"].max()
    default_range = (min_d, max_d)
    picked_range = st.sidebar.date_input("Date range (UTC dates)", value=default_range, min_value=min_d, max_value=max_d)
    if isinstance(picked_range, tuple):
        start_date, end_date = picked_range
    else:
        start_date, end_date = picked_range, picked_range
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    filtered = df.copy()
    if selected_insts:
        filtered = filtered[filtered["installation_id"].astype(str).isin(selected_insts)]
    filtered = filtered[(filtered["date"] >= start_date) & (filtered["date"] <= end_date)]

    if filtered.empty:
        st.info("No rows match the current filters.")
        st.stop()

    time_col = "ts_local" if show_local_time else "ts_utc"

    # KPIs: Latest diff; Min/Max/Mean over last 24h window ending at last timestamp in filtered
    last_ts = filtered["ts_utc"].max()
    window_start = last_ts - pd.Timedelta(hours=24)
    last_row = filtered.loc[filtered["ts_utc"].idxmax()] if not filtered.empty else None
    latest_diff = last_row["diff"] if last_row is not None else np.nan
    last24 = filtered[(filtered["ts_utc"] >= window_start) & (filtered["ts_utc"] <= last_ts)]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Latest diff", f"{latest_diff:,.2f}" if pd.notna(latest_diff) else "—")
    k2.metric("Min (last 24h)", f"{last24['diff'].min():,.2f}" if not last24.empty else "—")
    k3.metric("Max (last 24h)", f"{last24['diff'].max():,.2f}" if not last24.empty else "—")
    k4.metric("Mean (last 24h)", f"{last24['diff'].mean():,.2f}" if not last24.empty else "—")

    st.subheader("Diff over time")
    l = alt.Chart(filtered).mark_line(point=False).encode(
        x=alt.X(f"{time_col}:T", title="Time"),
        y=alt.Y("diff:Q", title="Diff"),
        color=alt.Color("installation_id:N", title="Installation"),
        tooltip=["installation_id:N", alt.Tooltip(f"{time_col}:T", title="Time"), alt.Tooltip("diff:Q", format=",.2f")],
    ).properties(height=320)
    st.altair_chart(l, use_container_width=True)

    st.subheader("Scatter (outlier view)")
    s = alt.Chart(filtered).mark_circle(opacity=0.7).encode(
        x=alt.X(f"{time_col}:T", title="Time"),
        y=alt.Y("diff:Q", title="Diff"),
        color=alt.Color("installation_id:N", title="Installation"),
        tooltip=["installation_id:N", alt.Tooltip(f"{time_col}:T", title="Time"), alt.Tooltip("diff:Q", format=",.2f")],
    ).properties(height=280)
    st.altair_chart(s, use_container_width=True)

    st.subheader("Aggregated (daily mean)")
    # Resample on tz-aware index
    g = (filtered.set_index("ts_utc")
                 .groupby("installation_id")
                 .apply(lambda x: x[["diff"]].resample("1D").mean())
                 .reset_index(level=0).reset_index())
    g["date"] = g["ts_utc"].dt.date
    b = alt.Chart(g).mark_bar().encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("diff:Q", title="Mean diff"),
        color=alt.Color("installation_id:N", title="Installation"),
        tooltip=["installation_id:N", alt.Tooltip("date:T", title="Date"), alt.Tooltip("diff:Q", format=",.2f")],
    ).properties(height=260)
    st.altair_chart(b, use_container_width=True)

    st.subheader("Recent rows")
    recent = filtered.sort_values("ts_utc", ascending=False).head(200).copy()
    recent = recent.rename(columns={time_col: "timestamp"})
    st.dataframe(recent[["installation_id", "timestamp", "diff"]], use_container_width=True)
