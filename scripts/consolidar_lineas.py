# -*- coding: utf-8 -*-
"""
Consolida los 23 archivos .js window (GeoJSON) de lineas de colectivo en un
unico lineas_data.js con el formato del visor (LINEAS_DATA), y convierte
paradas.gpkg a paradas_data.js (PARADAS_DATA).

- Une ida/vuelta por linea; 6H+6AH -> linea 6 (circular), 8H+8AH -> linea 8.
- Ordena ("cose") los tramos de cada MultiLineString por proximidad de
  extremos SIN invertir tramos (se asume digitalizacion en sentido de
  circulacion). Corta en paths separados si el hueco supera GAP_MAX m.
- Corrige linea=14 erroneo dentro de linea_15_data.js (manda el archivo).
- Normaliza Si/SI/No/-/'' de paradas a booleanos.
- Excluye paradas con coordenadas invalidas (fuera del rango de la ciudad).

Uso: python3 consolidar_lineas.py
"""
import json, re, glob, os, math, sqlite3, struct

BASE = os.path.dirname(os.path.abspath(__file__))
DIR_JS = os.path.join(BASE, "lineas", "js")
GPKG = os.path.join(BASE, "paradas.gpkg")
OUT_DIR = os.path.join(BASE, "..", "ide", "docs", "layers_transporte_lineas")
GAP_MAX = 150.0  # metros: hueco mayor => path separado

# Paleta (color claro / color modo oscuro) por linea, hues repartidos
PALETA = {
    "1":  ("#d62728", "#ff6b6b"), "2":  ("#1f77b4", "#5aa9e6"),
    "3":  ("#2ca02c", "#5fd068"), "4":  ("#9467bd", "#b78fe0"),
    "5":  ("#ff7f0e", "#ffa94d"), "5U": ("#8c564b", "#c9938a"),
    "6H": ("#e377c2", "#f2a6dd"), "6AH": ("#8e44ad", "#c39bd3"),
    "7":  ("#17becf", "#63dfee"),
    "8H": ("#bcbd22", "#d9db4f"), "8AH": ("#6b8e23", "#9acd32"),
    "9":  ("#7f2704", "#d95f02"),
    "12": ("#0d5b8c", "#4fa3d1"), "13": ("#a61e4d", "#e64980"),
    "14": ("#2b8a3e", "#69db7c"), "15": ("#5f3dc4", "#9775fa"),
    "16": ("#e8590c", "#ff922b"), "17": ("#0b7285", "#3bc9db"),
    "18": ("#862e9c", "#cc5de8"), "19": ("#c92a2a", "#ff8787"),
    "20": ("#364fc7", "#748ffc"), "21": ("#087f5b", "#38d9a9"),
    "22": ("#e67700", "#ffc078"),
}

def dist_m(a, b):
    # equirectangular, suficiente a escala urbana; a,b = (lng,lat)
    kx = 111320.0 * math.cos(math.radians(-45.86))
    return math.hypot((a[0]-b[0])*kx, (a[1]-b[1])*111320.0)

def coser(parts):
    """Ordena tramos encadenando fin->inicio sin invertirlos.
    Devuelve (lista de paths [lng,lat], hueco maximo interno)."""
    if len(parts) == 1:
        return [parts[0]], 0.0
    mejor, mejor_costo = None, None
    for inicio in range(len(parts)):
        usados = {inicio}
        orden = [inicio]
        costo = 0.0
        while len(usados) < len(parts):
            fin = parts[orden[-1]][-1]
            cand = min((i for i in range(len(parts)) if i not in usados),
                       key=lambda i: dist_m(fin, parts[i][0]))
            costo += dist_m(fin, parts[cand][0])
            usados.add(cand); orden.append(cand)
        if mejor_costo is None or costo < mejor_costo:
            mejor, mejor_costo = orden, costo
    paths, actual, gmax = [], list(parts[mejor[0]]), 0.0
    for i in mejor[1:]:
        g = dist_m(actual[-1], parts[i][0])
        if g > GAP_MAX:
            paths.append(actual); actual = list(parts[i])
        else:
            gmax = max(gmax, g)
            actual.extend(parts[i])
    paths.append(actual)
    return paths, gmax

def redondear(paths):
    # GeoJSON [lng,lat] -> visor [lat,lng], 6 decimales
    return [[[round(p[1], 6), round(p[0], 6)] for p in path] for path in paths]

def id_de_archivo(fname):
    return re.match(r"linea_(\w+?)_data\.js$", os.path.basename(fname)).group(1)

