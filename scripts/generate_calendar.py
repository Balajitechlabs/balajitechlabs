#!/usr/bin/env python3
import urllib.request, json, datetime, os, re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fetch_from_graphql(token):
    """Fetch contribution data directly via official GitHub GraphQL API when GITHUB_TOKEN is available."""
    url = 'https://api.github.com/graphql'
    query = """
    query {
      user(login: "Balajitechlabs") {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    level_map = {
        'NONE': 0,
        'FIRST_QUARTILE': 1,
        'SECOND_QUARTILE': 2,
        'THIRD_QUARTILE': 3,
        'FOURTH_QUARTILE': 4,
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({'query': query}).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        cal = result['data']['user']['contributionsCollection']['contributionCalendar']
        conts = []
        for w in cal.get('weeks', []):
            for d in w.get('contributionDays', []):
                conts.append({
                    'date': d['date'],
                    'count': d['contributionCount'],
                    'level': level_map.get(d.get('contributionLevel', 'NONE'), 0)
                })
        print(f"Official GitHub GraphQL API succeeded with {len(conts)} contribution days.")
        return {'contributions': conts}
    except Exception as e:
        print(f"GraphQL fetch failed ({e}), falling back to direct scrape...")
        return None

def fetch_contributions_data():
    """Fetch contribution data using GraphQL -> direct scrape -> API fallback chain."""
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        gql_data = fetch_from_graphql(token)
        if gql_data and len(gql_data.get('contributions', [])) > 0:
            return gql_data

    import time
    fallback_url = f'https://github.com/users/Balajitechlabs/contributions?_t={int(time.time())}'
    req_fb = urllib.request.Request(fallback_url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    })
    try:
        with urllib.request.urlopen(req_fb, timeout=10) as resp:
            html_content = resp.read().decode('utf-8')
        
        tds = re.findall(r'<td[^>]*class="[^"]*ContributionCalendar-day[^"]*"[^>]*>', html_content)
        tooltips = dict(re.findall(r'for="([^"]+)"[^>]*>([^<]+)<', html_content))
        conts = []
        for td in tds:
            dt_m = re.search(r'data-date="([^"]+)"', td)
            lvl_m = re.search(r'data-level="([^"]+)"', td)
            id_m = re.search(r'id="([^"]+)"', td)
            if dt_m and lvl_m:
                dt = dt_m.group(1)
                lvl = int(lvl_m.group(1))
                cell_id = id_m.group(1) if id_m else ''
                tip = tooltips.get(cell_id, '')
                cnt_m = re.search(r'(\d+)\s+contribution', tip)
                cnt = int(cnt_m.group(1)) if cnt_m else (1 if lvl > 0 else 0)
                conts.append({'date': dt, 'count': cnt, 'level': lvl})
        conts.sort(key=lambda x: x['date'])
        if len(conts) > 0:
            print(f"Direct GitHub scrape succeeded with {len(conts)} contribution days.")
            return {'contributions': conts}
    except Exception as fb_err:
        print(f"Direct GitHub scrape failed ({fb_err}), falling back to API...")

    url = 'https://github-contributions-api.jogruber.de/v4/Balajitechlabs'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data and 'contributions' in data:
                return data
    except Exception as e:
        print(f"API fetch also failed: {e}")

    return {'contributions': []}

def generate_calendar():
    data = fetch_contributions_data()
    date_map = {c['date']: c for c in data.get('contributions', [])}

    today = datetime.date.today()
    try:
        one_year_ago = today.replace(year=today.year - 1)
        min_date = one_year_ago + datetime.timedelta(days=1)
    except ValueError:
        min_date = today - datetime.timedelta(days=365)

    days_since_sunday = (today.weekday() + 1) % 7
    grid_end_sunday = today - datetime.timedelta(days=days_since_sunday)
    
    start_days_since_sunday = (min_date.weekday() + 1) % 7
    grid_start_sunday = min_date - datetime.timedelta(days=start_days_since_sunday)
    
    num_weeks = ((grid_end_sunday - grid_start_sunday).days // 7) + 1

    color_map_dark = {
        0: ('#141414', '#222222'),
        1: ('#555555', '#555555'),
        2: ('#888888', '#888888'),
        3: ('#cccccc', '#cccccc'),
        4: ('#ffffff', '#ffffff')
    }

    grid_x0 = 55
    grid_y0 = 62
    cell_size = 10
    gap = 3.5
    pitch = cell_size + gap

    current_year = today.year
    year_contributions = sum(c.get('count', 0) for c in data.get('contributions', []) if c.get('date', '').startswith(str(current_year)))
    total_contributions = year_contributions
    historical_2025 = 15
    total_all_time = year_contributions + historical_2025
    badge_text = f"{year_contributions} in {current_year}  \u2022  {total_all_time} All-Time"

    ist_tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now_ist = datetime.datetime.now(datetime.timezone.utc).astimezone(ist_tz)
    updated_str = now_ist.strftime('%d %b %Y, %I:%M %p IST')

    # Calculate month header labels matching GitHub thead colspans:
    # Group weeks into contiguous month spans, only render labels if span >= 2 columns
    month_labels = []
    weeks_by_month = []
    cur_m = None
    cur_m_name = ""
    cur_start_w = 0
    cur_count = 0

    for w in range(num_weeks):
        w_sunday = grid_start_sunday + datetime.timedelta(days=w * 7)
        m = w_sunday.month
        m_name = w_sunday.strftime('%b')
        if m != cur_m:
            if cur_m is not None:
                weeks_by_month.append((cur_start_w, cur_count, cur_m_name))
            cur_m = m
            cur_m_name = m_name
            cur_start_w = w
            cur_count = 1
        else:
            cur_count += 1
    if cur_m is not None:
        weeks_by_month.append((cur_start_w, cur_count, cur_m_name))

    for w_start_idx, col_span, mname in weeks_by_month:
        if col_span >= 2:
            month_labels.append((grid_x0 + w_start_idx * pitch, mname))

    weeks_rects = []
    for w in range(num_weeks):
        w_start = grid_start_sunday + datetime.timedelta(days=w * 7)
        for d in range(7):
            day_date = w_start + datetime.timedelta(days=d)
            if day_date < min_date or day_date > today:
                continue
            iso = day_date.isoformat()
            c = date_map.get(iso, {'count': 0, 'level': 0})
            lvl = c.get('level', 0)
            count = c.get('count', 0)
            x = grid_x0 + w * pitch
            y = grid_y0 + d * pitch
            title_text = f"{iso}: {count} contribution{'s' if count != 1 else ''}"
            weeks_rects.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="2" class="lvl-{lvl}"><title>{title_text}</title></rect>')

    month_svg = '\n'.join([f'<text x="{mx}" y="52" class="month-text">{mname}</text>' for mx, mname in month_labels])
    rects_svg = '\n  '.join(weeks_rects)

    svg_content = f'''<svg width="840" height="185" viewBox="0 0 840 185" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="calShimmer" x1="-100%" y1="0%" x2="200%" y2="0%">
      <stop offset="0%" stop-color="#666666" />
      <stop offset="35%" stop-color="#ffffff" />
      <stop offset="50%" stop-color="#ffffff" />
      <stop offset="65%" stop-color="#666666" />
      <stop offset="100%" stop-color="#333333" />
      <animate attributeName="x1" values="-100%;150%" dur="3.5s" repeatCount="indefinite" />
      <animate attributeName="x2" values="0%;250%" dur="3.5s" repeatCount="indefinite" />
    </linearGradient>
    <linearGradient id="calBorderPulse" x1="-100%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#222222" />
      <stop offset="50%" stop-color="#ffffff" stop-opacity="1" />
      <stop offset="100%" stop-color="#222222" />
      <animate attributeName="x1" values="-100%;100%" dur="3s" repeatCount="indefinite" />
      <animate attributeName="x2" values="0%;200%" dur="3s" repeatCount="indefinite" />
    </linearGradient>
  </defs>
  <style>
    .card-bg {{ fill: #000000; stroke: #2a2a2a; stroke-width: 1.5; rx: 12px; }}
    .cal-title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace; font-size: 13.5px; font-weight: 800; fill: url(#calShimmer); letter-spacing: 0.5px; }}
    .month-text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 9.5px; fill: #888888; }}
    .day-text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 9px; fill: #666666; }}
    .legend-text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 9.5px; fill: #888888; }}
    .stat-badge-bg {{ fill: #ffffff; stroke: #ffffff; rx: 4px; }}
    .stat-badge-text {{ font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace; font-size: 9.5px; font-weight: 700; fill: #000000; }}
    .octicon {{ fill: #ffffff; }}

    .lvl-0 {{ fill: #141414; stroke: #222222; stroke-width: 0.8; }}
    .lvl-1 {{ fill: #555555; }}
    .lvl-2 {{ fill: #888888; }}
    .lvl-3 {{ fill: #cccccc; }}
    .lvl-4 {{ fill: #ffffff; }}

    @media (prefers-color-scheme: light) {{
      .card-bg {{ fill: #ffffff; stroke: #000000; }}
      .cal-title {{ fill: #000000; }}
      .month-text {{ fill: #555555; }}
      .day-text {{ fill: #666666; }}
      .legend-text {{ fill: #444444; }}
      .stat-badge-bg {{ fill: #000000; stroke: #000000; }}
      .stat-badge-text {{ fill: #ffffff; }}
      .octicon {{ fill: #000000; }}

      .lvl-0 {{ fill: #ebedf0; stroke: #d0d7de; stroke-width: 0.8; }}
      .lvl-1 {{ fill: #b0b0b0; }}
      .lvl-2 {{ fill: #757575; }}
      .lvl-3 {{ fill: #404040; }}
      .lvl-4 {{ fill: #000000; }}
    }}
  </style>

  <!-- Container Box -->
  <rect x="1" y="1" width="838" height="183" rx="12" class="card-bg" />

  <!-- Animated Top Monochrome Accent Line -->
  <line x1="16" y1="1" x2="160" y2="1" stroke="url(#calBorderPulse)" stroke-width="2" stroke-linecap="round" />

  <!-- Header: Calendar Octicon + Title -->
  <g transform="translate(20, 16)">
    <svg width="16" height="16" viewBox="0 0 16 16" class="octicon" style="display: inline;">
      <path d="M4.75 0a.75.75 0 0 1 .75.75V2h5V.75a.75.75 0 0 1 1.5 0V2h1.25c.966 0 1.75.784 1.75 1.75v10.5A1.75 1.75 0 0 1 13.25 16H2.75A1.75 1.75 0 0 1 1 14.25V3.75C1 2.784 1.784 2 2.75 2H4V.75A.75.75 0 0 1 4.75 0ZM2.5 7.5v6.75c0 .138.112.25.25.25h10.5a.25.25 0 0 0 .25-.25V7.5Zm10.75-4H2.75a.25.25 0 0 0-.25.25V6h11V3.75a.25.25 0 0 0-.25-.25Z" />
    </svg>
    <text x="24" y="13" class="cal-title">CONTRIBUTION HEATMAP</text>
  </g>

  <!-- Right Header: Total Count Pill -->
  <rect x="624" y="15" width="196" height="20" class="stat-badge-bg" />
  <text x="722" y="29" text-anchor="middle" class="stat-badge-text">{badge_text}</text>

  <!-- Month Labels -->
  {month_svg}

  <!-- Day Labels (Mon, Wed, Fri) -->
  <text x="22" y="79" class="day-text">Mon</text>
  <text x="22" y="106" class="day-text">Wed</text>
  <text x="22" y="133" class="day-text">Fri</text>

  <!-- Contribution Heatmap Grid -->
  <g id="heatmap-grid">
  {rects_svg}
  </g>

  <!-- Last Updated at Bottom Left -->
  <g transform="translate(22, 166)">
    <circle cx="3" cy="5" r="2.5" class="legend-text" />
    <text x="11" y="8.5" class="legend-text">Updated: {updated_str}</text>
  </g>

  <!-- Legend at Bottom Right -->
  <g transform="translate(675, 166)">
    <text x="0" y="9" class="legend-text">Less</text>
    <rect x="28" y="0" width="10" height="10" rx="2" class="lvl-0" />
    <rect x="41" y="0" width="10" height="10" rx="2" class="lvl-1" />
    <rect x="54" y="0" width="10" height="10" rx="2" class="lvl-2" />
    <rect x="67" y="0" width="10" height="10" rx="2" class="lvl-3" />
    <rect x="80" y="0" width="10" height="10" rx="2" class="lvl-4" />
    <text x="96" y="9" class="legend-text">More</text>
  </g>
</svg>'''

    cal_path = os.path.join(BASE_DIR, 'icons', 'calendar.svg')
    with open(cal_path, 'w') as f:
        f.write(svg_content)
    print(f"Generated {cal_path} successfully with {year_contributions} contributions ({total_all_time} all-time).")

    dev_icons_dir = '/Users/btl/Developer/icons'
    if os.path.exists(dev_icons_dir) and os.path.abspath(os.path.join(BASE_DIR, 'icons')) != os.path.abspath(dev_icons_dir):
        dev_cal = os.path.join(dev_icons_dir, 'calendar.svg')
        with open(dev_cal, 'w') as f:
            f.write(svg_content)
        print(f"Synchronized {dev_cal} successfully.")

def update_profile_views():
    try:
        req = urllib.request.Request('https://komarev.com/ghpvc/?username=Balajitechlabs', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode('utf-8')
            match = re.search(r'>([0-9,]+)<', content)
            count_str = match.group(1) if match else "1,540"
    except Exception as e:
        print(f"Could not fetch views: {e}")
        count_str = "1,540"

    svg_views = f'''<svg width="200" height="30" viewBox="0 0 200 30" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="viewsShimmer" x1="-100%" y1="0%" x2="200%" y2="0%">
      <stop offset="0%" stop-color="#444444" />
      <stop offset="40%" stop-color="#ffffff" />
      <stop offset="60%" stop-color="#ffffff" />
      <stop offset="100%" stop-color="#444444" />
      <animate attributeName="x1" values="-100%;150%" dur="4s" repeatCount="indefinite" />
      <animate attributeName="x2" values="0%;250%" dur="4s" repeatCount="indefinite" />
    </linearGradient>
  </defs>
  <style>
    .badge-base {{ fill: #000000; stroke: #2a2a2a; stroke-width: 1.2; rx: 6px; }}
    .badge-label {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace; font-size: 10px; font-weight: 700; fill: #ffffff; letter-spacing: 0.6px; }}
    .badge-icon {{ fill: #ffffff; }}
    .count-bg {{ fill: #ffffff; rx: 4px; }}
    .count-text {{ font-family: -apple-system, BlinkMacSystemFont, 'SF Mono', monospace; font-size: 11px; font-weight: 800; fill: #000000; letter-spacing: 0.3px; }}
    @media (prefers-color-scheme: light) {{
      .badge-base {{ fill: #ffffff; stroke: #000000; }}
      .badge-label {{ fill: #000000; }}
      .badge-icon {{ fill: #000000; }}
      .count-bg {{ fill: #000000; }}
      .count-text {{ fill: #ffffff; }}
    }}
  </style>

  <!-- Container -->
  <rect x="1" y="1" width="198" height="28" rx="6" class="badge-base" />

  <!-- Eye Octicon -->
  <g transform="translate(10, 7) scale(0.9)">
    <path class="badge-icon" d="M8 2c1.981 0 3.671.992 4.933 2.078 1.27 1.091 2.187 2.345 2.637 3.023a1.62 1.62 0 0 1 0 1.798c-.45.678-1.367 1.932-2.637 3.023C11.67 13.008 9.981 14 8 14c-1.981 0-3.671-.992-4.933-2.078C1.797 10.83.88 9.576.43 8.898a1.62 1.62 0 0 1 0-1.798c.45-.677 1.367-1.931 2.637-3.022C4.33 2.992 6.019 2 8 2ZM1.679 7.932a.12.12 0 0 0 0 .136c.411.622 1.241 1.75 2.366 2.717C5.176 11.758 6.527 12.5 8 12.5c1.473 0 2.825-.742 3.955-1.715 1.124-.967 1.954-2.096 2.366-2.717a.12.12 0 0 0 0-.136c-.412-.621-1.242-1.75-2.366-2.717C10.824 4.242 9.473 3.5 8 3.5c-1.473 0-2.825.742-3.955 1.715-1.124.967-1.954 2.096-2.366 2.717ZM8 10a2 2 0 1 1-.001-3.999A2 2 0 0 1 8 10Z"/>
  </g>

  <!-- Label -->
  <text x="32" y="18.5" class="badge-label">PROFILE VIEWS</text>

  <!-- Value Pill (Inverted Solid White) -->
  <rect x="130" y="4" width="64" height="22" rx="4" class="count-bg" />
  <text x="162" y="18.5" text-anchor="middle" class="count-text">{count_str}+</text>
</svg>'''

    views_path = os.path.join(BASE_DIR, 'icons', 'profile_views.svg')
    with open(views_path, 'w') as f:
        f.write(svg_views)
    print(f"Generated {views_path} successfully with count {count_str}.")

    dev_icons_dir = '/Users/btl/Developer/icons'
    if os.path.exists(dev_icons_dir) and os.path.abspath(os.path.join(BASE_DIR, 'icons')) != os.path.abspath(dev_icons_dir):
        dev_views = os.path.join(dev_icons_dir, 'profile_views.svg')
        with open(dev_views, 'w') as f:
            f.write(svg_views)
        print(f"Synchronized {dev_views} with count {count_str}.")

    # Also sync view count in integrated footer wave
    for w_name in ['wave.svg', 'footer_wave.svg']:
        w_path = os.path.join(BASE_DIR, 'icons', w_name)
        if os.path.exists(w_path):
            with open(w_path, 'r') as f:
                w_content = f.read()
            w_updated = re.sub(r'class="count-text">[0-9,]+\+?<', f'class="count-text">{count_str}+<', w_content)
            with open(w_path, 'w') as f:
                f.write(w_updated)
            print(f"Synchronized {w_path} with count {count_str}+.")
            if os.path.exists(dev_icons_dir) and os.path.abspath(os.path.join(BASE_DIR, 'icons')) != os.path.abspath(dev_icons_dir):
                dev_w = os.path.join(dev_icons_dir, w_name)
                with open(dev_w, 'w') as f:
                    f.write(w_updated)
                print(f"Synchronized {dev_w} with count {count_str}+.")

if __name__ == '__main__':
    generate_calendar()
    update_profile_views()
    try:
        import generate_music_card
        generate_music_card.main()
    except Exception as e:
        print(f"Error updating music card: {e}")
