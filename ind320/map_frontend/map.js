/* Keep Leaflet and its tiles alive across Streamlit reruns. */
(() => {
  let map, layer, args, activeGeometry, revision = 0, timer;
  const geometries = new Map();
  const send = (type, payload) => window.parent.postMessage({isStreamlitMessage: true, type, ...payload}, '*');
  const currentStyle = feature => {
    const label = feature.properties[args.field];
    const area = args.areas[label];
    return {...area.style, color: label === args.selected ? '#FFAD75' : '#92A9BC',
      weight: label === args.selected ? 3 : 1};
  };
  function tooltip(label) {
    const area = args.areas[label];
    const table = document.createElement('table');
    for (const [name, value] of [['Area', label], [area.unit, area.value]]) {
      const row = table.insertRow();
      const heading = document.createElement('th'); heading.textContent = name;
      row.appendChild(heading); row.insertCell().textContent = value;
    }
    return table;
  }
  function publish(label = args.selected) {
    clearTimeout(timer);
    const center = map.getCenter();
    send('streamlit:setComponentValue', {dataType: 'json', value: {
      label, field: args.field, center: {lat: center.lat, lng: center.lng}, zoom: map.getZoom()
    }});
  }
  function updateLayers() {
    layer.eachLayer(item => {
      item.setStyle(currentStyle(item.feature));
      item.setTooltipContent(tooltip(item.feature.properties[args.field]));
    });
  }
  async function decode(boundary) {
    if (!geometries.has(boundary.id)) {
      const bytes = Uint8Array.from(atob(boundary.gzip), c => c.charCodeAt(0));
      const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
      geometries.set(boundary.id, await new Response(stream).json());
    }
    return geometries.get(boundary.id);
  }
  async function render(next) {
    args = next;
    const serial = ++revision;
    document.getElementById('map').style.height = `${args.height}px`;
    send('streamlit:setFrameHeight', {height: args.height});
    if (!map) {
      map = L.map('map', {scrollWheelZoom: false}).setView(args.center, args.zoom);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);
      L.control.scale().addTo(map);
      map.on('moveend', () => {clearTimeout(timer); timer = setTimeout(() => publish(), 180);});
      new ResizeObserver(() => map.invalidateSize({pan: false})).observe(document.getElementById('map'));
    }
    if (activeGeometry !== args.boundary.id) {
      const geo = await decode(args.boundary);
      if (serial !== revision) return;
      if (layer) map.removeLayer(layer);
      layer = L.geoJSON(geo, {
        style: currentStyle,
        onEachFeature(feature, item) {
          const label = feature.properties[args.field];
          item.bindTooltip(tooltip(label), {sticky: false, className: 'foliumtooltip'});
          item.on('click', () => {
            args = {...args, selected: label};
            updateLayers(); // Immediate outline; do not wait for the server.
            publish(label); // Send only the label, never the polygon coordinates.
          });
        }
      }).addTo(map);
      activeGeometry = args.boundary.id;
    } else updateLayers();
    document.getElementById('error').style.display = 'none';
  }
  window.addEventListener('message', event => {
    if (event.source !== window.parent || event.data?.type !== 'streamlit:render') return;
    render(event.data.args).catch(error => {
      const box = document.getElementById('error');
      box.textContent = 'The map could not load. Please refresh the page.';
      box.style.display = 'block'; console.error(error);
    });
  });
  send('streamlit:componentReady', {apiVersion: 1});
})();
