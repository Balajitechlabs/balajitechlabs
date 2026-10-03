#!/usr/bin/env python3
"""
Custom Animated Monochrome Music Card Generator for Balaji S (balajitechlabs)
Queries Lanyard API for Discord Rich Presence (BitChord / YouTube Music / Spotify).
If playing: Renders live animated equalizer, gliding progress bar, album artwork, track & artist.
If offline/idle: Renders a luxury "Midnight Studio Deck" with animated rotating cassette reels and ambient breathing sine wave.
"""

import os
import json
import urllib.request
import base64
import html

DISCORD_USER_ID = "1402595333120458782"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ICONS_DIR = os.path.join(REPO_ROOT, "icons")
DEV_ICONS_DIR = "/Users/btl/Developer/icons"

def fetch_image_as_base64(img_url):
    try:
        req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            mime = resp.headers.get_content_type() or 'image/jpeg'
            return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"
    except Exception:
        return None

def format_time(seconds):
    seconds = max(0, int(seconds))
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"

def generate_offline_svg():
    return '''<svg width="400" height="140" viewBox="0 0 400 140" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    @keyframes spinReel {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    @keyframes breathe {
      0%, 100% { opacity: 0.35; stroke-width: 1.2px; }
      50% { opacity: 0.95; stroke-width: 2px; }
    }
    @keyframes pulseDot {
      0%, 100% { r: 3.5px; opacity: 0.4; }
      50% { r: 5px; opacity: 1; }
    }
    .reel-left {
      transform-origin: 52px 70px;
      animation: spinReel 8s linear infinite;
    }
    .reel-right {
      transform-origin: 88px 70px;
      animation: spinReel 8s linear infinite;
    }
    .ambient-line {
      animation: breathe 3.5s ease-in-out infinite;
    }
    .zen-dot {
      animation: pulseDot 2.5s ease-in-out infinite;
    }
    .font-title { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: 700; fill: #ffffff; letter-spacing: 0.5px; }
    .font-sub { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 400; fill: #888888; }
    .font-badge { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 9px; font-weight: 600; fill: #a0a0a0; letter-spacing: 1px; text-transform: uppercase; }
  </style>

  <!-- Background Card -->
  <rect x="0.5" y="0.5" width="399" height="139" rx="14" fill="#050505" stroke="#242424"/>

  <!-- Top Status Bar -->
  <g transform="translate(18, 16)">
    <rect x="0" y="0" width="102" height="20" rx="10" fill="#121212" stroke="#2a2a2a"/>
    <circle class="zen-dot" cx="10" cy="10" r="4" fill="#ffffff"/>
    <text x="20" y="13.5" class="font-badge">STUDIO MODE</text>

    <!-- Sleeping Wave -->
    <path class="ambient-line" d="M 260 10 Q 280 4, 300 10 T 340 10 T 364 10" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round"/>
  </g>

  <!-- Cassette Tape Deck -->
  <g transform="translate(18, 48)">
    <rect x="0" y="0" width="104" height="66" rx="7" fill="#111111" stroke="#2a2a2a" stroke-width="1.5"/>
    <rect x="6" y="6" width="92" height="54" rx="4" fill="#161616" stroke="#222222"/>
    <path d="M 12 12 L 92 12 L 86 54 L 18 54 Z" fill="#0a0a0a" stroke="#262626" stroke-width="1"/>
    <rect x="26" y="20" width="52" height="26" rx="13" fill="#141414" stroke="#2e2e2e"/>
    <rect x="34" y="31" width="36" height="4" fill="#222222"/>

    <!-- Left Spool -->
    <g class="reel-left">
      <circle cx="52" cy="70" r="8" fill="#000000" stroke="#444444" stroke-width="1.5"/>
      <circle cx="52" cy="70" r="3" fill="#ffffff"/>
      <line x1="52" y1="62" x2="52" y2="78" stroke="#ffffff" stroke-width="1"/>
      <line x1="44" y1="70" x2="60" y2="70" stroke="#ffffff" stroke-width="1"/>
    </g>

    <!-- Right Spool -->
    <g class="reel-right">
      <circle cx="88" cy="70" r="8" fill="#000000" stroke="#444444" stroke-width="1.5"/>
      <circle cx="88" cy="70" r="3" fill="#ffffff"/>
      <line x1="88" y1="62" x2="88" y2="78" stroke="#ffffff" stroke-width="1"/>
      <line x1="80" y1="70" x2="96" y2="70" stroke="#ffffff" stroke-width="1"/>
    </g>
  </g>

  <!-- Typography & Details -->
  <g transform="translate(142, 58)">
    <text x="0" y="14" class="font-title">OFFLINE // CODING IN SILENCE</text>
    <text x="0" y="32" class="font-sub">Crafting at balajitechlabs • Pure Focus</text>
    
    <!-- Sleep Pulse Bar -->
    <rect x="0" y="42" width="238" height="4" rx="2" fill="#1c1c1c"/>
    <rect class="ambient-line" x="0" y="42" width="70" height="4" rx="2" fill="#ffffff"/>
    <text x="0" y="60" class="font-badge" fill="#555555">MUSIC ENGINE IDLE • WAITING FOR BIT CHORD</text>
  </g>
</svg>'''

