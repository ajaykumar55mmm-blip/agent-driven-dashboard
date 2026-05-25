from dotenv import load_dotenv
import os
from openai import OpenAI
import pandas as pd
import json


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




with open("motor_insurance_metric_library.json", "r") as f:
    metric_library = json.load(f)

approved_metrics = [
    m for m in metric_library["metrics"] if m["status"] == "approved"
]

metric_lookup = {
    m["name"]: m["dax"] for m in approved_metrics
}
print(metric_lookup)



df = pd.read_csv("motor_insurance_claims.csv")

columns = list(df.columns)

print("Columns detected:", columns)


user_prompt = """
Metrics:
- Loss Ratio
- Total Claims
- Avg Claim Cost = AVERAGE(claim_amount)

Breakdown:
- state
- claim_date

Visuals:
- KPI
- trend
"""
system_prompt = f"""
You are a dashboard analysis agent for motor insurance data.

You have access to these approved metrics:
{json.dumps(metric_lookup, indent=2)}

You have access to these data columns:
{columns}

The user will ask for a dashboard. You must respond in JSON format like this:
{{
  "metrics": ["metric1", "metric2"],
  "breakdowns": ["column1", "column2"],
  "visuals": ["KPI", "trend"]
}}

Only use metrics from the approved list. Only use columns from the data.
"""

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
)

agent_output = response.choices[0].message.content
print("Agent response:", agent_output)
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Parse the agent response
try:
    plan = json.loads(agent_output)
except:
    # Remove markdown code blocks if present
    cleaned = agent_output.replace("```json", "").replace("```", "").strip()
    plan = json.loads(cleaned)

print("Dashboard plan:", plan)

# Calculate the metrics from the data
figures = []

# KPI cards
for metric in plan.get("metrics", []):
    if metric == "Total Claims":
        value = df["claim_amount"].sum()
        fig = go.Figure(go.Indicator(
            mode="number",
            value=value,
            title={"text": "Total Claims"}
        ))
        figures.append(fig)

    elif metric == "Average Claim Cost":
        value = df["claim_amount"].mean()
        fig = go.Figure(go.Indicator(
            mode="number",
            value=round(value, 2),
            title={"text": "Average Claim Cost"}
        ))
        figures.append(fig)

    elif metric == "Loss Ratio":
        value = df["claim_amount"].sum() / df["premium"].sum()
        fig = go.Figure(go.Indicator(
            mode="number",
            value=round(value, 4),
            title={"text": "Loss Ratio"}
        ))
        figures.append(fig)

# Trend chart by state
if "state" in plan.get("breakdowns", []):
    state_df = df.groupby("state")["claim_amount"].sum().reset_index()
    fig = px.bar(state_df, x="state", y="claim_amount", title="Total Claims by State")
    figures.append(fig)

# Trend chart by date
if "claim_date" in plan.get("breakdowns", []):
    df["claim_date"] = pd.to_datetime(df["claim_date"])
    date_df = df.groupby("claim_date")["claim_amount"].sum().reset_index()
    fig = px.line(date_df, x="claim_date", y="claim_amount", title="Claims Trend Over Time")
    figures.append(fig)

# Build final HTML dashboard
html_parts = []
for fig in figures:
    html_parts.append(fig.to_html(full_html=False, include_plotlyjs='cdn'))

final_html = f"""
<html>
<head><title>Motor Insurance Dashboard</title>
<style>
    body {{ font-family: Arial; background: #f4f4f4; padding: 20px; }}
    h1 {{ color: #1F3A6E; }}
    .chart {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; }}
</style>
</head>
<body>
<h1>Motor Insurance Claims Dashboard</h1>
{''.join([f'<div class="chart">{c}</div>' for c in html_parts])}
</body>
</html>
"""

with open("dashboard.html", "w") as f:
    f.write(final_html)

print("Dashboard saved as dashboard.html")
print("Open it in your browser to view.")