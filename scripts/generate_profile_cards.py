import json, os, urllib.request
from collections import Counter

API = "https://api.github.com/graphql"
TOKEN = os.environ["GITHUB_TOKEN"]
USER = "Ravikiran9988"

query = '''query($login:String!){
  user(login:$login){
    followers{totalCount}
    repositories(ownerAffiliations:OWNER, privacy:PUBLIC, first:100){nodes{name stargazerCount forkCount primaryLanguage{name}}}
    contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}
  }
}'''

def gql():
    body = json.dumps({"query": query, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-cards",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]

def esc(s):
    return (str(s).replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;")
                  .replace('"', "&quot;"))

def svg_open(w, h, title, subtitle):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<rect width="100%" height="100%" rx="18" fill="#0d1117" stroke="#30363d"/>
<text x="30" y="38" fill="#f0f6fc" font-family="Arial,sans-serif" font-size="22" font-weight="700">{esc(title)}</text>
<text x="30" y="60" fill="#8b949e" font-family="Arial,sans-serif" font-size="12">{esc(subtitle)}</text>'''

def main():
    u = gql()
    repos = u["repositories"]["nodes"]
    langs = Counter(r["primaryLanguage"]["name"] for r in repos if r.get("primaryLanguage"))
    total = sum(langs.values()) or 1
    colors = {
        "JavaScript":"#f1e05a", "Python":"#3572A5", "TypeScript":"#3178c6",
        "HTML":"#e34c26", "CSS":"#563d7c", "Java":"#b07219",
        "PHP":"#4F5D95", "C++":"#f34b7d", "C":"#555555",
        "Jupyter Notebook":"#DA5B0B"
    }
    os.makedirs("assets", exist_ok=True)

    # Top Languages
    out = svg_open(900, 250, "Top Languages", "Primary language across your public repositories")
    y = 88
    barx, barw, barh = 30, 840, 16
    cur = barx
    for name, n in langs.most_common(8):
        w = barw * n / total
        out += f'<rect x="{cur:.1f}" y="{y}" width="{max(w,1):.1f}" height="{barh}" fill="{colors.get(name,"#58a6ff")}"/>'
        cur += w
    y = 132
    for i, (name, n) in enumerate(langs.most_common(8)):
        col = colors.get(name, "#58a6ff")
        yy = y + (i // 2) * 28
        xx = 35 + (i % 2) * 430
        out += f'<circle cx="{xx}" cy="{yy-5}" r="5" fill="{col}"/><text x="{xx+12}" y="{yy}" fill="#c9d1d9" font-family="Arial,sans-serif" font-size="13">{esc(name)}</text><text x="{xx+360}" y="{yy}" fill="#8b949e" font-family="Arial,sans-serif" font-size="13" text-anchor="end">{n/total*100:.1f}%</text>'
    out += '</svg>'
    with open("assets/top-languages.svg", "w", encoding="utf-8") as f:
        f.write(out)

    # Contribution Activity
    days = [d for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    maxc = max((d["contributionCount"] for d in days), default=1)
    out = svg_open(900, 300, "Contribution Activity", "GitHub contribution activity • generated from GitHub API")
    startx, starty, cell, gap = 30, 88, 13, 3
    fills = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

    # Use a valid SVG group for each day. No invalid child elements inside <rect>.
    for i, d in enumerate(days):
        week = i // 7
        dow = i % 7
        x = startx + week * (cell + gap)
        yy = starty + dow * (cell + gap)
        c = d["contributionCount"]
        level = 0 if c == 0 else min(4, 1 + int(c / maxc * 3))
        out += f'<rect x="{x}" y="{yy}" width="{cell}" height="{cell}" rx="2" fill="{fills[level]}"/>'

    total_contributions = u["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    out += f'<text x="30" y="250" fill="#8b949e" font-family="Arial,sans-serif" font-size="13">{total_contributions} contributions in the last year</text>'
    out += '<text x="30" y="273" fill="#484f58" font-family="Arial,sans-serif" font-size="11">Source: GitHub GraphQL API • auto-updated daily</text></svg>'
    with open("assets/activity.svg", "w", encoding="utf-8") as f:
        f.write(out)

if __name__ == "__main__":
    main()