def generate_playing_svg(title, artist, app_name, img_data_uri, elapsed_sec, total_sec):
    title_esc = html.escape(title)
    artist_esc = html.escape(f"{artist} • {app_name}")
    percent = (elapsed_sec / total_sec) * 100 if total_sec > 0 else 0
    remaining_sec = max(1, int(total_sec - elapsed_sec))
    elapsed_str = format_time(elapsed_sec)
    total_str = format_time(total_sec)

    artwork_markup = ""
    if img_data_uri:
        artwork_markup = f'''
    <clipPath id="artClip"><rect x="0" y="0" width="72" height="72" rx="10"/></clipPath>
    <image href="{img_data_uri}" width="72" height="72" clip-path="url(#artClip)" preserveAspectRatio="xMidYMid slice"/>
    <rect x="0" y="0" width="72" height="72" rx="10" fill="none" stroke="#282828" stroke-width="1"/>
'''
    else:
        artwork_markup = '''
    <rect x="0" y="0" width="72" height="72" rx="10" fill="#141414" stroke="#282828"/>
    <circle cx="36" cy="36" r="30" fill="#0a0a0a" stroke="#1f1f1f" stroke-width="1.5"/>
    <circle cx="36" cy="36" r="22" fill="none" stroke="#262626" stroke-width="1"/>
    <circle cx="36" cy="36" r="14" fill="none" stroke="#333333" stroke-width="1"/>
    <circle cx="36" cy="36" r="7" fill="#ffffff"/>
    <circle cx="36" cy="36" r="2.5" fill="#000000"/>
'''

    return f'''<svg width="400" height="140" viewBox="0 0 400 140" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    @keyframes eq1 {{ 0%, 100% {{ height: 4px; y: 14px; }} 50% {{ height: 16px; y: 2px; }} }}
    @keyframes eq2 {{ 0%, 100% {{ height: 16px; y: 2px; }} 50% {{ height: 5px; y: 13px; }} }}
    @keyframes eq3 {{ 0%, 100% {{ height: 8px; y: 10px; }} 50% {{ height: 18px; y: 0px; }} }}
    @keyframes eq4 {{ 0%, 100% {{ height: 17px; y: 1px; }} 50% {{ height: 6px; y: 12px; }} }}
    @keyframes eq5 {{ 0%, 100% {{ height: 6px; y: 12px; }} 50% {{ height: 15px; y: 3px; }} }}
    @keyframes pulseLive {{
      0%, 100% {{ transform: scale(1); opacity: 0.9; }}
      50% {{ transform: scale(1.3); opacity: 0.4; }}
    }}
    @keyframes liveProgress {{
      from {{ width: {percent:.1f}%; }}
      to {{ width: 100%; }}
    }}
    .eq-bar-1 {{ animation: eq1 0.85s ease-in-out infinite; }}
    .eq-bar-2 {{ animation: eq2 0.7s ease-in-out infinite; }}
    .eq-bar-3 {{ animation: eq3 0.95s ease-in-out infinite; }}
    .eq-bar-4 {{ animation: eq4 0.65s ease-in-out infinite; }}
    .eq-bar-5 {{ animation: eq5 0.8s ease-in-out infinite; }}
    .live-dot {{
      transform-origin: 10px 10px;
      animation: pulseLive 1.8s ease-in-out infinite;
    }}
    .progress-fill {{
      animation: liveProgress {remaining_sec}s linear infinite;
    }}
    .font-title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; font-weight: 700; fill: #ffffff; letter-spacing: 0.3px; }}
    .font-sub {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 12px; font-weight: 400; fill: #999999; }}
    .font-time {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 10px; font-weight: 500; fill: #777777; }}
    .font-badge {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 9px; font-weight: 600; fill: #ffffff; letter-spacing: 1px; text-transform: uppercase; }}
  </style>

  <!-- Background Card -->
  <rect x="0.5" y="0.5" width="399" height="139" rx="14" fill="#050505" stroke="#2a2a2a"/>

  <!-- Top Status Bar: Live Indicator + Animated Equalizer -->
  <g transform="translate(18, 14)">
    <rect x="0" y="0" width="108" height="20" rx="10" fill="#121212" stroke="#2a2a2a"/>
    <circle class="live-dot" cx="10" cy="10" r="3.5" fill="#ffffff"/>
    <text x="20" y="13.5" class="font-badge">NOW PLAYING</text>

    <!-- 5 Equalizer Bars -->
    <g transform="translate(340, 2)">
      <rect class="eq-bar-1" x="0" y="8" width="3" height="10" rx="1.5" fill="#ffffff"/>
      <rect class="eq-bar-2" x="5" y="2" width="3" height="16" rx="1.5" fill="#ffffff"/>
      <rect class="eq-bar-3" x="10" y="4" width="3" height="14" rx="1.5" fill="#ffffff"/>
      <rect class="eq-bar-4" x="15" y="1" width="3" height="17" rx="1.5" fill="#ffffff"/>
      <rect class="eq-bar-5" x="20" y="7" width="3" height="11" rx="1.5" fill="#ffffff"/>
    </g>
  </g>

  <!-- Album Artwork / Vinyl -->
  <g transform="translate(18, 46)">
{artwork_markup}
  </g>

  <!-- Track Title, Artist, & Live Progress Bar -->
  <g transform="translate(104, 52)">
    <text x="0" y="14" class="font-title">{title_esc}</text>
    <text x="0" y="32" class="font-sub">{artist_esc}</text>
    
    <!-- Animated Progress Bar -->
    <g transform="translate(0, 44)">
      <rect x="0" y="0" width="276" height="5" rx="2.5" fill="#1c1c1c"/>
      <rect class="progress-fill" x="0" y="0" width="{percent:.1f}%" height="5" rx="2.5" fill="#ffffff"/>
      <text x="0" y="18" class="font-time">{elapsed_str}</text>
      <text x="276" y="18" text-anchor="end" class="font-time">{total_str}</text>
    </g>
  </g>
</svg>'''

