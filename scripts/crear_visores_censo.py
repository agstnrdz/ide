#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crear_visores_censo.py
Genera un visor HTML por cada capa radios_* de layers_js, siguiendo las
normas de estilo de docs/visores_html (cabecera con logo, Argenmap IGN,
coropletas, popups, control de capas y leyenda).

Uso:  python scripts/crear_visores_censo.py
Salida: docs/visores_html/radios_*.html
"""

from pathlib import Path

BASE_JS   = "https://agstnrdz.github.io/ide/layers_censo_gpkg_geojson/layers_js"
LOGO      = "https://agstnrdz.github.io/ide/assets/img/logotipo_MCR_DGMIT_blanco.png"
CENTRO    = "[-45.83448112101565, -67.49450745314675]"
ZOOM      = 12
HEADER_BG = "#134768"
ATTRIB    = ("Instituto Geográfico Nacional + OpenStreetMap | "
             "Fuente: INDEC, 2022. Procesamiento: Modernización e Investigación Territorial")

# Paletas ColorBrewer (5 clases), coherentes con los visores existentes
PURPLES = "['#e8e0f5', '#c5aee8', '#9f7ed0', '#7b5ea7', '#4a2d7f']"
ORANGES = "['#feedde', '#fdbe85', '#fd8d3c', '#e6550d', '#a63603']"
REDS    = "['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15']"
GREENS  = "['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c']"
BLUES   = "['#eff3ff', '#bdd7e7', '#6baed6', '#2171b5', '#084594']"
DIVERG  = "['#2166ac', '#92c5de', '#f7f7f7', '#f4a582', '#b5546a']"

PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{titulo_pagina}</title>
  <style>html, body {{ margin:0; padding:0; }}</style>
</head>
<body>

<!-- ═══════════ COPIAR DESDE AQUÍ HASTA "FIN BLOQUE" EN ELEMENTOR (widget HTML) ═══════════ -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
  /* Popups compactos: fuerza el mismo interlineado dentro de WordPress */
  .leaflet-popup-content {{ line-height: 1.25 !important; margin: 8px 12px !important; }}
  .leaflet-popup-content p, .leaflet-popup-content b {{ line-height: 1.25 !important; margin: 0 !important; }}
  .leaflet-popup-content table td {{ line-height: 1.2 !important; padding-top: 0 !important; padding-bottom: 0 !important; }}
</style>

<div class="visor-geo" id="visor-{id}" style="max-width:100%;font-family:system-ui,Segoe UI,Roboto,sans-serif;border:1px solid #e2dfe8;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

  <!-- Cabecera del visor: título + descripción + logo -->
  <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;background:{header_bg};color:#fff;">
    <div>
      <div style="font-size:17px;font-weight:700;line-height:1.2;">{titulo}</div>
      <div style="font-size:12.5px;opacity:0.9;margin-top:2px;">{subtitulo}</div>
    </div>
    <img src="{logo}"
         alt="Logo" style="height:44px;width:auto;flex-shrink:0;margin-left:auto;" onerror="this.style.display='none'">
  </div>

  <div id="map-{id}" style="height:520px;"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="{js_url}"></script>

<script>
(function () {{
  const map = L.map('map-{id}').setView({centro}, {zoom});

  // Mapa base: Argenmap (IGN)
  L.tileLayer('https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/capabaseargenmap@EPSG%3A3857@png/{{z}}/{{x}}/{{-y}}.png', {{
    attribution: '{attrib}',
    minZoom: 3,
    maxZoom: 18
  }}).addTo(map);

  const breaks = {breaks};
  const colors = {colors};
  const labels = {labels};
  const nullColor = '#d0cdd6';

  function getColor(val) {{
    if (val == null || isNaN(val)) return nullColor;
    for (let i = breaks.length - 1; i >= 0; i--) if (val >= breaks[i]) return colors[i + 1];
    return colors[0];
  }}

  // Valor que pinta la coropleta
  function valor(p) {{
    {valor_fn}
  }}

  const fmt = v => v != null ? Number(v).toLocaleString('es-AR', {{ maximumFractionDigits: 1 }}) : 'Sin dato';
  const pct = (v, t) => (t > 0 && v != null) ? (v / t * 100).toFixed(1) + '%' : '—';

  function makePopup(p) {{
    {popup_fn}
  }}

  const estilo = feat => ({{
    fillColor:   getColor(valor(feat.properties)),
    fillOpacity: 0.75,
    color:       '#070707',
    weight:      1,
    opacity:     0.5
  }});

  const capa = L.geoJSON(window.{var_js}, {{
    style: estilo,
    onEachFeature: (feat, layer) => {{
      layer.bindPopup(makePopup(feat.properties), {{ maxWidth: 300 }});
      layer.on('mouseover', () => layer.setStyle({{ fillOpacity: 0.75, weight: 3 }}));
      layer.on('mouseout',  () => layer.setStyle(estilo(feat)));
    }}
  }}).addTo(map);

  // Control para activar/desactivar la capa
  L.control.layers(null, {{ '{capa_label}': capa }}, {{ collapsed: false }}).addTo(map);

  // Leyenda
  const legend = L.control({{ position: 'bottomright' }});
  legend.onAdd = function () {{
    const div = L.DomUtil.create('div', 'info legend');
    div.style.cssText = 'background:#fff;padding:8px 10px;border-radius:8px;font-size:12px;line-height:1.5;box-shadow:0 1px 4px rgba(0,0,0,0.3)';
    div.innerHTML = '<strong>{leyenda_titulo}</strong><br>';
    colors.forEach((c, i) => {{
      div.innerHTML += `<span style="display:inline-block;width:12px;height:12px;background:${{c}};margin-right:6px;border:1px solid #999"></span>${{labels[i]}}<br>`;
    }});
    div.innerHTML += `<span style="display:inline-block;width:12px;height:12px;background:${{nullColor}};margin-right:6px;border:1px solid #999"></span>Sin dato<br>`;
    return div;
  }};
  legend.addTo(map);
}})();
</script>
<!-- ═══════════ FIN BLOQUE ═══════════ -->

</body>
</html>
"""

