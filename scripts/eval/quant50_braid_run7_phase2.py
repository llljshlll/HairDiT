"""run7_phase2_rawstart braid 50장 정량 지표.

quant50_run7_phase2.py(unbraid판)의 braid 대응본. phase2는 replay(unbraid+braid) 학습이고
목적이 **braid 습득**이므로, unbraid 유지력만 재는 기존 지표만으로는 채택 근거가 절반뿐이다.

기존 스크립트가 braid를 생략했던 사유("braid_test 로컬에 없어" — quant50_run7.py 주석)는
해소됐다. dataset/braid/{img,matte,sketch}/test 에 107장이 있어 50장을 고정 시드로 뽑아 쓴다.

지표 (트레이너 _perceptual_validate의 braid 항목과 동일 정의):
  lpips_braid     — GT 대비 질감 충실도 (↓ 좋음)
  edge_iou_braid  — 입력 스케치 대비 구조 충실도 (↑ 좋음). braid 형태를 따라갔는지가 phase2 핵심
방향 지표(교수님 지시 ④ 필수)도 함께 측정:
  GT 오차 / coherence / seed 불일치  — orientation_metric.py 재사용 (sigma_i=3, erode_px=6)

python scripts/eval/quant50_braid_run7_phase2.py --epochs 5 10 15 20 25 30 35 40
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
from eval_metrics import canny_edges, edge_iou, hair_masked_lpips, _safe_mean  # noqa: E402

ROOT = Path(__file__).parent.parent.parent
POOL = ROOT / "outputs/0813/quant50/_pool50_braid"
GT_DIR = ROOT / "dataset/braid/img/test"
MATTE_DIR = ROOT / "dataset/braid/matte/test"
SKETCH_DIR = ROOT / "dataset/braid/sketch/test"
DEFAULT_GEN_ROOT = ROOT / "outputs/0813/quant50_braid/run7_phase2_rawstart"

SEEDS = [1, 2, 3, 42]
IMAGES = sorted((POOL / "selected_50.txt").read_text().split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", nargs="+", required=True)
    ap.add_argument("--gen-root", default=str(DEFAULT_GEN_ROOT))
    args = ap.parse_args()
    gen_root = Path(args.gen_root)

    print(f"n_images={len(IMAGES)} seeds={SEEDS} gen_root={gen_root}")
    rows = []
    for epoch in args.epochs:
        gt_errs, cohs, diss, lps, ious = [], [], [], [], []
        n_missing = 0
        for img_id in IMAGES:
            try:
                gt_bgr = cv2.imread(str(GT_DIR / f"{img_id}.png"))
                sk_bgr = cv2.imread(str(SKETCH_DIR / f"{img_id}.png"))
                m = cv2.imread(str(MATTE_DIR / f"{img_id}.png"), 0)
                if gt_bgr is None or sk_bgr is None or m is None:
                    raise FileNotFoundError(img_id)
                matte = m.astype(np.float64) / 255.0
                gens = {}
                for s in SEEDS:
                    p = gen_root / str(s) / f"epoch{epoch}" / f"{img_id}.png"
                    g = cv2.imread(str(p))
                    if g is None:
                        raise FileNotFoundError(p)
                    gens[s] = g
            except FileNotFoundError as e:
                n_missing += 1
                print(f"  [skip] {img_id}: {e}")
                continue

            errs = []
            for s in SEEDS:
                e_, c_ = orientation_error(gens[s], gt_bgr, matte, SIGMA_I, ERODE_PX)
                errs.append(e_)
                cohs.append(c_)
            gt_errs.append(float(np.mean(errs)))
            dis, _ = seed_disagreement(gens, matte, SIGMA_I, ERODE_PX)
            diss.append(dis)

            gt_rgb = cv2.cvtColor(gt_bgr, cv2.COLOR_BGR2RGB)
            sk_rgb = cv2.cvtColor(sk_bgr, cv2.COLOR_BGR2RGB)
            matte_u8 = (matte * 255).astype(np.uint8)
            for s in SEEDS:
                gen_rgb = cv2.cvtColor(gens[s], cv2.COLOR_BGR2RGB)
                lps.append(hair_masked_lpips(gen_rgb, gt_rgb, matte_u8))
                ious.append(edge_iou(canny_edges(gen_rgb), canny_edges(sk_rgb), matte_u8))

        if not gt_errs:
            print(f"epoch{epoch}: 생성 이미지 없음 — 건너뜀")
            continue
        lps = [v for v in lps if not np.isnan(v)]
        ious = [v for v in ious if not np.isnan(v)]
        row = dict(
            epoch=epoch, n=len(gt_errs), n_missing=n_missing,
            gt_err=float(np.mean(gt_errs)), coh=float(np.mean(cohs)),
            dis_mean=float(np.mean(diss)), dis_std=float(np.std(diss, ddof=1)),
            lpips=float(np.mean(lps)), iou=float(np.mean(ious)),
        )
        rows.append(row)
        print(f"epoch{epoch}: n={row['n']}(missing {row['n_missing']}) "
              f"GT_err={row['gt_err']:.2f} coh={row['coh']:.3f} "
              f"seed_dis={row['dis_mean']:.2f}+-{row['dis_std']:.2f} "
              f"lpips_braid={row['lpips']:.4f} edge_iou_braid={row['iou']:.4f}")

    print("\n=== markdown row ===")
    print("| epoch | GT 오차 평균 [deg] | coherence | seed 불일치 [deg] | lpips_braid ↓ | edge_iou_braid ↑ |")
    print("|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        print(f"| {r['epoch']} | {r['gt_err']:.2f} | {r['coh']:.3f} | "
              f"{r['dis_mean']:.2f}±{r['dis_std']:.2f} | {r['lpips']:.4f} | {r['iou']:.4f} |")


if __name__ == "__main__":
    main()
