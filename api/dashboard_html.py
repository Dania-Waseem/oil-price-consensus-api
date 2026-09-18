DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>WTI Consensus Oracle</title>
<style>
  :root {
    --bg: #F4F1FB;
    --card: #FFFFFF;
    --text: #33313D;
    --muted: #7A7686;
    --blue: #E8F1FC;
    --blue-text: #2C5C8A;
    --green: #E9F7EE;
    --green-text: #2F6E4A;
    --amber: #FDF3E3;
    --amber-text: #8A6620;
    --border: #E4E0F0;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, Segoe UI, Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 32px 24px;
  }
  h1 {
    font-size: 22px;
    font-weight: 600;
    margin: 0 0 4px 0;
  }
  .subtitle {
    color: var(--muted);
    font-size: 14px;
    margin-bottom: 24px;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    max-width: 900px;
  }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
  }
  .card h2 {
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--muted);
    margin: 0 0 10px 0;
    font-weight: 600;
  }
  .price {
    font-size: 32px;
    font-weight: 700;
  }
  .price-unit {
    font-size: 14px;
    color: var(--muted);
    margin-left: 6px;
  }
  .row {
    display: flex;
    justify-content: space-between;
    font-size: 14px;
    padding: 4px 0;
  }
  .row span:first-child { color: var(--muted); }
  .pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
  }
  .pill-green { background: var(--green); color: var(--green-text); }
  .pill-amber { background: var(--amber); color: var(--amber-text); }
  .pill-blue { background: var(--blue); color: var(--blue-text); }
  .source-item {
    font-size: 13px;
    padding: 6px 0;
    border-bottom: 1px solid var(--border);
  }
  .source-item:last-child { border-bottom: none; }
  .warning-item {
    font-size: 13px;
    background: var(--amber);
    color: var(--amber-text);
    border-radius: 8px;
    padding: 8px 10px;
    margin-bottom: 6px;
  }
  .status-line {
    font-size: 13px;
    color: var(--muted);
    margin-top: 20px;
  }
  .empty {
    font-size: 13px;
    color: var(--muted);
  }
</style>
</head>
<body>

  <h1>WTI consensus oracle</h1>
  <div class="subtitle">Live oil price, cross-checked across two sources</div>

  <div class="grid">
    <div class="card">
      <h2>Price</h2>
      <div id="price" class="price">-</div>
    </div>

    <div class="card">
      <h2>Freshness</h2>
      <div class="row"><span>Age</span><span id="age">-</span></div>
      <div class="row"><span>Status</span><span id="stale-pill">-</span></div>
    </div>

    <div class="card">
      <h2>Trust</h2>
      <div class="row"><span>Confidence</span><span id="confidence">-</span></div>
      <div class="row"><span>Quality</span><span id="quality">-</span></div>
      <div class="row"><span>Verified</span><span id="verified-pill">-</span></div>
    </div>

    <div class="card">
      <h2>Sources</h2>
      <div id="sources" class="empty">-</div>
    </div>
  </div>

  <div class="card" style="max-width: 900px; margin-top: 16px;">
    <h2>Warnings</h2>
    <div id="warnings" class="empty">No warnings</div>
  </div>

  <div class="status-line" id="status-line">Loading ...</div>

<script>
async function refresh() {
  const statusLine = document.getElementById("status-line");
  try {
    const resp = await fetch("/v1/energy/commodity/price?commodity=WTI");
    const body = await resp.json();

    if (resp.status !== 200) {
      statusLine.textContent = "Waiting for data: " + (body.detail || "not available yet");
      return;
    }

    const data = body.data;
    const meta = body.meta;

    document.getElementById("price").innerHTML =
      "$" + data.price + '<span class="price-unit">' + data.currency + " / " + data.unit + "</span>";

    document.getElementById("age").textContent = meta.freshness.age_seconds + "s";

    const stalePill = document.getElementById("stale-pill");
    if (meta.freshness.stale) {
      stalePill.innerHTML = '<span class="pill pill-amber">Stale</span>';
    } else {
      stalePill.innerHTML = '<span class="pill pill-green">Fresh</span>';
    }

    document.getElementById("confidence").textContent = meta.trust.confidence;
    document.getElementById("quality").textContent = meta.trust.quality_score;

    const verifiedPill = document.getElementById("verified-pill");
    verifiedPill.innerHTML = meta.trust.verified
      ? '<span class="pill pill-green">Yes</span>'
      : '<span class="pill pill-amber">No</span>';

    const sourcesDiv = document.getElementById("sources");
    sourcesDiv.innerHTML = "";
    meta.provenance.forEach((p) => {
      const item = document.createElement("div");
      item.className = "source-item";
      item.textContent = p.publisher;
      sourcesDiv.appendChild(item);
    });

    const warningsDiv = document.getElementById("warnings");
    warningsDiv.innerHTML = "";
    if (meta.warnings.length === 0) {
      warningsDiv.innerHTML = '<div class="empty">No warnings</div>';
    } else {
      meta.warnings.forEach((w) => {
        const item = document.createElement("div");
        item.className = "warning-item";
        item.textContent = w;
        warningsDiv.appendChild(item);
      });
    }

    statusLine.textContent = "Last updated: " + new Date().toLocaleTimeString();
  } catch (err) {
    statusLine.textContent = "Could not reach API: " + err;
  }
}

refresh();
setInterval(refresh, 5000);
</script>

</body>
</html>
"""