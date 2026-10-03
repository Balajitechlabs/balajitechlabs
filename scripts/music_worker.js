/**
 * Cloudflare Worker / Serverless Edge Function for Live Discord Music Presence
 * Endpoint: https://music.balajitechlab.com or https://<worker-name>.workers.dev
 *
 * Fetches real-time Discord presence from Lanyard API (BitChord / YouTube Music / Spotify).
 * - If playing: Returns luxury monochrome SVG with live animated equalizer, gliding progress bar, and album art.
 * - If offline/idle: Returns "Midnight Studio Deck" with animated rotating cassette reels and ambient sine wave.
 */

const DISCORD_USER_ID = "1402595333120458782";

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const userId = url.searchParams.get("userId") || DISCORD_USER_ID;

    try {
      const lanyardRes = await fetch(`https://api.lanyard.rest/v1/users/${userId}`, {
        headers: { "User-Agent": "BTL-Music-Worker/1.0" },
      });
      const json = await lanyardRes.json();
      const data = json?.data || {};

      const activities = data.activities || [];
      const musicAct = activities.find(
        (a) => a.type === 2 || (a.name && a.name.toLowerCase().includes("music")) || a.details
      );

      let svg = "";
      if (!musicAct || data.discord_status === "offline") {
        svg = renderOfflineSvg();
      } else {
        const title = musicAct.details || "Playing Music";
        const artist = musicAct.state || "Unknown Artist";
        const appName = musicAct.name || "btl music 🎶";
        const now = Date.now();
        const startMs = musicAct.timestamps?.start || now;
        const endMs = musicAct.timestamps?.end || now + 180000;

        const totalSec = Math.max(1, Math.floor((endMs - startMs) / 1000));
        const elapsedSec = Math.min(totalSec, Math.max(0, Math.floor((now - startMs) / 1000)));

        let imgDataUri = null;
        const largeImage = musicAct.assets?.large_image || "";
        if (largeImage.startsWith("mp:external/")) {
          const parts = largeImage.split("/https/");
          if (parts.length > 1) {
            const rawUrl = "https://" + parts[1];
            imgDataUri = await fetchImageBase64(rawUrl);
          }
        } else if (largeImage.startsWith("spotify:")) {
          const spotifyId = largeImage.replace("spotify:", "");
          imgDataUri = await fetchImageBase64(`https://i.scdn.co/image/${spotifyId}`);
        }

        svg = renderPlayingSvg(title, artist, appName, imgDataUri, elapsedSec, totalSec);
      }

      return new Response(svg, {
        headers: {
          "Content-Type": "image/svg+xml; charset=utf-8",
          "Cache-Control": "public, max-age=30, s-maxage=30",
          "Access-Control-Allow-Origin": "*",
        },
      });
    } catch (err) {
      return new Response(renderOfflineSvg(), {
        headers: {
          "Content-Type": "image/svg+xml; charset=utf-8",
          "Cache-Control": "public, max-age=60",
        },
      });
    }
  },
};

async function fetchImageBase64(imageUrl) {
  try {
    const res = await fetch(imageUrl);
    if (!res.ok) return null;
    const arrayBuffer = await res.arrayBuffer();
    const bytes = new Uint8Array(arrayBuffer);
    let binary = "";
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    const b64 = btoa(binary);
    const mime = res.headers.get("content-type") || "image/jpeg";
    return `data:${mime};base64,${b64}`;
  } catch {
    return null;
  }
}

