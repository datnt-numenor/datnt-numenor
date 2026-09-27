import json
import os
import urllib.request
from datetime import datetime

TOKEN = os.environ["GITHUB_TOKEN"]
LOGIN = os.environ["GITHUB_REPOSITORY_OWNER"]
OUT = "assets/activity-wave.svg"

query = """
query($login:String!) {
  user(login:$login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": {"login": LOGIN}}).encode(),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "profile-activity-generator",
    },
)

with urllib.request.urlopen(req) as r:
    payload = json.load(r)

calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
total = calendar["totalContributions"]

W, H = 1000, 330
left, top = 42, 92
cell, gap = 11, 5
step = cell + gap

counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
max_count = max(counts) if counts else 1

def color(c):
    if c == 0:
        return "#161b22"
    ratio = c / max_count
    if ratio < .25:
        return "#0e4429"
    if ratio < .50:
        return "#006d32"
    if ratio < .75:
        return "#26a641"
    return "#39d353"

squares, week_totals, month_labels = [], [], []
seen_months = set()

for wi, week in enumerate(weeks):
    days = week["contributionDays"]
    week_totals.append(sum(d["contributionCount"] for d in days))
    for di, day in enumerate(days):
        x = left + wi * step
        y = top + di * step
        squares.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{color(day["contributionCount"])}" />'
        )
        dt = datetime.strptime(day["date"], "%Y-%m-%d")
        key = (dt.year, dt.month)
        if dt.day <= 7 and key not in seen_months:
            seen_months.add(key)
            month_labels.append(
                f'<text x="{x}" y="78" class="month">{dt.strftime("%b")}</text>'
            )

max_week = max(week_totals) if week_totals else 1
points = []
for wi, value in enumerate(week_totals):
    x = left + wi * step + cell / 2
    y = 250 - (value / max_week) * 58
    points.append((x, y))

path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points) if points else "M 40 220 L 950 220"

svg = f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="{W}" y2="{H}">
    <stop stop-color="#0d1117"/>
    <stop offset="1" stop-color="#0f141b"/>
  </linearGradient>
</defs>
<style>
  .title {{ font:700 23px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; fill:#f0f6fc; }}
  .note {{ font:14px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; fill:#39d353; }}
  .month {{ font:12px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; fill:#8b949e; }}
  .stat {{ font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; fill:#8b949e; }}
  .wave {{ stroke:#39d353; stroke-width:2.4; fill:none; opacity:.85; }}
  .dot {{ fill:#c9d1d9; }}
</style>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="20" fill="url(#bg)" stroke="#30363d"/>
<text x="36" y="42" class="title">&gt; GitHub Activity</text>
<text x="720" y="42" class="note">// consistent progress compounds</text>
<text x="36" y="66" class="stat">{total} contributions in the last year</text>
{''.join(month_labels)}
{''.join(squares)}
<path d="{path}" class="wave"/>
<circle r="4" class="dot">
  <animateMotion dur="6s" repeatCount="indefinite" path="{path}" />
</circle>
<text x="36" y="305" class="stat">build → learn → experiment → improve</text>
<text x="790" y="305" class="note">{LOGIN}</text>
</svg>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"Generated {OUT} with {total} contributions")
