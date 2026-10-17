"""
GeoSentinel AI - Deterministic full-scene OSCD evaluation
==========================================================
Scores a Siamese change model on every OSCD test city at full extent
(sliding window, 256 px tiles, stride 128, averaged change probability) and
pools the confusion matrix over all test pixels. Padding is never scored.
Preprocessing is shared with training (scripts/train_change.py: load_scenes).

Optionally repeats a random-crop protocol (10 random 256 px crops per test
city, argmax) with fixed seeds for comparison with patch-based scores.

Usage:
    python scripts/evaluate_change_fullscene.py --weights data/weights/change_anchor_seed42.pt \
        --deeplab-weights data/weights/deeplabv3plus_best.pt --oscd-root data/benchmark/oscd \
        [--ablation] [--crop-seeds 0 1 2] [--out outputs/eval.json]
"""

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.train_change import OSCD12ChannelDataset, load_scenes  # noqa: E402
from src.models.siamese import GeoSentinelSiameseUNet  # noqa: E402

TILE = 256
STRIDE = 128
THRESHOLDS = (0.5, 0.75)


def load_model(weights, deeplab_weights, ablation, device):
    model = GeoSentinelSiameseUNet(str(deeplab_weights), num_classes=2, ablation_mode=ablation)
    ckpt = torch.load(weights, map_location="cpu", weights_only=True)
    state = ckpt.get("state_dict", ckpt.get("model_state_dict", ckpt))
    own = set(model.state_dict())
    state = {(k[6:] if k not in own and k[6:] in own else k): v for k, v in state.items()}
    result = model.load_state_dict(state, strict=False)
    if result.missing_keys or result.unexpected_keys:
        raise RuntimeError(f"checkpoint mismatch: {len(result.missing_keys)} missing, "
                           f"{len(result.unexpected_keys)} unexpected keys")
    model.to(device).eval()
    return model, result


def scores(cm):
    tn, fp, fn, tp = cm.ravel().astype(np.float64)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)
    iou = tp / max(tp + fp + fn, 1)
    oa = (tp + tn) / max(cm.sum(), 1)
    return {"OA": oa, "Precision": precision, "Recall": recall, "F1": f1, "IoU": iou}


def confusion(pred, target):
    valid = target >= 0
    cm = np.zeros((2, 2), dtype=np.int64)
    for t in (0, 1):
        for p in (0, 1):
            cm[t, p] = np.count_nonzero((target == t) & (pred == p) & valid)
    return cm


@torch.no_grad()
def predict_scene(model, t1, t2, device):
    """Sliding-window change probability for one full scene. t1/t2: [12, H, W]."""
    _, h, w = t1.shape
    ph = max(TILE, int(np.ceil((h - TILE) / STRIDE)) * STRIDE + TILE)
    pw = max(TILE, int(np.ceil((w - TILE) / STRIDE)) * STRIDE + TILE)
    pad = (0, pw - w, 0, ph - h)
    mode = "reflect" if min(h, w) > max(pad) else "constant"
    t1p = torch.nn.functional.pad(t1[None], pad, mode=mode)
    t2p = torch.nn.functional.pad(t2[None], pad, mode=mode)
    prob = torch.zeros(ph, pw)
    count = torch.zeros(ph, pw)
    for y in range(0, ph - TILE + 1, STRIDE):
        for x in range(0, pw - TILE + 1, STRIDE):
            a = t1p[..., y:y + TILE, x:x + TILE].contiguous().to(device)
            b = t2p[..., y:y + TILE, x:x + TILE].contiguous().to(device)
            prob[y:y + TILE, x:x + TILE] += torch.softmax(model(a, b), dim=1)[0, 1].cpu()
            count[y:y + TILE, x:x + TILE] += 1
    return (prob / count)[:h, :w].numpy()


def full_scene(model, root, device):
    total = {t: np.zeros((2, 2), dtype=np.int64) for t in THRESHOLDS}
    per_city = []
    for name, t1, t2, mask in load_scenes(Path(root), "test"):
        target = mask.numpy()
        prob = predict_scene(model, t1, t2, device)
        city = {"city": name, "pixels": int(target.size), "change_pixels": int((target == 1).sum())}
        for t in THRESHOLDS:
            cm = confusion((prob > t).astype(np.int64), target)
            total[t] += cm
            city[f"F1@{t}"] = scores(cm)["F1"]
        per_city.append(city)
        print(f"  {name}: {target.shape} change={city['change_pixels']} F1@0.5={city['F1@0.5']:.4f}", flush=True)
    return {str(t): scores(cm) for t, cm in total.items()}, per_city


@torch.no_grad()
def random_crops(model, root, device, seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    ds = OSCD12ChannelDataset(root, split="test", multiplier=10, augment=False)
    cm = np.zeros((2, 2), dtype=np.int64)
    for i in range(len(ds)):
        s = ds[i]
        logits = model(s["t1"][None].to(device), s["t2"][None].to(device))
        cm += confusion(logits.argmax(1)[0].cpu().numpy(), s["mask"].numpy())
    return scores(cm)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--deeplab-weights", default="data/weights/deeplabv3plus_best.pt")
    ap.add_argument("--oscd-root", default=str(PROJECT_ROOT / "data" / "benchmark" / "oscd"))
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--crop-seeds", type=int, nargs="*", default=[])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    torch.manual_seed(0)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, _ = load_model(args.weights, args.deeplab_weights, args.ablation, device)
    print("Checkpoint loaded: 0 missing, 0 unexpected keys")

    result = {"weights": Path(args.weights).name, "ablation": args.ablation}
    result["full_scene"], result["per_city"] = full_scene(model, args.oscd_root, device)
    for t, m in result["full_scene"].items():
        print(f"FULL-SCENE tau={t}: " + "  ".join(f"{k}={v * 100:.2f}" for k, v in m.items()), flush=True)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2, default=float))
    result["random_crops"] = {}
    for seed in args.crop_seeds:
        m = random_crops(model, Path(args.oscd_root), device, seed)
        result["random_crops"][seed] = m
        print(f"RANDOM-CROPS seed={seed}: " + "  ".join(f"{k}={v * 100:.2f}" for k, v in m.items()), flush=True)
        if args.out:
            Path(args.out).write_text(json.dumps(result, indent=2, default=float))


if __name__ == "__main__":
    main()
