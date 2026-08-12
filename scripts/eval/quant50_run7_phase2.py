"""run7_phase2_rawstart 50장 정량 지표 — quant50_run7.py의 phase2판.

quant50_run7.py와 지표·파라미터 전부 동일(structure tensor sigma_i=3/erode_px=6,
compute_delta_e_hue, hair_masked_lpips). GEN_ROOT와 라벨만 다르다 — run7_phase1 수치
(reports/[DIGLAB][0812][장서현]run7_phase1_result.md)와 직접 비교하기 위함이다.

GT는 dataset/unbraid/{img,matte}/test (unbraid split). braid_test가 로컬에 없어
lpips_braid/edge_iou_braid는 [DIGLAB][0810]run5_1_quant_eval.md §3.0과 동일하게 생략.
phase2는 replay(unbraid+braid) 학습이므로 이 지표는 "unbraid 유지력(forgetting)" 관점으로 읽는다.

python scripts/eval/quant50_run7_phase2.py --epochs 5 10 15 20 25 30 35 40
python scripts/eval/quant50_run7_phase2.py --epochs 40 --gen-root outputs/0813/quant50/기타런
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
from orientation_metric import SIGMA_I, ERODE_PX, orientation_error, seed_disagreement  # noqa: E402
from eval_metrics import compute_delta_e_hue, hair_masked_lpips  # noqa: E402

ROOT = Path(__file__).parent.parent.parent
POOL = ROOT / "outputs/0812/quant50/_pool50"          # phase1과 동일 pool 재사용 (비교 가능성)
GT_DIR = ROOT / "dataset/unbraid/img/test"
MATTE_DIR = ROOT / "dataset/unbraid/matte/test"
DEFAULT_GEN_ROOT = ROOT / "outputs/0813/quant50/run7_phase2_rawstart"

SEEDS = [1, 2, 3, 42]
IMAGES = sorted((POOL / "selected_50.txt").read_text().split())


def load_gt_bgr(img_id):
    return cv2.imread(str(GT_DIR / f"{img_id}.png"))


def load_matte(img_id):
    m = cv2.imread(str(MATTE_DIR / f"{img_id}.png"), 0)
    return m.astype(np.float64) / 255.0


def load_gen(gen_root, epoch, seed, img_id):
    p = gen_root / str(seed) / f"epoch{epoch}" / f"{img_id}.png"
    g = cv2.imread(str(p))
    if g is None:
        raise FileNotFoundError(p)
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", nargs="+", required=True,
                    help="정수 epoch 또는 'final'")
    ap.add_argument("--gen-root", default=str(DEFAULT_GEN_ROOT))
    ap.add_argument("--label", default="run7_phase2_rawstart")
    args = ap.parse_args()
    gen_root = Path(args.gen_root)

    print(f"n_images={len(IMAGES)} seeds={SEEDS} gen_root={gen_root}")
    rows = []
    for epoch in args.epochs:
        gt_errs, cohs, diss = [], [], []
        dEs, lps = [], []
        n_missing = 0
        for img_id in IMAGES:
            try:
                gt_bgr = load_gt_bgr(img_id)
                matte = load_matte(img_id)
                gens = {s: load_gen(gen_root, epoch, s, img_id) for s in SEEDS}
            except FileNotFoundError as e:
                n_missing += 1
                print(f"  [skip] {img_id}: {e}")
                continue
            errs = []
            for s in SEEDS:
                e, c = orientation_error(gens[s], gt_bgr, matte, SIGMA_I, ERODE_PX)
                errs.append(e)
                cohs.append(c)
            gt_errs.append(float(np.mean(errs)))
            dis, _ = seed_disagreement(gens, matte, SIGMA_I, ERODE_PX)
            diss.append(dis)

            gt_rgb = cv2.cvtColor(gt_bgr, cv2.COLOR_BGR2RGB)
            matte_u8 = (matte * 255).astype(np.uint8)
            for s in SEEDS:
                gen_rgb = cv2.cvtColor(gens[s], cv2.COLOR_BGR2RGB)
                dEs.append(compute_delta_e_hue(gen_rgb, gt_rgb, matte_u8))
                lps.append(hair_masked_lpips(gen_rgb, gt_rgb, matte_u8))

        if not gt_errs:
            print(f"epoch{epoch}: 생성 이미지 없음 — 건너뜀")
            continue
        dEs = [v for v in dEs if not np.isnan(v)]
        lps = [v for v in lps if not np.isnan(v)]
        row = dict(
            epoch=epoch, n=len(gt_errs), n_missing=n_missing,
            gt_err=float(np.mean(gt_errs)), coh=float(np.mean(cohs)),
            dis_mean=float(np.mean(diss)), dis_std=float(np.std(diss, ddof=1)),
            dE=float(np.mean(dEs)), lpips=float(np.mean(lps)),
        )
        rows.append(row)
        print(f"epoch{epoch}: n={row['n']}(missing {row['n_missing']}) "
              f"GT_err={row['gt_err']:.2f} coh={row['coh']:.3f} "
              f"seed_dis={row['dis_mean']:.2f}+-{row['dis_std']:.2f} "
              f"dE_unbraid={row['dE']:.4f} lpips_unbraid={row['lpips']:.4f}")

    print("\n=== markdown row ===")
    print("| epoch | GT 오차 평균 [deg] | coherence | seed 불일치 [deg] | dE_unbraid | lpips_unbraid |")
    print("|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        print(f"| {row['epoch']} | {row['gt_err']:.2f} | {row['coh']:.3f} | "
              f"{row['dis_mean']:.2f}±{row['dis_std']:.2f} | {row['dE']:.4f} | {row['lpips']:.4f} |")


if __name__ == "__main__":
    main()
