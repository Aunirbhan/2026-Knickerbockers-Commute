// Live MTA data layer. Queries Socrata directly from the browser (public,
// keyless, CORS-enabled) and shapes one day into the same {stations, frames,
// hourTotals} object the prebuilt fallback files under data/<event>/ use.
const MTASource = (() => {
  const API = "https://data.ny.gov/resource/5wq4-mkjj.json";
  const TIMEOUT_MS = 6000; // past this, app.js falls back to the committed JSON
  const pad = (h) => String(h).padStart(2, "0");

  async function fetchDay(date, hours) {
    const hMin = hours[0];
    const hMax = hours[hours.length - 1];
    const params = new URLSearchParams({
      $select:
        "transit_timestamp, station_complex, latitude, longitude, sum(ridership) as ridership",
      $where: `transit_timestamp between '${date}T${pad(hMin)}:00:00' and '${date}T${pad(hMax)}:59:59'`,
      $group: "transit_timestamp, station_complex, latitude, longitude",
      $limit: "50000", // one NYC day is ~7.5k grouped rows — a single page
    });
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
    try {
      const resp = await fetch(`${API}?${params}`, { signal: ctrl.signal });
      if (!resp.ok) throw new Error(`Socrata ${resp.status}`);
      const rows = await resp.json();
      if (!rows.length) throw new Error("no rows for this day");
      return shape(date, rows, hours);
    } finally {
      clearTimeout(timer);
    }
  }

  function shape(date, rows, hours) {
    const stations = [];
    const index = {};
    for (const r of rows) {
      if (!(r.station_complex in index)) {
        index[r.station_complex] = stations.length;
        stations.push([
          r.station_complex,
          +(+r.latitude).toFixed(5),
          +(+r.longitude).toFixed(5),
        ]);
      }
    }
    const frames = {};
    const hourTotals = {};
    for (const h of hours) {
      frames[String(h)] = new Array(stations.length).fill(0);
      hourTotals[String(h)] = 0;
    }
    for (const r of rows) {
      // Timestamps arrive as "YYYY-MM-DDTHH:..." with no zone suffix; slice
      // the hour out rather than trusting Date() to guess a timezone.
      const h = String(parseInt(r.transit_timestamp.slice(11, 13), 10));
      if (!(h in frames)) continue;
      const v = Math.round(+r.ridership);
      frames[h][index[r.station_complex]] += v;
      hourTotals[h] += v;
    }
    return { date, stations, frames, hourTotals };
  }

  return { fetchDay };
})();