SENTIDOS = {
    "ida": ("Ida", "ida"), "vuelta": ("Vuelta", "vuelta"),
    "horario": ("Horario", "circular"), "antihorario": ("Antihorario", "circular"),
    "": ("Único", "unico"),
}
FUSION = {}  # cada archivo es una linea propia (23 lineas)
ORDEN_SENT = {"ida": 0, "vuelta": 1, "horario": 0, "antihorario": 1, "": 0}

def main():
    lineas = {}
    reporte = []
    for f in sorted(glob.glob(os.path.join(DIR_JS, "*_data.js"))):
        fid = id_de_archivo(f)
        lid = FUSION.get(fid, fid)
        txt = open(f, encoding="utf-8").read()
        body = re.match(r"window\.\w+\s*=\s*(\{.*)$", txt, re.S).group(1).rstrip().rstrip(";")
        gj = json.loads(body)
        for ft in gj["features"]:
            p, g = ft["properties"], ft["geometry"]
            sent = (p.get("sentido") or "").strip().lower()
            nombre = (p.get("nombre") or "").strip()
            parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
            parts = [pt for pt in parts if len(pt) >= 2]
            paths, gmax = coser(parts)
            reporte.append((lid, sent or "unico", len(parts), len(paths), round(gmax)))
            sdisp, tipo = SENTIDOS.get(sent, (sent.capitalize() or "Único", "ida"))
            L = lineas.setdefault(lid, {"id": lid, "nombre": nombre, "rutas": []})
            if nombre and (not L["nombre"] or sent in ("ida", "horario", "")):
                L["nombre"] = nombre
            L["rutas"].append({
                "id": f"{lid}-{sent or 'unico'}", "sentido": sdisp, "tipo": tipo,
                "_orden": ORDEN_SENT.get(sent, 9), "paths": redondear(paths),
            })
    for L in lineas.values():
        L["rutas"].sort(key=lambda r: r.pop("_orden"))
        c, cd = PALETA.get(L["id"], ("#555555", "#aaaaaa"))
        L["color"], L["colorDark"] = c, cd

    def clave(lid):
        m = re.match(r"(\d+)(\w*)", lid)
        return (int(m.group(1)), m.group(2))
    data = [lineas[k] for k in sorted(lineas, key=clave)]

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "lineas_data.js")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("// Generado por consolidar_lineas.py a partir de lineas/js/*_data.js — no editar a mano.\n")
        fh.write("window.LINEAS_DATA = ")
        fh.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        fh.write(";\n")
    print(f"{out}: {len(data)} lineas, {sum(len(l['rutas']) for l in data)} rutas, {os.path.getsize(out)//1024} KB")
    print("\nCosido (linea, sentido, tramos, paths_finales, hueco_max_unido_m):")
    for r in reporte:
        print("  %-4s %-11s %3d -> %2d  gap<=%dm" % r)

    # ── paradas ──
    db = sqlite3.connect(GPKG)
    cur = db.cursor()
    si = lambda v: str(v).strip().lower() in ("si", "sí")
    paradas = []
    for fid_, ID, calle, esq, poste, cartel, refugio, geom in cur.execute(
            "select fid, ID, Calle, Esquina, Poste, Cartel, Regufio, geom from paradas order by fid"):
        flags = geom[3]
        envlen = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(flags >> 1) & 7]
        wkb = geom[8 + envlen:]
        bo = "<" if wkb[0] == 1 else ">"
        x, y = struct.unpack(bo + "2d", wkb[5:21])
        if not (-68.0 < x < -67.0 and -46.2 < y < -45.0):
            print(f"  AVISO: parada fid={fid_} ({calle} esq. {esq}) con coordenadas invalidas "
                  f"({x}, {y}) — EXCLUIDA. Corregir en paradas.gpkg.")
            continue
        paradas.append({
            "id": int(fid_), "lat": round(y, 6), "lng": round(x, 6),
            "calle": (calle or "").strip() or "Calle sin nombre",
            "esquina": (esq or "").strip(),
            "poste": si(poste), "cartel": si(cartel), "refugio": si(refugio),
        })
    out2 = os.path.join(OUT_DIR, "paradas_data.js")
    with open(out2, "w", encoding="utf-8") as fh:
        fh.write("// Generado por consolidar_lineas.py a partir de paradas.gpkg — no editar a mano.\n")
        fh.write("window.PARADAS_DATA = ")
        fh.write(json.dumps(paradas, ensure_ascii=False, separators=(",", ":")))
        fh.write(";\n")
    print(f"\n{out2}: {len(paradas)} paradas, {os.path.getsize(out2)//1024} KB")

if __name__ == "__main__":
    main()