def main():
    import time
    now_ms = time.time() * 1000

    url = f"https://api.lanyard.rest/v1/users/{DISCORD_USER_ID}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = {}
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode()).get('data', {})
    except Exception as e:
        print(f"Error fetching Lanyard: {e}")

    activities = data.get('activities', [])
    music_act = None
    for act in activities:
        if act.get('type') == 2 or 'music' in act.get('name', '').lower() or act.get('details'):
            music_act = act
            break

    svg_content = ""
    if not music_act or data.get('discord_status') == 'offline':
        print("User is offline/idle -> Generating Midnight Studio Deck")
        svg_content = generate_offline_svg()
    else:
        title = music_act.get('details', 'Playing Music')
        artist = music_act.get('state', 'Unknown Artist')
        app_name = music_act.get('name', 'btl music 🎶')
        timestamps = music_act.get('timestamps', {})
        start_ms = timestamps.get('start', now_ms)
        end_ms = timestamps.get('end', now_ms + 180000)

        total_sec = max(1, (end_ms - start_ms) / 1000)
        elapsed_sec = min(total_sec, max(0, (now_ms - start_ms) / 1000))

        # Extract artwork URL if available
        large_image = music_act.get('assets', {}).get('large_image', '')
        img_data_uri = None
        if large_image:
            if large_image.startswith('mp:external/'):
                # Extract external URL
                parts = large_image.split('/https/')
                if len(parts) > 1:
                    raw_url = 'https://' + parts[1]
                    img_data_uri = fetch_image_as_base64(raw_url)
            elif large_image.startswith('spotify:'):
                spotify_id = large_image.replace('spotify:', '')
                raw_url = f"https://i.scdn.co/image/{spotify_id}"
                img_data_uri = fetch_image_as_base64(raw_url)

        print(f"User is playing: {title} by {artist} ({format_time(elapsed_sec)} / {format_time(total_sec)})")
        svg_content = generate_playing_svg(title, artist, app_name, img_data_uri, elapsed_sec, total_sec)

    # Save to icons/music_card.svg
    os.makedirs(ICONS_DIR, exist_ok=True)
    target_path = os.path.join(ICONS_DIR, "music_card.svg")
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Saved: {target_path}")

    # Also sync to /Users/btl/Developer/icons
    if os.path.exists(DEV_ICONS_DIR):
        dev_target = os.path.join(DEV_ICONS_DIR, "music_card.svg")
        with open(dev_target, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Synced: {dev_target}")

if __name__ == "__main__":
    main()
