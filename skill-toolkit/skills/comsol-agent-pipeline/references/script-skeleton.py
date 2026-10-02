"""<ROUND> - <one-line purpose> (COMSOL_Test-style round: a test rig, never a device claim).

Inputs: every number is tagged [L] library seed as shipped / [D] derivation or textbook / [E] labelled guess / [X?] a
number the source does not state (any [X?] caps the result label at `design-study`). Untagged numbers are defects.

Gates (each has a machine check; a control that cannot fire is not a control):
  G1  <physics gate vs an analytic/closed-form reference, tolerance stated>                                     [D]
  C1  control (must fire): <mechanism removed / wrong ruler> -> result must move by > X %
  I1  mesh / consistency gate evaluated in the SAME regime as the physics gate (R-GATE-REGIME)
  Rn  REPORT only (no tolerance) - written as "REPORT", never counted in the PASS total

Run: python <script>.py > runN.log 2>&1   (one process, mph.start(cores=8) per R-CORES; no GUI, no vision)
"""
import sys, time, json, pathlib
import numpy as np, jpype, mph
HERE = pathlib.Path(__file__).resolve().parent; OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
def step(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)
def err(e): return " | ".join(l.strip() for l in str(e).splitlines() if l.strip())[:400]

# ---------------- analytic reference (pure Python, no COMSOL) ----------------
def reference(**p):
    """Closed form the gate compares against. Keep it independent of the model (different code path, same units)."""
    raise NotImplementedError

# ---------------- model (seed-driven or from text) ----------------
def build(client, **p):
    """Seed route: model = client.load(SEED); m = model.java; m.param().set(...); rebuild geom/mesh if geometry changed.
    From-text route: client.create -> param -> geom (lengthUnit) -> BoxSelections (R-SEL) -> materials -> physics ->
    mesh -> study. Assert entity counts after geom.run() (R-SEL). Prefix parameter names (R-RESERVED-NAMES)."""
    model = client.create("m1"); m = model.java
    # ... build ...
    return model

def read_global(m, exprs, dset="dset1", tag="gev1"):
    """EvalGlobal: [expression][solution] (R-EVALGLOBAL-SHAPE, R-GLOBAL-READ)."""
    num = m.result().numerical()
    if tag not in [str(t) for t in num.tags()]: num.create(tag, "EvalGlobal")
    f = m.result().numerical(tag); f.set("expr", exprs); f.set("data", dset)
    return np.array(f.getReal(), dtype=float).reshape(len(exprs), -1)

def read_points(m, exprs, xs, ys=None, solnum=1, tag="interp1"):
    """Interp at points: coordinates in the GEOMETRY length unit (R-INTERP-UNIT); result is points x expressions
    (R-INTERP-SHAPE) -> returned as expressions x points."""
    num = m.result().numerical()
    if tag not in [str(t) for t in num.tags()]: num.create(tag, "Interp")
    f = m.result().numerical(tag); f.set("expr", exprs); f.set("solnum", str(solnum))
    cols = [[float(v) for v in xs]] + ([[float(v) for v in ys]] if ys is not None else [])
    f.setInterpolationCoordinates(jpype.JArray(jpype.JDouble, 2)(cols))
    return np.array(f.getReal(), dtype=float).reshape(len(xs), len(exprs)).T

# ---------------- verdict ----------------
def main():
    client = mph.start(cores=8); step(f"mph client {client.version}")
    # R-RESULT-JSON-SCHEMA: keep these top-level keys - page builders / inventory scripts read them, the log is the audit copy
    res = {"round": "<NN>", "item": "<Uxx>", "inputs": {}, "timings_s": {}}; lines = []; fails = []; undet = []
    t_start = time.time()
    def gate(name, ok, text):
        tag = "PASS" if ok else "FAIL"; lines.append(f"{tag}  {name}: {text}"); step(f"  {tag}  {name}: {text}")
        if not ok: fails.append(name)
    def report(name, text): step(f"  REPORT  {name}: {text}"); res.setdefault("reports", []).append(f"{name}: {text}")
    # 1. physics gate(s) ...   gate("G1 ...", abs(dev) <= tol, f"... ({dev:+.2f} %)")
    # 2. control(s): if the control does not separate, append to undet - a silent control is an UNDET verdict, not a PASS
    # 3. mesh gate in the physics gate's regime
    # 4. save: model.save(str(OUT / "x.mph")); tables/exports as %-header text (sap read); result json
    res["gates"] = lines; res["fails"] = fails; res["undet"] = undet
    res["verdict"] = "UNDET" if undet else ("FAIL" if fails else "PASS"); res["timings_s"]["total"] = time.time() - t_start
    (OUT / "result.json").write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
    n_pass = sum(l.startswith("PASS") for l in lines)
    step(f"VERDICT: {'PASS' if not fails and not undet else 'FAIL'} {n_pass}/{len(lines)} gates; fails={fails}; undet={undet}")
    return 2 if undet else (1 if fails else 0)

if __name__ == "__main__":
    sys.exit(main())
