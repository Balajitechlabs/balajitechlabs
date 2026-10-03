#!/usr/bin/env python3
import urllib.request, json, datetime, os, re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_calendar():
    url = 'https://github-contributions-api.jogruber.de/v4/Balajitechlabs'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())

    date_map = {c['date']: c for c in data.get('contributions', [])}

    today = datetime.date.today()
    # Find current week Saturday (or today)
    # GitHub week ends on Saturday
    days_to_saturday = (5 - today.weekday()) % 7
    end_date = today + datetime.timedelta(days=days_to_saturday)
    if end_date > today:
        end_date = today

    # Align 52 weeks (364 days) back
    # Find Sunday for start
    cur = end_date
    while cur.weekday() != 6: # Sunday
        cur -= datetime.timedelta(days=1)
    start_date = cur - datetime.timedelta(weeks=51)

    color_map_dark = {
        0: ('#141414', '#222222'),
        1: ('#3d3d3d', '#3d3d3d'),
        2: ('#707070', '#707070'),
        3: ('#adadad', '#adadad'),
        4: ('#ffffff', '#ffffff')
    }

    weeks_rects = []
    month_labels = []
    last_month = None

    grid_x0 = 55
    grid_y0 = 62
    cell_size = 10
    gap = 3.5
    pitch = cell_size + gap

    total_contributions = 0

    for w in range(52):
        w_start = start_date + datetime.timedelta(days=w*7)
        if w_start.month != last_month:
            month_labels.append((grid_x0 + w * pitch, w_start.strftime('%b')))
            last_month = w_start.month
        for d in range(7):
            day_date = w_start + datetime.timedelta(days=d)
            iso = day_date.isoformat()
            c = date_map.get(iso, {'count': 0, 'level': 0})
            lvl = c.get('level', 0)
            count = c.get('count', 0)
            total_contributions += count
            fill, stroke = color_map_dark.get(lvl, color_map_dark[0])
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
    .lvl-1 {{ fill: #3d3d3d; }}
    .lvl-2 {{ fill: #707070; }}
    .lvl-3 {{ fill: #adadad; }}
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
  <rect x="656" y="15" width="164" height="20" class="stat-badge-bg" />
  <text x="738" y="29" text-anchor="middle" class="stat-badge-text">{total_contributions} Contributions in 2026</text>

  <!-- Month Labels -->
  {month_svg}

  <!-- Day Labels (Mon, Wed, Fri) -->
  <text x="22" y="79" class="day-text">Mon</text>
  <text x="22" y="106" class="day-text">Wed</text>
  <text x="22" y="133" class="day-text">Fri</text>

  <!-- Contribution Heatmap Grid (364 Days) -->
  <g id="heatmap-grid">
  {rects_svg}
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
    print(f"Generated {cal_path} successfully with {total_contributions} contributions.")

def update_profile_views():
    try:
        req = urllib.request.Request('https://komarev.com/ghpvc/?username=Balajitechlabs', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
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

if __name__ == '__main__':
    generate_calendar()
    update_profile_views()
    try:
        import generate_music_card
        generate_music_card.main()
    except Exception as e:
        print(f"Error updating music card: {e}")

