async function loadHeatmap() {
  const days = parseInt(document.getElementById('days').value, 10) || 2;
  const bucket = parseInt(document.getElementById('bucket').value, 10) || 5;
  const r = await fetch(`/api/heatmap_data?days=${days}&bucket=${bucket}`);
  const data = await r.json();

  const trace = {
    x: data.x,
    y: data.y,
    z: data.z,
    type: 'heatmap',
    hoverongaps: false,
    colorscale: 'RdBu',
    reversescale: true
  };

  const layout = {
    title: `SmartMoney Heatmap (alerts: ${data.meta.alerts})`,
    xaxis: { title: 'Λεπτό (0–95)' },
    yaxis: { title: 'Match ID', automargin: true },
    margin: { l: 120, r: 30, t: 40, b: 60 }
  };

  Plotly.newPlot('chart', [trace], layout, {responsive: true});
}

document.getElementById('reload').addEventListener('click', loadHeatmap);
window.addEventListener('load', loadHeatmap);
