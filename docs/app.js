// UI for the NYC transit map dashboard. Plotly owns only the map layer;
// everything else is vanilla JS. Day data comes from MTASource (live API,
// see sources/mta.js) with the prebuilt data/<event>/ JSON as fallback.

// Ridership heat scale: small & blue = quiet, big & red = surge.
const HEAT = [
  [0.0, "#2c5f8a"],
  [0.25, "#4c9bd1"],
  [0.5, "#f2d06b"],
  [0.75, "#ef8a3c"],
  [1.0, "#e4342b"],
];
const MAX_BUBBLE_PX = 46;
const COLOR_MAX = 15000; // colorbar/heat range caps here regardless of the true max

const ICON_PLAY = `<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="6 3 20 12 6 21 6 3"/></svg>`;
const ICON_PAUSE = `<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="5" y="3" width="5" height="18" rx="1"/><rect x="14" y="3" width="5" height="18" rx="1"/></svg>`;

// Official MTA line colors — tint each station's hover pop-up by the line it
// serves (parsed from the "(A,C,E)" suffix in the station name).
const MTA_LINE = {
  1: "#D82233",
  2: "#D82233",
  3: "#D82233", // red
  4: "#009952",
  5: "#009952",
  6: "#009952", // dark green
  7: "#9A38A1", // purple
  A: "#0078C6",
  C: "#0078C6",
  E: "#0078C6", // blue
  B: "#EB6800",
  D: "#EB6800",
  F: "#EB6800",
  M: "#EB6800", // orange
  G: "#799534", // light green
  J: "#8E5C33",
  Z: "#8E5C33", // brown
  L: "#7C858C",
  S: "#7C858C", // grey
  N: "#F6BC26",
  Q: "#F6BC26",
  R: "#F6BC26",
  W: "#F6BC26", // yellow
  T: "#008EB7",
  SIR: "#008EB7", // teal / SIR
};
const MTA_DEFAULT = "#0062CF"; // ISA blue, used when a name has no parseable line
// Yellow needs dark text for contrast; everything else takes white.
const DARK_TEXT_ON = new Set(["#F6BC26"]);

// Multi-line hubs pick one of their lines at random per day, instead of
// always favoring whichever line sorts first.
function lineColorFor(name) {
  if (state.stationColorCache[name]) return state.stationColorCache[name];
  const m = name.match(/\(([^)]+)\)/); // grab the "(A,C,E)" group
  let color = MTA_DEFAULT;
  if (m) {
    const lines = m[1].split(",").map((s) => s.trim().toUpperCase());
    const pick = lines[Math.floor(Math.random() * lines.length)];
    color = MTA_LINE[pick] || MTA_DEFAULT;
  }
  state.stationColorCache[name] = color;
  return color;
}

const state = {
  manifest: null,
  day: null,
  dayCache: {},
  stationColorCache: {},
  hour: 20,
  playing: null,
  plotted: false,
};

const $ = (id) => document.getElementById(id);
const fmt = (n) => n.toLocaleString("en-US");
const money = (n) => "$" + Math.round(n).toLocaleString("en-US");
const hourLabel = (h) => {
  const ampm = h < 12 ? "AM" : "PM";
  const h12 = h % 12 === 0 ? 12 : h % 12;
  return `${h12} ${ampm}`;
};

async function loadEvent(eventId) {
  state.dayCache = {};
  state.plotted = false;
  const manifest = await fetch(`data/${eventId}/manifest.json`).then((r) =>
    r.json(),
  );
  state.manifest = manifest;
  buildDayTabs();
  $("dataPanel").classList.add("hidden");
  const first =
    manifest.days.find((d) => d.hasData && d.day_type === "Home game") ||
    manifest.days.find((d) => d.hasData);
  await selectDay(first.date);
}

