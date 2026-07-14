#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geojson_to_js.py
Convierte archivos .geojson a .js con el patron window.<NOMBRE>_DATA,
listos para servir a visores web (Leaflet, MapLibre, etc.) via <script src=...>.

Uso:
    python geojson_to_js.py                # convierte todos los .geojson de ./data a ./data/js
    python geojson_to_js.py -i data -o docs/js
    python geojson_to_js.py -p 5           # redondear coordenadas a 5 decimales (~1 m)

En el HTML del visor:
    <script src="https://.../radios_nbi_data.js"></script>
    L.geoJSON(window.RADIOS_NBI_DATA).addTo(map);
"""

import argparse
import json
import re
from pathlib import Path


def round_coords(obj, precision):
    """Redondea recursivamente todas las coordenadas de una geometria."""
    if isinstance(obj, float):
        return round(obj, precision)
    if isinstance(obj, list):
        return [round_coords(v, precision) for v in obj]
    return obj


def to_var_name(stem):
    """radios_nbi -> RADIOS_NBI_DATA (identificador JS valido)."""
    name = re.sub(r"\W+", "_", stem).strip("_").upper()
    if name and name[0].isdigit():
        name = "_" + name
    return f"{name}_DATA"


def convert(src, dst_dir, precision=None):
    with open(src, encoding="utf-8") as f:
        gj = json.load(f)

    if precision is not None:
        for feat in gj.get("features", []):
            geom = feat.get("geometry")
            if geom and "coordinates" in geom:
                geom["coordinates"] = round_coords(geom["coordinates"], precision)

    var = to_var_name(src.stem)
    dst = dst_dir / f"{src.stem}_data.js"
    body = json.dumps(gj, ensure_ascii=False, separators=(",", ":"))
    dst.write_text(f"window.{var} = {body};\n", encoding="utf-8")

    kb_in, kb_out = src.stat().st_size / 1024, dst.stat().st_size / 1024
    n = len(gj.get("features", []))
    print(f"  {src.name:40s} -> {dst.name:40s} window.{var:35s} {n:4d} features  {kb_in:7.0f} KB -> {kb_out:7.0f} KB")
    return dst


def main():
    ap = argparse.ArgumentParser(description="GeoJSON -> JS (window.<NOMBRE>_DATA)")
    ap.add_argument("-i", "--input", default="data", help="carpeta de entrada (default: data)")
    ap.add_argument("-o", "--output", default=None, help="carpeta de salida (default: <input>/js)")
    ap.add_argument("-p", "--precision", type=int, default=6,
                    help="decimales de coordenadas (default: 6 ~ 0.1 m; usar -1 para no redondear)")
    args = ap.parse_args()

    in_path = Path(args.input)
    if in_path.is_file():
        files = [in_path]
        in_dir = in_path.parent
    else:
        in_dir = in_path
        files = sorted(in_dir.glob("*.geojson"))
    out_dir = Path(args.output) if args.output else in_dir / "js"
    out_dir.mkdir(parents=True, exist_ok=True)
    precision = None if args.precision < 0 else args.precision
    if not files:
        print(f"No se encontraron .geojson en {in_dir.resolve()}")
        return

    print(f"Convirtiendo {len(files)} capas de {in_dir} a {out_dir} (precision={precision}):")
    for src in files:
        convert(src, out_dir, precision)
    print("Listo.")


if __name__ == "__main__":
    main()
