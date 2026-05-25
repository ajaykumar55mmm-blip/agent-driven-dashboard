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