// Cross-day comparison charts: total riders and estimated revenue per day,
// drawn straight from the manifest (no per-day file fetches needed).
function renderComparisonCharts() {
  const days = state.manifest.days.filter((d) => d.hasData);
  const dates = days.map((d) => d.label);
  const riders = days.map((d) => d.total);
  const revenue = days.map((d) => Math.round(d.total * state.manifest.fare));
  // Neutral two-tone: game days read lighter than the no-game baseline.
  const barColors = days.map((d) => (d.matchup ? "#fafafa" : "#52525b"));

  const baseLayout = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { l: 48, r: 12, t: 8, b: 40 },
    font: { color: "#a1a1aa", size: 10 },
    xaxis: { tickfont: { size: 9 }, gridcolor: "rgba(255,255,255,0.08)" },
    yaxis: { gridcolor: "rgba(255,255,255,0.08)" },
    showlegend: false,
  };

  Plotly.newPlot(
    "chartRidership",
    [
      {
        type: "bar",
        x: dates,
        y: riders,
        marker: { color: barColors },
        hovertemplate: "%{x}<br>%{y:,} riders<extra></extra>",
      },
    ],
    baseLayout,
    { displayModeBar: false, responsive: true },
  );

  Plotly.newPlot(
    "chartRevenue",
    [
      {
        type: "scatter",
        mode: "lines+markers",
        x: dates,
        y: revenue,
        line: { color: "#a1a1aa" },
        marker: { color: barColors, size: 6 },
        hovertemplate: "%{x}<br>$%{y:,.0f}<extra></extra>",
      },
    ],
    baseLayout,
    { displayModeBar: false, responsive: true },
  );
}

function toggleDataPanel() {
  const panel = $("dataPanel");
  const opening = panel.classList.contains("hidden");
  panel.classList.toggle("hidden");
  if (opening) renderComparisonCharts();
}

function buildDayTabs() {
  const wrap = $("days");
  wrap.innerHTML = "";
  for (const d of state.manifest.days) {
    const el = document.createElement("div");
    el.className =
      "day" + (d.matchup ? " game" : "") + (d.hasData ? "" : " nodata");
    el.dataset.date = d.date;
    el.title = d.detail || d.label;
    if (d.colors && d.colors.length) {
      el.style.borderBottomColor = d.colors[0];
    }
    el.innerHTML = `<div class="d-dow">${d.dow}</div><div class="d-date">${d.date.slice(8)}</div>`;
    if (d.hasData) el.addEventListener("click", () => selectDay(d.date));
    wrap.appendChild(el);
  }
}

// API-first: try the live MTA query, fall back to the prebuilt JSON.
async function loadDay(date) {
  try {
    const day = await MTASource.fetchDay(date, state.manifest.hours);
    console.info(`${date}: live MTA API`);
    return day;
  } catch (err) {
    console.info(`${date}: cached fallback (${err.message})`);
    return fetch(`data/${state.manifest.id}/${date}.json`).then((r) =>
      r.json(),
    );
  }
}

async function selectDay(date, autoplay = true) {
  if (!state.dayCache[date]) {
    state.dayCache[date] = await loadDay(date);
  }
  state.day = state.dayCache[date];
  state.stationColorCache = {}; // reshuffle multi-line hub colors for this day
  document.querySelectorAll(".day").forEach((el) => {
    const on = el.dataset.date === date;
    el.classList.toggle("active", on);
    if (on) el.scrollIntoView({ inline: "center", block: "nearest" });
  });
  state.hour = state.manifest.hours[0]; // start each day from the beginning
  renderMap();
  if (autoplay) startPlay();
  else stopPlay();
}

function frameArrays(day, hour) {
  const vals = day.frames[String(hour)] || [];
  const lat = [],
    lon = [],
    size = [],
    color = [],
    text = [],
    hbg = [],
    hfg = [];
  day.stations.forEach((s, i) => {
    const r = vals[i] || 0;
    if (r <= 0) return;
    const lc = lineColorFor(s[0]);
    lat.push(s[1]);
    lon.push(s[2]);
    size.push(r);
    color.push(r);
    text.push(`${s[0]}<br>${fmt(r)} riders · ${hourLabel(hour)}`);
    hbg.push(lc);
    hfg.push(DARK_TEXT_ON.has(lc) ? "#111" : "#fff");
  });
  return { lat, lon, size, color, text, hbg, hfg };
}