function escapeXml(unsafe) {
  return String(unsafe).replace(/[<>&'"]/g, (c) => {
    switch (c) {
      case "<": return "&lt;";
      case ">": return "&gt;";
      case "&": return "&amp;";
      case "'": return "&apos;";
      case '"': return "&quot;";
    }
  });
}

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function renderOfflineSvg() {
  return `<svg width="400" height="140" viewBox="0 0 400 140" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    @keyframes spinReel { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes breathe { 0%, 100% { opacity: 0.35; stroke-width: 1.2px; } 50% { opacity: 0.95; stroke-width: 2px; } }
    @keyframes pulseDot { 0%, 100% { r: 3.5px; opacity: 0.4; } 50% { r: 5px; opacity: 1; } }
    .reel-left { transform-origin: 52px 70px; animation: spinReel 8s linear infinite; }
    .reel-right { transform-origin: 88px 70px; animation: spinReel 8s linear infinite; }
    .ambient-line { animation: breathe 3.5s ease-in-out infinite; }
    .zen-dot { animation: pulseDot 2.5s ease-in-out infinite; }
    .font-title { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13px; font-weight: 700; fill: #ffffff; letter-spacing: 0.5px; }
    .font-sub { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: 400; fill: #888888; }
    .font-badge { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 9px; font-weight: 600; fill: #a0a0a0; letter-spacing: 1px; text-transform: uppercase; }
  </style>
  <rect x="0.5" y="0.5" width="399" height="139" rx="14" fill="#050505" stroke="#242424"/>
  <g transform="translate(18, 16)">
    <rect x="0" y="0" width="102" height="20" rx="10" fill="#121212" stroke="#2a2a2a"/>
    <circle class="zen-dot" cx="10" cy="10" r="4" fill="#ffffff"/>
    <text x="20" y="13.5" class="font-badge">STUDIO MODE</text>
    <path class="ambient-line" d="M 260 10 Q 280 4, 300 10 T 340 10 T 364 10" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round"/>
  </g>
  <g transform="translate(18, 48)">
    <rect x="0" y="0" width="104" height="66" rx="7" fill="#111111" stroke="#2a2a2a" stroke-width="1.5"/>
    <rect x="6" y="6" width="92" height="54" rx="4" fill="#161616" stroke="#222222"/>
    <path d="M 12 12 L 92 12 L 86 54 L 18 54 Z" fill="#0a0a0a" stroke="#262626" stroke-width="1"/>
    <rect x="26" y="20" width="52" height="26" rx="13" fill="#141414" stroke="#2e2e2e"/>
    <rect x="34" y="31" width="36" height="4" fill="#222222"/>
    <g class="reel-left">
      <circle cx="52" cy="70" r="8" fill="#000000" stroke="#444444" stroke-width="1.5"/>
      <circle cx="52" cy="70" r="3" fill="#ffffff"/>
      <line x1="52" y1="62" x2="52" y2="78" stroke="#ffffff" stroke-width="1"/>
      <line x1="44" y1="70" x2="60" y2="70" stroke="#ffffff" stroke-width="1"/>
    </g>
    <g class="reel-right">
      <circle cx="88" cy="70" r="8" fill="#000000" stroke="#444444" stroke-width="1.5"/>
      <circle cx="88" cy="70" r="3" fill="#ffffff"/>
      <line x1="88" y1="62" x2="88" y2="78" stroke="#ffffff" stroke-width="1"/>
      <line x1="80" y1="70" x2="96" y2="70" stroke="#ffffff" stroke-width="1"/>
    </g>
  </g>
  <g transform="translate(142, 58)">
    <text x="0" y="14" class="font-title">OFFLINE // CODING IN SILENCE</text>
    <text x="0" y="32" class="font-sub">Crafting at balajitechlabs • Pure Focus</text>
    <rect x="0" y="42" width="238" height="4" rx="2" fill="#1c1c1c"/>
    <rect class="ambient-line" x="0" y="42" width="70" height="4" rx="2" fill="#ffffff"/>
    <text x="0" y="60" class="font-badge" fill="#555555">MUSIC ENGINE IDLE • WAITING FOR BIT CHORD</text>
  </g>
</svg>`;
}

