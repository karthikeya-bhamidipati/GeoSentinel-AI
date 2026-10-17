"""
GeoSentinel AI - Kaggle driver for the OSCD change-detection experiments.

  python scripts/kaggle_job.py data
      Downloads the official OSCD archives from the IMT hosts (parallel ranged
      requests), verifies their MD5 against TorchGeo and extracts them to
      /kaggle/working/oscd. Save the notebook version and attach its output to
      the training notebooks.

  python scripts/kaggle_job.py train --runs anchor:1 baseline:1
      Trains each run on its own GPU (T4 x2 -> two runs in parallel), then
      evaluates every checkpoint on the full OSCD test scenes. Checkpoints go to
      /kaggle/working/weights, results to /kaggle/working/results.
"""

import argparse
import glob
import hashlib
import os
import subprocess
import sys
import threading
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORK = Path("/kaggle/working")
OSCD_FILES = {
    "Onera Satellite Change Detection dataset - Images.zip":
        ("https://partage.imt.fr/index.php/s/gKRaWgRnLMfwMGo/download", "c50d4a2941da64e03a47ac4dec63d915"),
    "Onera Satellite Change Detection dataset - Train Labels.zip":
        ("https://partage.imt.fr/index.php/s/2D6n03k58ygBSpu/download", "4d2965af8170c705ebad3d6ee71b6990"),
    "Onera Satellite Change Detection dataset - Test Labels.zip":
        ("https://partage.imt.fr/index.php/s/gpStKn4Mpgfnr63/download", "8177d437793c522653c442aa4e66c617"),
}
ANCHOR_URL = ("https://media.githubusercontent.com/media/karthikeya-bhamidipati/GeoSentinel-AI/"
              "master/data/weights/deeplabv3plus_best.pt")
ANCHOR_SHA256 = "89700f1a4055a8b61b201b649d6704bed15a8442d77dfd16bef7bdc9be8ab312"
CHUNK = 8 * 1024 * 1024


def _size(url):
    req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return int(r.headers["Content-Range"].split("/")[-1])


def _get_range(url, start, end, part):
    for _ in range(40):
        have = part.stat().st_size if part.exists() else 0
        if have >= end - start + 1:
            return
        req = urllib.request.Request(url, headers={"Range": f"bytes={start + have}-{end}"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r, open(part, "ab") as f:
                while True:
                    buf = r.read(1 << 20)
                    if not buf:
                        break
                    f.write(buf)
        except Exception as e:  # retry on dropped connections
            print(f"    retry {part.name}: {e}", flush=True)
    raise RuntimeError(f"failed to download {part}")


def download(url, dest: Path, workers=16):
    total = _size(url)
    ranges = [(s, min(s + CHUNK, total) - 1) for s in range(0, total, CHUNK)]
    parts = [dest.parent / f".{dest.name}.part{i:04d}" for i in range(len(ranges))]
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda a: _get_range(url, *a), [(s, e, p) for (s, e), p in zip(ranges, parts)]))
    with open(dest, "wb") as f:
        for p in parts:
            f.write(p.read_bytes())
            p.unlink()


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def job_data():
    out = WORK / "oscd"
    out.mkdir(parents=True, exist_ok=True)
    for name, (url, digest) in OSCD_FILES.items():
        dest = out / name
        if not (dest.exists() and md5(dest) == digest):
            print(f"Downloading {name} ...", flush=True)
            download(url, dest)
        got = md5(dest)
        assert got == digest, f"MD5 mismatch for {name}: {got}"
        print(f"  OK {name} md5={got}", flush=True)
        zipfile.ZipFile(dest).extractall(out)
        dest.unlink()  # keep only the extracted folders in the output
    print("OSCD ready:", sorted(os.listdir(out)), flush=True)


def find_oscd():
    hits = glob.glob("/kaggle/input/**/Onera Satellite Change Detection dataset - Images", recursive=True)
    if not hits:
        raise SystemExit("Attach the OSCD data notebook output as an input to this notebook.")
    return str(Path(hits[0]).parent)


def get_anchor():
    dest = WORK / "weights" / "deeplabv3plus_best.pt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        urllib.request.urlretrieve(ANCHOR_URL, dest)
    h = hashlib.sha256(dest.read_bytes()).hexdigest()
    assert h == ANCHOR_SHA256, f"anchor SHA-256 mismatch: {h}"
    print("Anchor weights OK (sha256 verified)", flush=True)
    return dest


def _tee(proc, path, prefix):
    """Copy a training process's output to its log file; echo epoch and error lines to the notebook log."""
    keys = ("Epoch", "Train cities", "Validation cities", "Best checkpoint", "Error", "Traceback", "Seed set")
    with open(path, "w") as f:
        for line in proc.stdout:
            f.write(line)
            if any(k in line for k in keys):
                print(prefix, line.rstrip(), flush=True)


