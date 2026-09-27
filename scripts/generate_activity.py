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

W, H = 1000, 290
left, top = 44, 96
cell, gap = 11, 5
step = cell + gap

counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
max_count = max(counts) if counts else 1

def color(c):
    if c == 0:
        return "#161b22"
    ratio = c / max_count
    if ratio < 0.25:
        return "#0e4429"
    if ratio < 0.50:
        return "#006d32"
    if ratio < 0.75:
        return "#26a641"
    return "#39d353"

squares = []
month_labels = []
seen_months = set()

for wi, week in enumerate(weeks):
    days = week["contributionDays"]
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
                f'<text x="{x}" y="76" class="month">{dt.strftime("%b")}</text>'
            )

grid_width = len(weeks) * step
scan_y = top + 42
scan_x1 = left
scan_x2 = left + grid_width - gap

svg = f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="{W}" y2="{H}">
    <stop stop-color="#0d1117"/>
    <stop offset="1" stop-color="#0f141b"/>
  </linearGradient>

  <linearGradient id="scanline" x1="{scan_x1}" y1="{scan_y}" x2="{scan_x2}" y2="{scan_y}" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#39d353" stop-opacity="0"/>
    <stop offset="0.5" stop-color="#39d353" stop-opacity="1"/>
    <stop offset="1" stop-color="#39d353" stop-opacity="0"/>
  </linearGradient>

  <filter id="softGlow" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="2.5" result="blur"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>

<style>
  .title {{
    font:700 23px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    fill:#f0f6fc;
  }}
  .note {{
    font:14px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    fill:#39d353;
  }}
  .month {{
    font:12px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    fill:#8b949e;
  }}
  .stat {{
    font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    fill:#8b949e;
  }}
  .scan-track {{
    stroke:#30363d;
    stroke-width:1;
    opacity:.8;
  }}
  .scanline {{
    stroke:url(#scanline);
    stroke-width:3;
    filter:url(#softGlow);
    stroke-linecap:round;
  }}
  .scan-dot {{
    fill:#c9d1d9;
    filter:url(#softGlow);
  }}
</style>

<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="20" fill="url(#bg)" stroke="#30363d"/>

<text x="36" y="42" class="title">&gt; GitHub Activity</text>
<text x="720" y="42" class="note">// contribution scanner</text>
<text x="36" y="66" class="stat">{total} contributions in the last year</text>

{''.join(month_labels)}
{''.join(squares)}

<line x1="{scan_x1}" y1="{scan_y}" x2="{scan_x2}" y2="{scan_y}" class="scan-track"/>

<line x1="{scan_x1}" y1="{scan_y}" x2="{scan_x1+150}" y2="{scan_y}" class="scanline">
  <animate attributeName="x1" values="{scan_x1};{scan_x2-150};{scan_x1}" dur="6s" repeatCount="indefinite"/>
  <animate attributeName="x2" values="{scan_x1+150};{scan_x2};{scan_x1+150}" dur="6s" repeatCount="indefinite"/>
</line>

<circle cy="{scan_y}" r="4" class="scan-dot">
  <animate attributeName="cx" values="{scan_x1};{scan_x2};{scan_x1}" dur="6s" repeatCount="indefinite"/>
</circle>

<text x="36" y="255" class="stat">scan mode → contribution matrix</text>
<text x="790" y="255" class="note">{LOGIN}</text>
</svg>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"Generated {OUT} with {total} contributions")