function renderPlayingSvg(title, artist, appName, imgDataUri, elapsedSec, totalSec) {
  const percent = Math.min(100, Math.max(0, (elapsedSec / totalSec) * 100));
  const remainingSec = Math.max(1, totalSec - elapsedSec);
  const elapsedStr = formatTime(elapsedSec);
  const totalStr = formatTime(totalSec);

  const artworkMarkup = imgDataUri
    ? `<clipPath id="artClip"><rect x="0" y="0" width="72" height="72" rx="10"/></clipPath>
       <image href="${imgDataUri}" width="72" height="72" clip-path="url(#artClip)" preserveAspectRatio="xMidYMid slice"/>
       <rect x="0" y="0" width="72" height="72" rx="10" fill="none" stroke="#282828" stroke-width="1"/>`
    : `<rect x="0" y="0" width="72" height="72" rx="10" fill="#141414" stroke="#282828"/>
       <circle cx="36" cy="36" r="30" fill="#0a0a0a" stroke="#1f1f1f" stroke-width="1.5"/>
       <circle cx="36" cy="36" r="22" fill="none" stroke="#262626" stroke-width="1"/>
       <circle cx="36" cy="36" r="14" fill="none" stroke="#333333" stroke-width="1"/>
       <circle cx="36" cy="36" r="7" fill="#ffffff"/>
       <circle cx="36" cy="36" r="2.5" fill="#000000"/>`;

  return `<svg width="400" height="140" viewBox="0 0 400 140" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    @keyframes eq1 { 0%, 100% { height: 4px; y: 14px; } 50% { height: 16px; y: 2px; } }
    @keyframes eq2 { 0%, 100% { height: 16px; y: 2px; } 50% { height: 5px; y: 13px; } }
    @keyframes eq3 { 0%, 100% { height: 8px; y: 10px; } 50% { height: 18px; y: 0px; } }
    @keyframes eq4 { 0%, 100% { height: 17px; y: 1px; } 50% { height: 6px; y: 12px; } }
    @keyframes eq5 { 0%, 100% { height: 6px; y: 12px; } 50% { height: 15px; y: 3px; } }
    @keyframes pulseLive { 0%, 100% { transform: scale(1); opacity: 0.9; } 50% { transform: scale(1.3); opacity: 0.4; } }
    @keyframes liveProgress { from { width: ${percent.toFixed(1)}%; } to { width: 100%; } }
    .eq-bar-1 { animation: eq1 0.85s ease-in-out infinite; }
    .eq-bar-2 { animation: eq2 0.7s ease-in-out infinite; }
    .eq-bar-3 { animation: eq3 0.95s ease-in-out infinite; }
    .eq-bar-4 { animation: eq4 0.65s ease-in-out infinite; }
    .eq-bar-5 { animation: eq5 0.8s ease-in-out infinite; }
    .live-dot { transform-origin: 10px 10px; animation: pulseLive 1.8s ease-in-out infinite; }
    .progress-fill { animation: liveProgress ${remainingSec}s linear infinite; }
    .font-title { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; font-weight: 700; fill: #ffffff; letter-spacing: 0.3px; }
    .font-sub { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 12px; font-weight: 400; fill: #999999; }
    .font-time { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 10px; font-weight: 500; fill: #777777; }
    .font-badge { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 9px; font-weight: 600; fill: #ffffff; letter-spacing: 1px; text-transform: uppercase; }
  </style>
  <rect x="0.5" y="0.5" width="399" height="139" rx="14" fill="#050505" stroke="#2a2a2a"/>
  <g transform="translate(18, 14)">
    <rect x="0" y="0" width="108" height="20" rx="10" fill="#121212" stroke="#2a2a2a"/>
    <circle class="live-dot" cx="10" cy="10" r="3.5" fill="#ffffff"/>
    <text x="20" y="13.5" class="font-badge">NOW PLAYING</text>
    <g transform="translate(340, 2)">
      <rect class="eq-bar-1" x="0" y="8" width="3" height="10" rx="1.5" fill="#ffffff"/>
      <rect class="eq-bar-2" x="5" y="2" width="3" height="16" rx="1.5" fill="#ffffff"/>
      <rect class="eq-bar-3" x="10" y="4" width="3" height="14" rx="1.5" fill="#ffffff"/>
      <rect class="eq-bar-4" x="15" y="1" width="3" height="17" rx="1.5" fill="#ffffff"/>
      <rect class="eq-bar-5" x="20" y="7" width="3" height="11" rx="1.5" fill="#ffffff"/>
    </g>
  </g>
  <g transform="translate(18, 46)">
    ${artworkMarkup}
  </g>
  <g transform="translate(104, 52)">
    <text x="0" y="14" class="font-title">${escapeXml(title)}</text>
    <text x="0" y="32" class="font-sub">${escapeXml(artist)} • ${escapeXml(appName)}</text>
    <g transform="translate(0, 44)">
      <rect x="0" y="0" width="276" height="5" rx="2.5" fill="#1c1c1c"/>
      <rect class="progress-fill" x="0" y="0" width="${percent.toFixed(1)}%" height="5" rx="2.5" fill="#ffffff"/>
      <text x="0" y="18" class="font-time">${elapsedStr}</text>
      <text x="276" y="18" text-anchor="end" class="font-time">${totalStr}</text>
    </g>
  </g>
</svg>`;
}