function renderMap() {
  const day = state.day,
    hour = state.hour,
    gmax = state.manifest.globalMax;
  const a = frameArrays(day, hour);

  if (!state.plotted) {
    const sizeref = (2.0 * gmax) / (MAX_BUBBLE_PX * MAX_BUBBLE_PX);
    const trace = {
      type: "scattermap",
      lat: a.lat,
      lon: a.lon,
      text: a.text,
      hovertemplate: "%{text}<extra></extra>",
      hoverlabel: {
        bgcolor: a.hbg,
        bordercolor: "rgba(255,255,255,0.6)",
        font: { color: a.hfg, size: 13 },
      },
      mode: "markers",
      marker: {
        size: a.size,
        sizemode: "area",
        sizeref,
        sizemin: 2,
        color: a.color,
        cmin: 0,
        cmax: COLOR_MAX,
        colorscale: HEAT,
        opacity: 0.82,
        colorbar: {
          title: {
            text: "riders/hr",
            side: "right",
            font: { color: "#a1a1aa" },
          },
          thickness: 12,
          x: 1,
          xpad: 6,
          len: 0.5,
          y: 0.5,
          bgcolor: "rgba(0,0,0,0)",
          tickfont: { color: "#a1a1aa" },
        },
      },
    };
    const layout = {
      map: {
        style: "carto-darkmatter",
        center: state.manifest.map.center,
        zoom: state.manifest.map.zoom,
      },
      margin: { l: 0, r: 0, t: 0, b: 0 },
      paper_bgcolor: "#09090b",
      showlegend: false,
    };
    Plotly.newPlot("map", [trace], layout, {
      displayModeBar: false,
      scrollZoom: true,
      responsive: true,
    });
    state.plotted = true;
  } else {
    // Update bubbles only -- leaves the user's pan/zoom untouched.
    Plotly.restyle(
      "map",
      {
        lat: [a.lat],
        lon: [a.lon],
        text: [a.text],
        "marker.size": [a.size],
        "marker.color": [a.color],
        "hoverlabel.bgcolor": [a.hbg],
        "hoverlabel.font.color": [a.hfg],
      },
      [0],
    );
  }
  updateStats();
}

function updateStats() {
  const day = state.day,
    hour = state.hour;
  const riders = (day.hourTotals && day.hourTotals[String(hour)]) || 0;
  $("statRiders").textContent = fmt(riders);
  $("statRevenue").textContent = money(riders * state.manifest.fare);
  $("statClock").textContent = hourLabel(hour);
  const meta = state.manifest.days.find((d) => d.date === day.date);
  $("statDay").textContent = meta ? meta.day_type : "";
  $("nowDate").textContent = meta ? meta.label : day.date;
  const chip = $("nowGame");
  chip.textContent = meta && meta.matchup ? meta.detail : "";
  if (meta && meta.colors && meta.colors.length) {
    chip.style.background = meta.colors[0];
  }
  const dayTotal = meta ? meta.total : 0;
  $("dayTotals").textContent =
    `${fmt(dayTotal)} riders today · ${money(dayTotal * state.manifest.fare)} today`;
  $("hourLabel").textContent = hourLabel(hour);
  $("hour").value = hour;
}

function setHour(h) {
  state.hour = h;
  if (state.day) renderMap();
}

function step() {
  const hours = state.manifest.hours;
  let h = state.hour + 1;
  if (h > hours[hours.length - 1]) h = hours[0]; // loop the day
  setHour(h);
}
function startPlay() {
  if (state.playing) clearInterval(state.playing);
  $("playBtn").innerHTML = ICON_PAUSE;
  state.playing = setInterval(step, 550);
}
function stopPlay() {
  if (state.playing) clearInterval(state.playing);
  state.playing = null;
  $("playBtn").innerHTML = ICON_PLAY;
}
function togglePlay() {
  if (state.playing) stopPlay();
  else startPlay();
}

function initControls(events) {
  const sel = $("eventSelect");
  events.forEach((e) => {
    const o = document.createElement("option");
    o.value = e.id;
    o.textContent = e.name;
    sel.appendChild(o);
  });
  sel.addEventListener("change", async () => {
    $("loading").textContent = "loading event…";
    $("loading").classList.remove("hidden");
    try {
      await loadEvent(sel.value);
      $("loading").classList.add("hidden");
    } catch (err) {
      $("loading").textContent = "No data built for this event yet.";
      console.error(err);
    }
  });
  $("hour").addEventListener("input", (e) => {
    stopPlay(); // manual scrub takes over from autoplay
    setHour(parseInt(e.target.value, 10));
  });
  $("playBtn").addEventListener("click", togglePlay);
  $("dataToggle").addEventListener("click", toggleDataPanel);
  $("dataClose").addEventListener("click", () =>
    $("dataPanel").classList.add("hidden"),
  );
  window.addEventListener("resize", () => Plotly.Plots.resize("map"));
}

async function main() {
  try {
    const events = await fetch("data/events.json").then((r) => r.json());
    initControls(events);
    await loadEvent(events[0].id);
  } catch (err) {
    $("loading").textContent =
      "Could not load event data. Run scripts/build.py first.";
    console.error(err);
    return;
  }
  $("loading").classList.add("hidden");
}

main();
