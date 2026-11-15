import json, os, sys, urllib.request
from xml.sax.saxutils import escape

USER = os.environ.get("GH_USER", "kakkky")
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"
THEMES = {
    "dark":  dict(bg="#0d1117", border="#30363d", text="#e6edf3", muted="#8b949e", accent="#39d353", track="#21262d"),
    "light": dict(bg="#ffffff", border="#d0d7de", text="#1f2328", muted="#57606a", accent="#1a7f37", track="#eaeef2"),
}
QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    contributionsCollection { totalCommitContributions restrictedContributionsCount totalPullRequestReviewContributions contributionCalendar { totalContributions } }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
  }
}
"""
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    body = json.load(urllib.request.urlopen(req))
    if "errors" in body:
        sys.exit(body["errors"])
    return body["data"]["user"]

def rank(commits, prs, issues, reviews, stars, followers):
    # github-readme-stats の rank.js と同じ重み・中央値で上位何 % かを出す
    exp_cdf = lambda x: 1 - 2 ** -x
    log_cdf = lambda x: x / (1 + x)
    parts = [
        (2, exp_cdf(commits / 250)),
        (3, exp_cdf(prs / 50)),
        (1, exp_cdf(issues / 25)),
        (1, exp_cdf(reviews / 2)),
        (4, log_cdf(stars / 50)),
        (1, log_cdf(followers / 10)),
    ]
    percentile = (1 - sum(w * v for w, v in parts) / sum(w for w, _ in parts)) * 100
    for threshold, level in zip([1, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100], ["S", "A+", "A", "A-", "B+", "B", "B-", "C+", "C"]):
        if percentile <= threshold:
            return level, percentile


def summarize(u):
    repos = u["repositories"]["nodes"]
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"]["color"] or "#8b949e"])[0] += e["size"]
    cc = u["contributionsCollection"]
    stats = [
        ("Total Stars", sum(r["stargazerCount"] for r in repos)),
        ("Commits (last year)", cc["totalCommitContributions"]),
        ("Contributions (last year)", cc["contributionCalendar"]["totalContributions"] - cc["restrictedContributionsCount"]),
        ("Pull Requests", u["pullRequests"]["totalCount"]),
        ("Issues", u["issues"]["totalCount"]),
        ("Public Repos", u["repositories"]["totalCount"]),
    ]
    level = rank(stats[1][1], stats[3][1], stats[4][1], cc["totalPullRequestReviewContributions"],
                 stats[0][1], u["followers"]["totalCount"])
    top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]
    total = sum(v[0] for _, v in top)
    return stats, level, [(n, v[1], v[0] / total) for n, v in top]

def card(c, w, h, title, inner, extra_css=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<style>
.t{{font:600 16px {SANS};fill:{c["text"]}}}
.l{{font:13px {SANS};fill:{c["muted"]}}}
.v{{font:600 13px {MONO};fill:{c["text"]}}}
.row{{opacity:0;animation:in .5s ease-out forwards}}
@keyframes in{{from{{opacity:0;transform:translateX(-8px)}}to{{opacity:1;transform:none}}}}
{extra_css}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;opacity:1!important}}}}
</style>
<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{c["bg"]}" stroke="{c["border"]}"/>
<text class="t" x="24" y="36">{escape(title)}</text>
{inner}
</svg>
'''

def stats_card(c, stats, level):
    rows = "".join(
        f'<g class="row" style="animation-delay:{0.15 + i * 0.12:.2f}s">'
        f'<text class="l" x="24" y="{70 + i * 26}">{escape(k)}</text>'
        f'<text class="v" x="250" y="{70 + i * 26}" text-anchor="end">{v:,}</text></g>'
        for i, (k, v) in enumerate(stats))
    grade, percentile = level
    r, cx, cy = 44, 345, 118
    circ = 2 * 3.14159 * r
    fill = (100 - percentile) / 100
    css = (f".ring{{stroke-dasharray:{circ:.1f};stroke-dashoffset:{circ:.1f};animation:ring 1.6s cubic-bezier(.2,.8,.2,1) .3s forwards}}"
           f"@keyframes ring{{to{{stroke-dashoffset:{circ * (1 - fill):.1f}}}}}")
    ring = (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["track"]}" stroke-width="8"/>'
            f'<circle class="ring" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c["accent"]}" stroke-width="8" stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>'
            f'<text x="{cx}" y="{cy + 10}" text-anchor="middle" style="font:800 30px {SANS};fill:{c["text"]}">{grade}</text>'
            f'<text x="{cx}" y="{cy + r + 26}" text-anchor="middle" class="l" style="font-size:11px">top {percentile:.1f}%</text>')
    return card(c, 420, 230, f"{USER}'s GitHub Stats", rows + ring, css)

def langs_card(c, langs):
    x, bar = 24, []
    width = 302
    for i, (n, col, p) in enumerate(langs):
        w = width * p
        bar.append(f'<rect x="{x:.1f}" y="52" width="{w:.1f}" height="10" fill="{col}"/>')
        x += w
    css = (f".bar{{clip-path:inset(0 100% 0 0 round 5px);animation:grow 1.2s cubic-bezier(.2,.8,.2,1) .2s forwards}}"
           f"@keyframes grow{{to{{clip-path:inset(0 0 0 0 round 5px)}}}}")
    legend = "".join(
        f'<g class="row" style="animation-delay:{0.5 + i * 0.1:.2f}s">'
        f'<circle cx="{30 + (i % 2) * 150}" cy="{88 + (i // 2) * 26}" r="5" fill="{col}"/>'
        f'<text class="l" x="{42 + (i % 2) * 150}" y="{92 + (i // 2) * 26}">{escape(n)} <tspan class="v" style="font-weight:400">{p * 100:.1f}%</tspan></text></g>'
        for i, (n, col, p) in enumerate(langs))
    return card(c, 350, 230, "Most Used Languages", f'<g class="bar">{"".join(bar)}</g>{legend}', css)

stats, level, langs = summarize(fetch())
for name, c in THEMES.items():
    open(f"{OUT}/stats-{name}.svg", "w").write(stats_card(c, stats, level))
    open(f"{OUT}/langs-{name}.svg", "w").write(langs_card(c, langs))
print(stats, level, [(n, round(p, 3)) for n, _, p in langs])