def job_train(runs, epochs, batch_size, workers):
    oscd = find_oscd()
    anchor = get_anchor()
    wdir, rdir = WORK / "weights", WORK / "results"
    rdir.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    procs = []
    for gpu, run in enumerate(runs):
        kind, seed = run.split(":")
        cmd = [py, str(REPO / "scripts" / "train_change.py"), "--oscd-root", oscd, "--deeplab-ckpt", str(anchor),
               "--out-dir", str(wdir), "--seed", seed, "--gpu", str(gpu % 2), "--epochs", str(epochs),
               "--batch-size", str(batch_size), "--num-workers", str(workers)]
        if kind == "baseline":
            cmd.append("--ablation")
        print("Launching:", " ".join(cmd), flush=True)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=REPO, text=True, bufsize=1)
        t = threading.Thread(target=_tee, args=(p, WORK / f"train_{kind}_seed{seed}.log", f"[{kind}:{seed}]"), daemon=True)
        t.start()
        procs.append((kind, seed, p, t))
    for kind, seed, p, t in procs:
        rc = p.wait()
        t.join()
        print(f"  {kind} seed {seed}: exit {rc}", flush=True)
        log_tail = (WORK / f"train_{kind}_seed{seed}.log").read_text().splitlines()[-15:]
        print("\n".join(log_tail), flush=True)
        if rc != 0:
            raise SystemExit(f"training failed: {kind} seed {seed}")

    for kind, seed, *_ in procs:
        ckpt = wdir / f"change_{kind}_seed{seed}.pt"
        cmd = [py, str(REPO / "scripts" / "evaluate_change_fullscene.py"), "--weights", str(ckpt),
               "--deeplab-weights", str(anchor), "--oscd-root", oscd, "--crop-seeds", "0", "1", "2",
               "--out", str(rdir / f"eval_{kind}_seed{seed}.json")]
        if kind == "baseline":
            cmd.append("--ablation")
        print("Evaluating:", ckpt.name, flush=True)
        subprocess.run(cmd, check=True, cwd=REPO)


def job_report(figure_city="lasvegas"):
    """Aggregate all seeds, pick the anchor run with the lowest *validation* loss and render Fig. 1."""
    import json
    import shutil
    import statistics

    import numpy as np
    import torch

    sys.path.insert(0, str(REPO))
    from scripts.evaluate_change_fullscene import load_model, predict_scene
    from scripts.train_change import load_scenes

    rdir = WORK / "report"
    rdir.mkdir(parents=True, exist_ok=True)
    evals = {Path(f).name: json.load(open(f)) for f in glob.glob("/kaggle/input/**/results/eval_*_seed*.json", recursive=True)}
    ckpts = {Path(f).name: f for f in glob.glob("/kaggle/input/**/weights/change_*_seed*.pt", recursive=True)}
    print("Found evaluations:", sorted(evals), flush=True)
    print("Found checkpoints:", sorted(ckpts), flush=True)

    summary, val = {}, {}
    for name, ev in sorted(evals.items()):
        kind, seed = name[5:-5].rsplit("_seed", 1)
        meta = torch.load(ckpts[f"change_{kind}_seed{seed}.pt"], map_location="cpu", weights_only=True)
        val[(kind, seed)] = {"val_loss": meta["val_loss"], "val_f1": meta["val_f1"], "epoch": meta["epoch"]}
        summary.setdefault(kind, {})[seed] = {"full_scene": ev["full_scene"], "per_city": ev["per_city"],
                                              "random_crops": ev["random_crops"], **val[(kind, seed)]}
    (rdir / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    for kind, seeds in summary.items():
        f1 = [s["full_scene"]["0.5"]["F1"] * 100 for s in seeds.values()]
        print(f"{kind}: F1@0.5 per seed {[round(x, 2) for x in f1]} mean {statistics.mean(f1):.2f}", flush=True)

    best_seed = min((s for k, s in val if k == "anchor"), key=lambda s: val[("anchor", s)]["val_loss"])
    best = ckpts[f"change_anchor_seed{best_seed}.pt"]
    print(f"Best anchor run by validation loss: seed {best_seed} {val[('anchor', best_seed)]}", flush=True)
    shutil.copy(best, rdir / "change_unet_best.pt")
    (rdir / "best_run.json").write_text(json.dumps({"seed": best_seed, **val[("anchor", best_seed)]}, default=float))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, _ = load_model(best, get_anchor(), False, device)
    scene = next(s for s in load_scenes(Path(find_oscd()), "test") if s[0] == figure_city)
    _, t1, t2, mask = scene
    pred = predict_scene(model, t1, t2, device) > 0.5

    def rgb(t):
        img = t[[2, 1, 0]].permute(1, 2, 0).numpy()
        lo, hi = np.percentile(img, 2), np.percentile(img, 98)
        return np.clip((img - lo) / (hi - lo + 1e-9), 0, 1)

    fig, axes = plt.subplots(1, 4, figsize=(16, 4.4))
    panels = [(rgb(t1), "a"), (rgb(t2), "b"), (mask.numpy() == 1, "c"), (pred, "d")]
    for ax, (img, label) in zip(axes, panels):
        ax.imshow(img, cmap=None if img.ndim == 3 else "gray", interpolation="nearest")
        ax.set_title(label, loc="left", fontweight="bold", fontsize=14)
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(rdir / "figure1.png", dpi=300, bbox_inches="tight")
    print("Figure 1 written for", figure_city, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job", choices=["data", "train", "report"])
    ap.add_argument("--runs", nargs="*", default=["anchor:1", "baseline:1"])
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    if args.job == "data":
        job_data()
    elif args.job == "report":
        job_report()
    else:
        job_train(args.runs, args.epochs, args.batch_size, args.workers)


if __name__ == "__main__":
    main()
