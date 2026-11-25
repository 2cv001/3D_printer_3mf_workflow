# Vérificateur indépendant de la macro : pour chaque <item> d'un 3MF, calcule
# la boîte englobante de l'objet SUR LE PLATEAU (composants + transform),
# avec ElementTree (parseur XML réel, donc vérifie aussi que le XML est valide).
import zipfile, sys, re
import xml.etree.ElementTree as ET

CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
IDENT = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]


def tf(s):
    v = [float(x) for x in s.split()] if s else IDENT
    return v if len(v) == 12 else IDENT


def compose(a, b):  # a puis b
    r = []
    for i in range(3):
        for j in range(3):
            r.append(sum(a[i * 3 + k] * b[k * 3 + j] for k in range(3)))
    for j in range(3):
        r.append(sum(a[9 + k] * b[k * 3 + j] for k in range(3)) + b[9 + j])
    return r


def apply(m, p):
    x, y, z = p
    return (x * m[0] + y * m[3] + z * m[6] + m[9], x * m[1] + y * m[4] + z * m[7] + m[10],
            x * m[2] + y * m[5] + z * m[8] + m[11])


def names_from_cfg(z):
    names = {}
    for cfg in ("Metadata/model_settings.config", "Metadata/Slic3r_PE_model.config"):
        if cfg in z.namelist():
            root = ET.fromstring(z.read(cfg))
            for o in root.findall("object"):
                for md in o.findall("metadata"):
                    if md.get("key") == "name":
                        names.setdefault(o.get("id"), md.get("value"))
                        break
    return names


def world(path):
    with zipfile.ZipFile(path) as z:
        return _world(z)


def _world(z):
    roots = {}

    def root(name):
        if name not in roots:
            roots[name] = ET.fromstring(z.read(name))
        return roots[name]

    main = root("3D/3dmodel.model")
    names = names_from_cfg(z)
    out = []

    def objects(r):
        return {o.get("id"): o for o in r.iter(CORE + "object")}

    def meshes(fname, oid, m):
        o = objects(root(fname)).get(oid)
        if o is None:
            raise ValueError(f"objet {oid} absent de {fname}")
        mesh = o.find(CORE + "mesh")
        if mesh is not None:
            vs = [(float(v.get("x")), float(v.get("y")), float(v.get("z")))
                  for v in mesh.iter(CORE + "vertex")]
            nt = len(list(mesh.iter(CORE + "triangle")))
            yield [apply(m, p) for p in vs], nt
        comps = o.find(CORE + "components")
        if comps is not None:
            for c in comps.findall(CORE + "component"):
                p = None
                for k, v in c.attrib.items():
                    if k.endswith("path"):
                        p = v.lstrip("/")
                yield from meshes(p or fname, c.get("objectid"), compose(tf(c.get("transform")), m))

    for it in main.find(CORE + "build").findall(CORE + "item"):
        oid = it.get("objectid")
        o = objects(main)[oid]
        pts, ntri = [], 0
        for vs, nt in meshes("3D/3dmodel.model", oid, tf(it.get("transform"))):
            pts += vs
            ntri += nt
        xs, ys, zs = zip(*pts)
        out.append({"id": oid, "name": names.get(oid) or o.get("name"), "tri": ntri,
                    "min": (min(xs), min(ys), min(zs)), "max": (max(xs), max(ys), max(zs))})
    return out


def show(path):
    for o in world(path):
        mn, mx = o["min"], o["max"]
        c = [(a + b) / 2 for a, b in zip(mn, mx)]
        print(f"   id={o['id']:>3} {str(o['name'])[:28]:28} tri={o['tri']:6} "
              f"centre=({c[0]:8.3f},{c[1]:8.3f}) zmin={mn[2]:8.4f} taille=({mx[0]-mn[0]:.2f},{mx[1]-mn[1]:.2f},{mx[2]-mn[2]:.2f})")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p)
        show(p)
