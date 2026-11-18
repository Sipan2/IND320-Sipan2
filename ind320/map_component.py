"""Persistent Leaflet map: lossless boundaries and small selection events."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_component = components.declare_component(
    "reservoir_map", path=str(Path(__file__).with_name("map_frontend"))
)


@st.cache_data(show_spinner=False)
def boundary_payload(path, modified_ns):
    """Compress without rounding, simplifying or dropping any coordinates."""
    geo = json.loads(Path(path).read_text())
    raw = json.dumps(geo, separators=(",", ":"), ensure_ascii=False).encode()
    return {
        "id": hashlib.sha256(raw).hexdigest(),
        "gzip": base64.b64encode(gzip.compress(raw, mtime=0)).decode("ascii"),
    }


def reservoir_map(*, boundary, field, areas, selected, view, on_change):
    return _component(
        boundary=boundary, field=field, areas=areas, selected=selected,
        center=view.get("center", [65.0, 17.5]), zoom=view.get("zoom", 4),
        height=600, key="reservoir_map", default=None, on_change=on_change,
    )