SUB = "Comodoro Rivadavia — 325 radios censales (Censo 2022). Hacé clic en cada radio para ver el detalle."

VISORES = [
    {
        "archivo": "radios_poblacion_densidad", "id": "poblacion-densidad",
        "titulo_pagina": "Radios censales - Población y densidad",
        "titulo": "Población y densidad por radio censal", "subtitulo": SUB,
        "var_js": "RADIOS_POBLACION_DENSIDAD_DATA",
        "capa_label": "Población y densidad",
        "breaks": "[1500, 4000, 6000, 9500]", "colors": PURPLES,
        "labels": "['< 1.500', '1.500 – 4.000', '4.000 – 6.000', '6.000 – 9.500', '≥ 9.500']",
        "leyenda_titulo": "Densidad (hab/km²)",
        "valor_fn": "return p.densidad;",
        "popup_fn": """return `<b>Radio censal ${p.LINK}</b><br>` +
      `Población: ${fmt(p.totpob)} hab.<br>` +
      `Superficie: ${fmt(p.area_km2)} km²<br>` +
      `Densidad: ${fmt(p.densidad)} hab/km²`;""",
    },
    {
        "archivo": "radios_viviendas_densidad", "id": "viviendas-densidad",
        "titulo_pagina": "Radios censales - Viviendas y densidad",
        "titulo": "Viviendas y densidad por radio censal", "subtitulo": SUB,
        "var_js": "RADIOS_VIVIENDAS_DENSIDAD_DATA",
        "capa_label": "Viviendas y densidad",
        "breaks": "[500, 1750, 2500, 3500]", "colors": ORANGES,
        "labels": "['< 500', '500 – 1.750', '1.750 – 2.500', '2.500 – 3.500', '≥ 3.500']",
        "leyenda_titulo": "Densidad (viv/km²)",
        "valor_fn": "return p.dens_viv;",
        "popup_fn": """return `<b>Radio censal ${p.geo_id}</b><br>` +
      `Viviendas: ${fmt(p.viviendas)}<br>` +
      `Superficie: ${fmt(p.area_km2)} km²<br>` +
      `Densidad: ${fmt(p.dens_viv)} viv/km²`;""",
    },
    {
        "archivo": "radios_sexo", "id": "sexo",
        "titulo_pagina": "Radios censales - Distribución por sexo",
        "titulo": "Distribución por sexo por radio censal",
        "subtitulo": "Comodoro Rivadavia — 325 radios censales (Censo 2022). Azul: mayoría de varones · Rosa: mayoría de mujeres.",
        "var_js": "RADIOS_SEXO_DATA",
        "capa_label": "Distribución por sexo",
        "breaks": "[47, 49, 51, 53]", "colors": DIVERG,
        "labels": "['< 47 % mujeres', '47 – 49 %', '49 – 51 % (equilibrado)', '51 – 53 %', '≥ 53 % mujeres']",
        "leyenda_titulo": "% de mujeres",
        "valor_fn": "return p.porc_fem;",
        "popup_fn": """return `<b>Radio censal ${p.geo_id}</b><br>` +
      `Mujeres: ${fmt(p.femenino)} (${pct(p.femenino, p.total)})<br>` +
      `Varones: ${fmt(p.masculino)} (${pct(p.masculino, p.total)})<br>` +
      `Total: ${fmt(p.total)}<br>` +
      `Índice de feminidad: ${fmt(p.i_feminida)}`;""",
    },
    {
        "archivo": "radios_nbi", "id": "nbi",
        "titulo_pagina": "Radios censales - Hogares con NBI",
        "titulo": "Hogares con NBI por radio censal",
        "subtitulo": "Comodoro Rivadavia — 325 radios censales (Censo 2022). Necesidades Básicas Insatisfechas por hogar.",
        "var_js": "RADIOS_NBI_DATA",
        "capa_label": "Hogares con NBI",
        "breaks": "[2, 4, 6, 9]", "colors": REDS,
        "labels": "['< 2 %', '2 – 4 %', '4 – 6 %', '6 – 9 %', '≥ 9 %']",
        "leyenda_titulo": "% de hogares con NBI",
        "valor_fn": "return p.hogares > 0 ? p.nbi_si / p.hogares * 100 : null;",
        "popup_fn": """const pNbi = pct(p.nbi_si, p.hogares);
    return `<b>Radio censal ${p.geo_id}</b><br>` +
      `Hogares con NBI: ${fmt(p.nbi_si)} (${pNbi})<br>` +
      `Hogares sin NBI: ${fmt(p.nbi_no)}<br>` +
      `Total de hogares: ${fmt(p.hogares)}<br>` +
      `Densidad de hogares NBI: ${fmt(p.dens_nbi)} hog/km²`;""",
    },
    {
        "archivo": "radios_cobertura_salud", "id": "cobertura-salud",
        "titulo_pagina": "Radios censales - Cobertura de salud",
        "titulo": "Cobertura de salud por radio censal",
        "subtitulo": "Comodoro Rivadavia — 325 radios censales (Censo 2022). Población según tipo de cobertura de salud.",
        "var_js": "RADIOS_COBERTURA_SALUD_DATA",
        "capa_label": "Cobertura de salud",
        "breaks": "[15, 20, 25, 34]", "colors": REDS,
        "labels": "['< 15 %', '15 – 20 %', '20 – 25 %', '25 – 34 %', '≥ 34 %']",
        "leyenda_titulo": "% sin cobertura de salud",
        "valor_fn": "return p.porc_sin;",
        "popup_fn": """return `<b>Radio censal ${p.geo_id}</b><br>` +
      `Prepaga / obra social: ${fmt(p.salud_prep)} (${pct(p.salud_prep, p.pers_total)})<br>` +
      `Solo sistema estatal: ${fmt(p.salud_esta)} (${pct(p.salud_esta, p.pers_total)})<br>` +
      `Sin cobertura: ${fmt(p.salud_sin)} (${pct(p.salud_sin, p.pers_total)})<br>` +
      `Total relevado: ${fmt(p.pers_total)} personas`;""",
    },
    {
        "archivo": "radios_hogar_migrantes", "id": "hogar-migrantes",
        "titulo_pagina": "Radios censales - Hogares con integrantes migrantes",
        "titulo": "Hogares con integrantes migrantes por radio censal",
        "subtitulo": "Comodoro Rivadavia — 325 radios censales (Censo 2022). Hogares con al menos un integrante migrante.",
        "var_js": "RADIOS_HOGAR_MIGRANTES_DATA",
        "capa_label": "Hogares con migrantes",
        "breaks": "[7, 10, 13, 20]", "colors": GREENS,
        "labels": "['< 7 %', '7 – 10 %', '10 – 13 %', '13 – 20 %', '≥ 20 %']",
        "leyenda_titulo": "% de hogares con migrantes",
        "valor_fn": "return p.hog_porc_m;",
        "popup_fn": """return `<b>Radio censal ${p.geo_id}</b><br>` +
      `Hogares con migrantes: ${fmt(p.hog_migran)} (${pct(p.hog_migran, p.hog_total)})<br>` +
      `Hogares sin migrantes: ${fmt(p.hog_no_mig)}<br>` +
      `Total de hogares: ${fmt(p.hog_total)}`;""",
    },
    {
        "archivo": "radios_lugar_nacimiento", "id": "lugar-nacimiento",
        "titulo_pagina": "Radios censales - Lugar de nacimiento",
        "titulo": "Lugar de nacimiento por radio censal",
        "subtitulo": "Comodoro Rivadavia — 325 radios censales (Censo 2022). Población según lugar de nacimiento.",
        "var_js": "RADIOS_LUGAR_NACIMIENTO_DATA",
        "capa_label": "Lugar de nacimiento",
        "breaks": "[3, 5, 7, 10]", "colors": BLUES,
        "labels": "['< 3 %', '3 – 5 %', '5 – 7 %', '7 – 10 %', '≥ 10 %']",
        "leyenda_titulo": "% nacidos en otro país",
        "valor_fn": "return p.porc_extr;",
        "popup_fn": """return `<b>Radio censal ${p.geo_id}</b><br>` +
      `Nacidos en Chubut: ${fmt(p.nac_chubut)} (${pct(p.nac_chubut, p.pers_total)})<br>` +
      `Nacidos en otra provincia: ${fmt(p.nac_otra_p)} (${pct(p.nac_otra_p, p.pers_total)})<br>` +
      `Nacidos en otro país: ${fmt(p.nac_otro_p)} (${pct(p.nac_otro_p, p.pers_total)})<br>` +
      `Total relevado: ${fmt(p.pers_total)} personas`;""",
    },
]


def main():
    out_dir = Path(__file__).resolve().parent.parent / "docs" / "visores_html"
    out_dir.mkdir(parents=True, exist_ok=True)
    for v in VISORES:
        html = PLANTILLA.format(
            centro=CENTRO, zoom=ZOOM, header_bg=HEADER_BG, logo=LOGO, attrib=ATTRIB,
            js_url=f"{BASE_JS}/{v['archivo']}_data.js", **v,
        )
        dst = out_dir / f"{v['archivo']}.html"
        dst.write_text(html, encoding="utf-8")
        print(f"  {dst.name}")
    print(f"Listo: {len(VISORES)} visores en {out_dir}")


if __name__ == "__main__":
    main()
