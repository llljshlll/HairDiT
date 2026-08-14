"""
Split-aware evaluation script.

Usage:
  python3 scripts/eval_metrics.py \\
      --split   braid                          \\
      --pred    custom_results/dit/exp1        \\
      [--pred-suffix _full]                    \\
      [--out    eval_results/exp1_braid]       \\
      [--tag    "Exp1"]

Dataset paths are derived automatically from the split:
  dataset/{split}/img/test    — GT images
  dataset/{split}/matte/test  — GT mattes (grayscale)
  dataset/{split}/sketch/test — sketch images

Metrics (최종 7개 — 스펙 확정):
  per-image (braid/unbraid/macro 분리 보고, braid는 ±CI95):
    ① Sketch LPIPS ↓  (구조,     paired vs sketch, hair 영역)
    ② Edge IoU ↑      (구조 보조, paired vs sketch, hair 영역)
    ④ LPIPS (GT) ↓    (외형,     paired vs GT,     hair-masked)
    ⑥ Boundary LPIPS ↓(경계 보조, paired vs GT,     경계 band)
  FID (통합 573만 보고, dims=2048):
    ③ Hair FID ↓          (리얼리즘,   hair 마스킹/크롭)
    ⑤ Boundary FID ↓      (경계,       경계 band)
    ⑦ Full-portrait FID ↓ (전역 조화,  whole-image)

R2 지표 세트 (reports/last_test.md "## R2 정량 지표 세트 — 측정 영역 축 포함"):
  측정 영역 축을 명시적으로 분리한다.
    matte **내부** : KID_hair(주력) / ΔE2000 / LPIPS(GT) / Edge IoU
    경계 **밴드 B**: Boundary LPIPS — band = dilate(matte>0,k) − erode(matte>0,k), k=8·16
    matte **외부** : PSNR_bg · LPIPS_bg  (배경 보존 = leakage 서사)
    얼굴 영역     : ArcFace cos (identity 보존, cross-id 대조로 해석)

  - KID_hair: 573장은 2048-dim FID가 rank-deficient가 되는 소표본이라 KID를 주력으로 둔다
    (FID는 참고). subset_size는 표본 수에 맞춰 자동 축소되며 로그·CSV에 남는다.
  - Boundary LPIPS: 밴드는 **이진** 가중이다. alpha로 가중하면 밴드 바깥쪽 절반(matte=0)이
    지워져 이음새를 못 본다. legacy bnd_lpips(alpha 값 밴드 25~230)는 과거 리포트 비교용으로
    남겨뒀으니 혼동하지 말 것 — 신규 측정은 bnd_lpips_k8/k16.
  - ArcFace: --face-dir 미지정이면 GT와 비교(same-identity ceiling). cross-id 평가에서는
    --face-dir experiment_cross_id/face_links/{type} 로 B의 얼굴과 비교한다.
    insightface 미설치 시 경고 후 NaN (pip install insightface onnxruntime).
  - region IoU: 이번 스펙에서 **보류**(2026-08-14 결정). 생성 이미지용 hair segmenter가
    레포에 없고, GT matte와 다른 세그멘터를 쓰면 상수 편향이 생겨 해석이 어려워진다.

  보고 단위 규칙:
    - FID/KID는 2048-dim 특징 → n=107 braid 단독은 불안정. 통합(573)만 보고.
    - per-image는 unbraid/braid/macro 분리. braid는 ±CI95.

Outputs:
  <out>_per_image.csv  (stem, split, ①②④⑥)
  <out>_summary.csv    (metric, axis, paired, unit, braid, braid_ci95, unbraid, macro, combined573)
  console table
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import tempfile
import warnings
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from tqdm import tqdm

warnings.filterwarnings("ignore")

ROOT   = Path(__file__).parent.parent
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

ALL_METRICS = frozenset({
    "sketch_lpips", "sketch_delta_e", "edge_iou",  # vs sketch (구조/색상)
    "lpips_gt", "bnd_lpips",                        # vs GT (외형/경계)
    "delta_e_gt", "psnr",                           # vs GT (색상/화질)
    "hair_fid", "bnd_fid", "full_fid",             # FID (리얼리즘)
    # --- R2 지표 세트 (reports/last_test.md "## R2 정량 지표 세트 — 측정 영역 축 포함") ---
    "bnd_lpips_k8", "bnd_lpips_k16",               # 경계 밴드 B (morphological, k=8/16)
    "psnr_bg", "lpips_bg",                          # matte '외부' — 배경 보존(leakage)
    "kid_hair",                                     # 리얼리즘 주력 (소표본에서 FID보다 안정)
    "arcface",                                      # 얼굴 영역 identity 보존
})

# R2 밴드 정의: band = dilate(matte>0, k) − erode(matte>0, k). 권고 k = 8 또는 16.
# "유리한 것 선택"(last_test.md) → 둘 다 계산해두고 리포트에서 하나를 고른다.
BND_KS = (8, 16)

def build_splits(data_root: Path) -> dict:
    """{split: {img,matte,sketch}} 경로. data_root 아래 {split}/{kind}/test 레이아웃 전제."""
    return {
        s: {k: data_root / s / k / "test" for k in ("img", "matte", "sketch")}
        for s in ("braid", "unbraid")
    } | {"combined": None}   # combined는 --pred braid_dir unbraid_dir 순서로 2개 지정


# 모듈 전역 — --data-root로 main()에서 교체된다(테스트/외부 호출은 직접 대입해도 된다).
SPLITS = build_splits(ROOT / "dataset")


# ---------------------------------------------------------------------------
# LPIPS
# NOTE: compute_lpips는 항상 RGB 3채널 컬러 입력을 받는다.
#   - lpips_gt, bnd_lpips: pred/GT 모두 full-color RGB crop → 컬러 비교 ✓
#   - sketch_lpips: pred 측은 Canny edge map (grayscale→3ch 복제)으로 변환 후 비교.
#     구조(선 패턴) 유사도가 목적이므로 컬러 비교가 아니다.
#     컬러 충실도 비교는 sketch_delta_e(ΔE) 지표가 담당한다.
# ---------------------------------------------------------------------------
_lpips_fn = None


def get_lpips():
    global _lpips_fn
    if _lpips_fn is None:
        import lpips
        _lpips_fn = lpips.LPIPS(net="alex", verbose=False).to(DEVICE)
    return _lpips_fn


def _to_lpips_tensor(arr: np.ndarray) -> torch.Tensor:
    t = torch.from_numpy(arr).float().permute(2, 0, 1) / 127.5 - 1.0
    return t.unsqueeze(0).to(DEVICE)


def compute_lpips(a: np.ndarray, b: np.ndarray) -> float:
    fn = get_lpips()
    with torch.no_grad():
        ta, tb = _to_lpips_tensor(a), _to_lpips_tensor(b)
        if ta.shape[-1] < 64 or ta.shape[-2] < 64:
            ta = F.interpolate(ta, (64, 64), mode="bilinear", align_corners=False)
            tb = F.interpolate(tb, (64, 64), mode="bilinear", align_corners=False)
        return float(fn(ta, tb).item())


# ---------------------------------------------------------------------------
# Pixel metrics
# ---------------------------------------------------------------------------

def compute_psnr(a: np.ndarray, b: np.ndarray,
                 alpha: np.ndarray | None = None) -> float:
    """MSE → PSNR. alpha (H,W) float [0,1]: alpha-weighted MSE."""
    a64, b64 = a.astype(np.float64), b.astype(np.float64)
    if alpha is None:
        err = float(np.mean((a64 - b64) ** 2))
    else:
        aw = alpha[..., None].astype(np.float64)   # (H,W,1) broadcast over C
        w  = float(aw.sum()) * (a64.shape[-1] if a64.ndim == 3 else 1)
        if w < 1e-6:
            return float("nan")
        err = float(((a64 - b64) ** 2 * aw).sum() / w)
    return 10 * math.log10(255.0 ** 2 / err) if err > 0 else float("inf")


def _rgb_to_lab(img: np.ndarray) -> np.ndarray:
    """RGB uint8 → CIE Lab float64 (L∈[0,100], a,b∈[-128,127])."""
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.float64)
    lab[:, :, 0] = lab[:, :, 0] * 100.0 / 255.0
    lab[:, :, 1] -= 128.0
    lab[:, :, 2] -= 128.0
    return lab


def compute_delta_e_hue(a: np.ndarray, b: np.ndarray, mask: np.ndarray,
                         alpha: np.ndarray | None = None) -> float:
    """CIEDE2000 between shade-normalized mean Lab colors within mask.

    Shade normalization: L is fixed to 50 before averaging so the result
    reflects hue/chroma difference only, not lighting variation.
    alpha (H,W) float [0,1]: soft-alpha weights for the mean.
    """
    from skimage.color import deltaE_ciede2000
    pixels = mask > 0
    if pixels.sum() < 10:
        return float("nan")
    lab_a = _rgb_to_lab(a)[pixels].copy()   # (N, 3)
    lab_b = _rgb_to_lab(b)[pixels].copy()
    lab_a[:, 0] = 50.0                       # shade normalization
    lab_b[:, 0] = 50.0
    if alpha is not None:
        w = alpha[pixels].astype(np.float64)
        w_sum = w.sum()
        if w_sum > 1e-8:
            mean_a = (lab_a * w[:, None]).sum(0) / w_sum
            mean_b = (lab_b * w[:, None]).sum(0) / w_sum
        else:
            mean_a, mean_b = lab_a.mean(0), lab_b.mean(0)
    else:
        mean_a, mean_b = lab_a.mean(axis=0), lab_b.mean(axis=0)
    return float(deltaE_ciede2000(mean_a, mean_b))


# ---------------------------------------------------------------------------
# Masking helpers
# ---------------------------------------------------------------------------

def _bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    return int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1


def _alpha_blend_crop(img: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """img * alpha[...,None], returns uint8. alpha ∈ [0,1] float."""
    return (img.astype(np.float64) * alpha[..., None]).clip(0, 255).astype(np.uint8)


def extract_region_crop(img: np.ndarray, matte: np.ndarray, min_px: int = 64):
    hair = matte > 0
    if hair.sum() < min_px:
        return None
    y0, y1, x0, x1 = _bbox(hair)
    crop    = img  [y0:y1, x0:x1].copy()
    alpha_c = matte[y0:y1, x0:x1].astype(np.float64) / 255.0
    crop    = _alpha_blend_crop(crop, alpha_c)
    if crop.shape[0] < 16 or crop.shape[1] < 16:
        return None
    return cv2.resize(crop, (128, 128))


def get_boundary_mask(matte: np.ndarray) -> np.ndarray:
    """[legacy] alpha 값 밴드 — matte가 반투명한 구간(25~230)만 경계로 본다.

    ⚠️ R2 스펙의 밴드가 아니다. 과거 리포트(run5~run7)의 bnd_lpips/bnd_fid가 이 정의로
    측정됐으므로 비교 가능성 때문에 남겨둔다. 신규 측정은 get_boundary_band()를 쓸 것.
    이 정의는 matte가 하드(0/255)하면 밴드가 거의 비어버린다 — R2가 형태학적 밴드를
    요구한 이유.
    """
    return (matte >= 25) & (matte <= 230)


def get_boundary_band(matte: np.ndarray, k: int) -> np.ndarray:
    """R2 경계 밴드: band = dilate(matte>0, k) − erode(matte>0, k) (경계 안팎 링).

    k = 구조요소 반경(px) → 링 폭 = 2k+1 px (안쪽 k + 경계 1 + 바깥쪽 k). 실측 확인:
    k=8 → 17px, k=16 → 33px.
    matte 값이 아니라 matte>0 이진 전경의 형태에서만 만들어지므로, alpha가 하드컷이어도
    항상 폭이 보장된다(legacy get_boundary_mask와의 결정적 차이).
    """
    fg = (matte > 0).astype(np.uint8)
    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1))
    return (cv2.dilate(fg, se).astype(np.int16) - cv2.erode(fg, se).astype(np.int16)) > 0


# ---------------------------------------------------------------------------
# Metric functions
# ---------------------------------------------------------------------------

def canny_edges(img: np.ndarray) -> np.ndarray:
    return cv2.Canny(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), 50, 150) > 0


def edge_iou(pred_e: np.ndarray, sk_e: np.ndarray, matte: np.ndarray) -> float:
    hair = matte > 0
    a, b = pred_e & hair, sk_e & hair
    union = (a | b).sum()
    return float((a & b).sum() / union) if union > 0 else 0.0


def sketch_lpips(pred: np.ndarray, sketch: np.ndarray, matte: np.ndarray) -> float:
    hair = matte > 0
    if hair.sum() == 0:
        return float("nan")
    y0, y1, x0, x1 = _bbox(hair)
    alpha_c  = matte[y0:y1, x0:x1].astype(np.float64) / 255.0
    edge_rgb = np.stack([canny_edges(pred).astype(np.uint8) * 255] * 3, axis=-1)
    p_crop   = _alpha_blend_crop(edge_rgb[y0:y1, x0:x1].copy(), alpha_c)
    s_crop   = _alpha_blend_crop(sketch  [y0:y1, x0:x1].copy(), alpha_c)
    if p_crop.shape[0] < 8 or p_crop.shape[1] < 8:
        return float("nan")
    return compute_lpips(p_crop, s_crop)


def hair_masked_lpips(pred: np.ndarray, gt: np.ndarray, matte: np.ndarray) -> float:
    hair = matte > 0
    if hair.sum() < 64:
        return float("nan")
    y0, y1, x0, x1 = _bbox(hair)
    alpha_c = matte[y0:y1, x0:x1].astype(np.float64) / 255.0
    p_crop  = _alpha_blend_crop(pred[y0:y1, x0:x1].copy(), alpha_c)
    g_crop  = _alpha_blend_crop(gt  [y0:y1, x0:x1].copy(), alpha_c)
    if p_crop.shape[0] < 8 or p_crop.shape[1] < 8:
        return float("nan")
    return compute_lpips(p_crop, g_crop)


def boundary_lpips(pred: np.ndarray, gt: np.ndarray, matte: np.ndarray) -> float:
    bnd = get_boundary_mask(matte)
    if bnd.sum() < 64:
        return float("nan")
    y0, y1, x0, x1 = _bbox(bnd)
    bnd_alpha = np.where(bnd, matte.astype(np.float64) / 255.0, 0.0)
    alpha_c   = bnd_alpha[y0:y1, x0:x1]
    p_crop = _alpha_blend_crop(pred[y0:y1, x0:x1].copy(), alpha_c)
    g_crop = _alpha_blend_crop(gt  [y0:y1, x0:x1].copy(), alpha_c)
    if p_crop.shape[0] < 8 or p_crop.shape[1] < 8:
        return float("nan")
    return compute_lpips(p_crop, g_crop)


def boundary_band_lpips(pred: np.ndarray, gt: np.ndarray, matte: np.ndarray, k: int) -> float:
    """R2 Boundary LPIPS — 형태학적 밴드 B 안에서만 pred vs GT 비교.

    legacy boundary_lpips()와 두 가지가 다르다:
      ① 밴드가 alpha 값이 아니라 형태학적 링(get_boundary_band)
      ② 가중치가 **이진**(밴드 안=1). alpha로 가중하면 matte=0인 바깥쪽 절반이 0으로
         지워져 "이음새 바깥"을 못 본다 — 경계 블러/헤일로를 재는 게 목적이므로 안 된다.
    """
    band = get_boundary_band(matte, k)
    if band.sum() < 64:
        return float("nan")
    y0, y1, x0, x1 = _bbox(band)
    alpha_c = band[y0:y1, x0:x1].astype(np.float64)      # 이진 가중
    p_crop = _alpha_blend_crop(pred[y0:y1, x0:x1].copy(), alpha_c)
    g_crop = _alpha_blend_crop(gt  [y0:y1, x0:x1].copy(), alpha_c)
    if p_crop.shape[0] < 8 or p_crop.shape[1] < 8:
        return float("nan")
    return compute_lpips(p_crop, g_crop)


# ---------------------------------------------------------------------------
# 배경(matte 외부) 보존 — leakage 서사 지원 (R2)
# ---------------------------------------------------------------------------

def bg_psnr(pred: np.ndarray, gt: np.ndarray, matte: np.ndarray) -> float:
    """matte 외부 가중 PSNR. 가중치 = 1 - alpha (헤어일수록 0)."""
    bg_alpha = 1.0 - matte.astype(np.float64) / 255.0
    if bg_alpha.sum() < 64:
        return float("nan")
    return compute_psnr(pred, gt, bg_alpha)


def bg_lpips(pred: np.ndarray, gt: np.ndarray, matte: np.ndarray) -> float:
    """matte 외부 LPIPS. 헤어 영역을 0으로 지운 전체 이미지끼리 비교한다.

    배경은 이미지 전역에 흩어져 있어 crop이 의미가 없으므로 bbox를 잡지 않는다
    (hair/boundary 지표와 다른 점).
    """
    bg_alpha = 1.0 - matte.astype(np.float64) / 255.0
    if bg_alpha.sum() < 64:
        return float("nan")
    p = _alpha_blend_crop(pred.copy(), bg_alpha)
    g = _alpha_blend_crop(gt.copy(),   bg_alpha)
    return compute_lpips(p, g)


# ---------------------------------------------------------------------------
# ArcFace identity (얼굴 영역) — R2, 리뷰어 요구
# ---------------------------------------------------------------------------

_arcface_app = None
_arcface_warned = False


def get_arcface():
    """insightface buffalo_l(ArcFace w600k_r50) lazy 로드. 없으면 None.

    pytorch_fid와 같은 graceful-degradation 규약: 미설치 시 경고 1회 후 NaN.
      pip install insightface onnxruntime      (GPU면 onnxruntime-gpu)
    최초 실행 시 모델(~300MB)이 ~/.insightface로 자동 다운로드된다.
    """
    global _arcface_app, _arcface_warned
    if _arcface_app is None and not _arcface_warned:
        try:
            from insightface.app import FaceAnalysis
            providers = (["CUDAExecutionProvider", "CPUExecutionProvider"]
                         if DEVICE.type == "cuda" else ["CPUExecutionProvider"])
            # detection(SCRFD) + recognition(ArcFace w600k_r50)만 로드.
            # buffalo_l에는 genderage·landmark 모델도 들어 있는데 identity 비교엔 불필요하다.
            app = FaceAnalysis(name="buffalo_l", providers=providers,
                               allowed_modules=["detection", "recognition"])
            app.prepare(ctx_id=0 if DEVICE.type == "cuda" else -1, det_size=(640, 640))
            _arcface_app = app
        except Exception as e:
            _arcface_warned = True
            print(f"[WARN] ArcFace 비활성 ({type(e).__name__}: {e}). "
                  f"→ pip install insightface onnxruntime")
    return _arcface_app


ARCFACE_PAD_RATIO = 0.25
_arcface_miss = 0


def _arcface_embed(img_rgb: np.ndarray):
    """가장 큰 얼굴의 L2-정규화 512-d 임베딩. 얼굴 미검출 시 None.

    검출 전에 가장자리를 ARCFACE_PAD_RATIO만큼 replicate 패딩한다. 이 데이터셋은 얼굴이
    512x512 프레임을 거의 꽉 채우는 클로즈업이라, 패딩 없이는 SCRFD가 절반 이상을 놓친다
    (실측: 패딩 0 → 11/30, 0.25 → 30/30, det_thresh=0.5 동일). det_thresh를 낮추는 대신
    패딩을 쓰는 이유는 정밀도를 깎지 않기 때문. pred/ref에 동일 적용되므로 비교는 공정하다.
    """
    global _arcface_miss
    app = get_arcface()
    if app is None:
        return None
    bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    p = int(bgr.shape[0] * ARCFACE_PAD_RATIO)
    if p > 0:
        bgr = cv2.copyMakeBorder(bgr, p, p, p, p, cv2.BORDER_REPLICATE)
    faces = app.get(bgr)
    if not faces:
        _arcface_miss += 1
        return None
    f = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
    return f.normed_embedding      # recognition 모델이 안 붙으면 None (호출부에서 NaN 처리)


def arcface_cos(pred: np.ndarray, ref: np.ndarray) -> float:
    """ArcFace cosine similarity(pred, ref) ∈ [-1,1]. 높을수록 동일 인물.

    ref는 "얼굴이 와야 할 사람"의 원본 이미지다:
      - 일반(same-identity) run  : ref = GT (=그 stem 본인) → identity 보존 ceiling
      - cross-id run             : ref = B의 이미지(face_links) → 헤어 생성이 B의 얼굴
                                    identity를 침범하지 않았는가
    --face-dir로 ref 디렉터리를 지정한다(미지정 시 GT).
    """
    ea, eb = _arcface_embed(pred), _arcface_embed(ref)
    if ea is None or eb is None:
        return float("nan")
    return float(np.dot(ea, eb))


# ---------------------------------------------------------------------------
# FID / KID
# ---------------------------------------------------------------------------

def compute_fid(real_imgs: list, fake_imgs: list, dims: int = 2048) -> float:
    """표준 InceptionV3 FID. dims=2048 (pool3 2048-dim 공분산).

    주의: 2048-dim 공분산은 표본 수 n < 2048 이면 rank-deficient → 통합(573)에서만
    안정적. braid 단독(n=107) 분리 보고 금지 (스펙 보고 단위 규칙).
    """
    try:
        from pytorch_fid import fid_score
    except ImportError:
        print("[WARN] pytorch_fid 없음 — FID는 NaN. pip install pytorch-fid")
        return float("nan")
    with tempfile.TemporaryDirectory() as tmp:
        real_dir, fake_dir = Path(tmp) / "real", Path(tmp) / "fake"
        real_dir.mkdir()
        fake_dir.mkdir()
        for i, img in enumerate(real_imgs):
            if img is not None:
                Image.fromarray(img).save(real_dir / f"{i:05d}.png")
        for i, img in enumerate(fake_imgs):
            if img is not None:
                Image.fromarray(img).save(fake_dir / f"{i:05d}.png")
        nr = len(list(real_dir.glob("*.png")))
        nf = len(list(fake_dir.glob("*.png")))
        if nr < 2 or nf < 2:
            return float("nan")
        return float(fid_score.calculate_fid_given_paths(
            [str(real_dir), str(fake_dir)],
            batch_size=32, device=str(DEVICE), dims=dims, num_workers=0,
        ))


_inception = None


def _inception_features(imgs: list, batch_size: int = 32, dims: int = 2048) -> np.ndarray | None:
    """InceptionV3 pool3 (2048-d) 특징. pytorch_fid의 추출기를 그대로 재사용한다
    (FID와 동일한 특징 공간 → KID와 FID가 같은 것을 재도록)."""
    global _inception
    try:
        from pytorch_fid.inception import InceptionV3
    except ImportError:
        return None
    if _inception is None:
        idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
        _inception = InceptionV3([idx]).to(DEVICE).eval()
    feats = []
    with torch.no_grad():
        for i in range(0, len(imgs), batch_size):
            chunk = np.stack(imgs[i:i + batch_size])                    # (B,H,W,3) uint8
            t = torch.from_numpy(chunk).permute(0, 3, 1, 2).float().to(DEVICE) / 255.0
            f = _inception(t)[0].squeeze(-1).squeeze(-1)                 # (B,2048)
            feats.append(f.cpu().numpy())
    return np.concatenate(feats, axis=0) if feats else None


def _mmd2_poly(x: np.ndarray, y: np.ndarray) -> float:
    """다항 커널 k(a,b)=(a·b/d + 1)^3 의 unbiased MMD² (Bińkowski et al. 2018 KID)."""
    d = x.shape[1]
    kxx = (x @ x.T / d + 1.0) ** 3
    kyy = (y @ y.T / d + 1.0) ** 3
    kxy = (x @ y.T / d + 1.0) ** 3
    m, n = len(x), len(y)
    # 대각(자기 자신) 제외 = unbiased
    sxx = (kxx.sum() - np.trace(kxx)) / (m * (m - 1))
    syy = (kyy.sum() - np.trace(kyy)) / (n * (n - 1))
    return float(sxx + syy - 2.0 * kxy.mean())


def compute_kid(real_imgs: list, fake_imgs: list,
                n_subsets: int = 100, subset_size: int | None = None,
                seed: int = 0) -> tuple[float, float]:
    """KID (Kernel Inception Distance) — (mean, std) 반환. 낮을수록 좋음.

    FID를 안 쓰고 KID를 주력으로 두는 이유(last_test.md R2 "금지선: 소표본 FID"):
    FID는 2048-dim 가우시안 적합이라 표본 수가 차원보다 한참 작으면(573 ≪ 2048) 공분산이
    rank-deficient가 되어 값이 표본 수에 강하게 편향된다. KID는 unbiased MMD² 추정량이라
    소표본에서도 기대값이 표본 수에 의존하지 않는다.

    subset_size 기본값은 min(100, n) — 표본이 573뿐이라 관례값 1000을 쓸 수 없다.
    실제 사용된 값은 호출부에서 로그로 남긴다(리포트 명기 의무).
    """
    real = [x for x in real_imgs if x is not None]
    fake = [x for x in fake_imgs if x is not None]
    if len(real) < 10 or len(fake) < 10:
        return float("nan"), float("nan")
    fr = _inception_features(real)
    ff = _inception_features(fake)
    if fr is None or ff is None:
        print("[WARN] pytorch_fid 없음 — KID는 NaN. pip install pytorch-fid")
        return float("nan"), float("nan")
    n = min(len(fr), len(ff))
    m = min(subset_size or 100, n)
    if m < 10:
        print(f"[WARN] KID: 표본이 너무 적다(n={n}, subset={m}<10) — NaN 반환.")
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    vals = [
        _mmd2_poly(fr[rng.choice(len(fr), m, replace=False)],
                   ff[rng.choice(len(ff), m, replace=False)])
        for _ in range(n_subsets)
    ]
    return float(np.mean(vals)), float(np.std(vals))


# ---------------------------------------------------------------------------
# Summary / output
# ---------------------------------------------------------------------------

# 최종 정량 지표 7개 (스펙 확정).
#   (label, per_image_key, fid_key, higher_better, axis, paired, unit)
#     unit = "split"    → per-image. braid/unbraid/macro 분리 보고 (braid는 ±CI)
#     unit = "combined" → FID. 통합(573)만 보고 (2048-dim 공분산, braid n=107 rank-deficient)
SPEC_METRICS = [
    ("Sketch LPIPS ↓",      "sketch_lpips",   None,       False, "구조",        "paired(vs sketch)", "split"),
    ("Sketch ΔE2000 ↓",      "sketch_delta_e", None,       False, "색상(vs sk)", "paired(vs sketch)", "split"),
    ("Edge IoU ↑",          "edge_iou",       None,       True,  "구조(보조)",  "paired(vs sketch)", "split"),
    ("Hair FID ↓",          None,             "hair_fid", False, "리얼리즘",    "unpaired",          "combined"),
    ("LPIPS (GT) ↓",        "lpips",          None,       False, "외형",        "paired(vs GT)",     "split"),
    ("ΔE2000 (GT, hair) ↓",  "delta_e_gt",     None,       False, "색상(vs GT)", "paired(vs GT)",     "split"),
    ("PSNR (hair) ↑",       "psnr",           None,       True,  "화질",        "paired(vs GT)",     "split"),
    ("Boundary FID ↓",      None,             "bnd_fid",  False, "경계",        "unpaired",          "combined"),
    ("Boundary LPIPS ↓",    "bnd_lpips",      None,       False, "경계(보조)",  "paired(vs GT)",     "split"),
    ("Full-portrait FID ↓", None,             "full_fid", False, "전역 조화",   "unpaired",          "combined"),
    # --- R2 지표 세트 (reports/last_test.md). 측정 영역 축을 라벨에 명시한다. ---
    ("KID_hair ↓",          None,             "kid_hair", False, "리얼리즘",    "unpaired",          "combined"),
    ("Bnd LPIPS k=8 ↓",     "bnd_lpips_k8",   None,       False, "경계밴드B",   "paired(vs GT)",     "split"),
    ("Bnd LPIPS k=16 ↓",    "bnd_lpips_k16",  None,       False, "경계밴드B",   "paired(vs GT)",     "split"),
    ("PSNR_bg ↑",           "psnr_bg",        None,       True,  "배경보존",    "paired(vs GT)",     "split"),
    ("LPIPS_bg ↓",          "lpips_bg",       None,       False, "배경보존",    "paired(vs GT)",     "split"),
    ("ArcFace cos ↑",       "arcface",        None,       True,  "identity",    "paired(vs face)",   "split"),
]

PER_IMAGE_KEYS = [
    "sketch_lpips", "sketch_delta_e", "edge_iou", "lpips", "bnd_lpips", "delta_e_gt", "psnr",
    # R2
    "bnd_lpips_k8", "bnd_lpips_k16", "psnr_bg", "lpips_bg", "arcface",
]


def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "N/A"
    return f"{v:.4f}"


def _safe_mean(vals):
    vs = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
    return sum(vs) / len(vs) if vs else None


def _n_ok(vals):
    """NaN/None을 제외한 유효 표본 수. 지표마다 다를 수 있어 별도로 보고한다
    (예: ArcFace는 braid=뒤통수 샷이라 얼굴이 없어 대부분 NaN)."""
    return sum(1 for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v)))


def _ci95(vals):
    """95% 신뢰구간 half-width (1.96·SD/√n). 표본<2면 None."""
    vs = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
    n = len(vs)
    if n < 2:
        return None
    m = sum(vs) / n
    var = sum((v - m) ** 2 for v in vs) / (n - 1)
    return 1.96 * math.sqrt(var) / math.sqrt(n)


def build_summary(rows_braid, rows_unbraid, fid: dict) -> list[dict]:
    """SPEC_METRICS 각 지표를 보고단위별로 정리.
    combined 모드: rows_braid, rows_unbraid 둘 다 지정. single split: 한쪽만(나머지 None)."""
    out = []
    for label, pk, fk, higher, axis, paired, unit in SPEC_METRICS:
        r = {"label": label, "axis": axis, "paired": paired, "unit": unit,
             "braid": None, "braid_ci95": None, "unbraid": None, "unbraid_ci95": None,
             "macro": None, "macro_ci95": None, "combined": None, "combined_std": None,
             "braid_n": None, "unbraid_n": None}
        if unit == "combined":
            r["combined"] = fid.get(fk)
            r["combined_std"] = fid.get(f"{fk}_std")   # KID만 존재 (subset 간 표준편차)
        else:
            if rows_braid is not None:
                vals = [x.get(pk) for x in rows_braid]
                r["braid"]      = _safe_mean(vals)
                r["braid_ci95"] = _ci95(vals)
                r["braid_n"]    = _n_ok(vals)
            if rows_unbraid is not None:
                vals = [x.get(pk) for x in rows_unbraid]
                r["unbraid"]      = _safe_mean(vals)
                r["unbraid_ci95"] = _ci95(vals)
                r["unbraid_n"]    = _n_ok(vals)
            if r["braid"] is not None and r["unbraid"] is not None:
                r["macro"] = (r["braid"] + r["unbraid"]) / 2
                # 독립 두 그룹 평균의 평균 → CI = ½·√(CI_b² + CI_u²)
                cb, cu = r["braid_ci95"], r["unbraid_ci95"]
                if cb is not None and cu is not None:
                    r["macro_ci95"] = 0.5 * math.sqrt(cb ** 2 + cu ** 2)
        out.append(r)
    return out


def _fmt_ci(v, ci) -> str:
    s = _fmt(v)
    if s == "N/A" or ci is None or (isinstance(ci, float) and math.isnan(ci)):
        return s                      # "N/A±nan" 같은 출력 방지
    return f"{s}±{ci:.4f}"


def print_summary(summary: list[dict], tag: str, n_b: int, n_u: int):
    print(f"\n{'='*80}")
    print(f"  tag={tag}   braid n={n_b}   unbraid n={n_u}   combined N={n_b + n_u}")
    print("=" * 80)
    print(f"  {'Metric':<20}{'축':<12}{'braid(±CI95)':>22}{'unbraid(±CI95)':>22}{'macro(±CI95)':>22}{'comb573':>18}")
    print("-" * 118)
    for r in summary:
        if r["unit"] == "combined":
            braid = unbraid = macro = "—"
            comb = _fmt_ci(r["combined"], r["combined_std"])
        else:
            braid   = _fmt_ci(r["braid"],   r["braid_ci95"])
            unbraid = _fmt_ci(r["unbraid"], r["unbraid_ci95"])
            macro   = _fmt_ci(r["macro"],   r["macro_ci95"])
            comb    = "—"
        print(f"  {r['label']:<20}{r['axis']:<12}{braid:>22}{unbraid:>22}{macro:>22}{comb:>18}")
    print("=" * 118)
    print("  · FID/KID=통합573만  · per-image=braid/unbraid/macro (모두 ±CI95)")
    print("  · KID는 ±subset 표준편차. 리포트에 subset_size 명기 의무(위 로그 참고)")
    print("  · 측정 영역: matte 내부 / 경계밴드 B(k) / matte 외부(bg) / 얼굴(ArcFace) — R2 스펙")
    if _arcface_miss:
        af = next((r for r in summary if r["label"].startswith("ArcFace")), None)
        detail = ""
        if af is not None:
            detail = (f"  유효 표본 braid={af['braid_n']}/{n_b}, unbraid={af['unbraid_n']}/{n_u}")
        print(f"  · ⚠️ ArcFace 얼굴 미검출 {_arcface_miss}건 → NaN(평균에서 제외).{detail}")
        print("    braid 원본은 대부분 뒤통수 샷이라 잴 얼굴이 없다 — 결손이 아니라 정의상 N/A다.")
        print("    ArcFace는 unbraid 기준으로만 해석할 것(macro/combined에 섞어 읽지 말 것).")
    # 지표마다 유효 n이 다를 수 있다 → CSV의 braid_n/unbraid_n 열을 함께 볼 것.
    print("  · run 간 유의차 확정은 scripts/stats_compare.py (paired t-test + Wilcoxon)")


def write_summary_csv(summary: list[dict], tag: str, path: Path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "axis", "paired", "unit",
                    "braid", "braid_ci95", "unbraid", "unbraid_ci95",
                    "macro", "macro_ci95", "combined573", "combined_std",
                    "braid_n", "unbraid_n"])
        for r in summary:
            w.writerow([
                r["label"], r["axis"], r["paired"], r["unit"],
                _fmt(r["braid"]),   _fmt(r["braid_ci95"]),
                _fmt(r["unbraid"]), _fmt(r["unbraid_ci95"]),
                _fmt(r["macro"]),   _fmt(r["macro_ci95"]),
                _fmt(r["combined"]), _fmt(r.get("combined_std")),
                r.get("braid_n"), r.get("unbraid_n"),
            ])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def discover_stems(pred_dir: Path, gt_dir: Path, suffix: str) -> list[str]:
    pred_stems = {
        (p.stem[:-len(suffix)] if suffix and p.stem.endswith(suffix) else p.stem)
        for p in pred_dir.glob("*.png")
    }
    gt_stems = {p.stem for p in gt_dir.glob("*.png")}
    common = pred_stems & gt_stems
    if not common:
        print("[ERROR] pred와 GT 사이에 공통 stem이 없습니다.")
        sys.exit(1)
    skipped = gt_stems - common
    if skipped:
        print(f"[INFO] GT에만 있어 제외된 stem: {len(skipped)}개")
    return sorted(common)


def _load_face_ref(face_dir: Path | None, gt_dir: Path, stem: str, h: int, w: int) -> np.ndarray:
    """ArcFace 기준 얼굴 이미지. face_dir 미지정/파일 없음이면 GT로 폴백.

    face_links/ 는 심볼릭 링크라 Image.open이 그대로 따라간다(gen_cross_id_map.py 참고).
    """
    p = (face_dir / f"{stem}.png") if face_dir is not None else None
    src = p if (p is not None and p.exists()) else gt_dir / f"{stem}.png"
    ref = np.array(Image.open(src).convert("RGB"))
    if ref.shape[:2] != (h, w):
        ref = cv2.resize(ref, (w, h), interpolation=cv2.INTER_LINEAR)
    return ref


def _process_split(split_name: str, pred_dir: Path, suffix: str,
                   sketch_dir: Path | None = None,
                   metrics: frozenset = ALL_METRICS,
                   face_dir: Path | None = None) -> dict:
    """단일 split 평가. per-image rows(split 라벨 포함) + FID/KID용 이미지 리스트 dict 반환.

    face_dir — ArcFace 기준 얼굴 이미지 디렉터리. 미지정 시 GT(=same-identity ceiling).
               cross-id에서는 experiment_cross_id/face_links/{type} 을 넘긴다(B의 얼굴).
    """
    ds     = SPLITS[split_name]
    gt_dir = ds["img"]
    mt_dir = ds["matte"]
    sk_dir = sketch_dir if sketch_dir is not None else ds["sketch"]

    need_sketch = "sketch_lpips" in metrics or "edge_iou" in metrics or "sketch_delta_e" in metrics
    need_gt     = "lpips_gt" in metrics or "bnd_lpips" in metrics or "delta_e_gt" in metrics or "psnr" in metrics

    stems = discover_stems(pred_dir, gt_dir, suffix)
    print(f"  [{split_name}] {len(stems)}개  metrics={sorted(metrics)}")

    rows = []
    hair_r, hair_f = [], []
    bnd_r,  bnd_f  = [], []
    full_r, full_f = [], []

    for stem in tqdm(stems, desc=f"[{split_name}]"):
        pred_name = f"{stem}{suffix}.png" if suffix else f"{stem}.png"
        pred_path = pred_dir / pred_name

        gt    = np.array(Image.open(gt_dir / f"{stem}.png").convert("RGB"))
        matte = np.array(Image.open(mt_dir / f"{stem}.png").convert("L"))
        sk    = np.array(Image.open(sk_dir / f"{stem}.png").convert("RGB")) if need_sketch else None

        h, w = gt.shape[:2]
        if matte.shape[:2] != (h, w):
            matte = cv2.resize(matte, (w, h), interpolation=cv2.INTER_LINEAR)
        if sk is not None and sk.shape[:2] != (h, w):
            sk = cv2.resize(sk, (w, h), interpolation=cv2.INTER_LINEAR)

        if not pred_path.exists():
            rows.append({"stem": stem, "split": split_name, **{k: None for k in PER_IMAGE_KEYS}})
            continue

        pred = np.array(Image.open(pred_path).convert("RGB"))
        if pred.shape[:2] != (h, w):
            pred = cv2.resize(pred, (w, h), interpolation=cv2.INTER_LINEAR)

        alpha     = matte.astype(np.float64) / 255.0
        hair      = matte > 0
        bnd       = get_boundary_mask(matte)
        bnd_matte = (matte * bnd.astype(np.uint8))   # boundary zone only, with matte values

        pred_e = canny_edges(pred) if need_sketch else None
        sk_e   = canny_edges(sk)   if need_sketch else None

        rows.append({
            "stem":           stem,
            "split":          split_name,
            "sketch_lpips":   sketch_lpips(pred, sk, matte)                                          if "sketch_lpips"   in metrics else None,
            "sketch_delta_e": compute_delta_e_hue(pred, sk, (sk.min(axis=-1) < 240) & hair, alpha)  if "sketch_delta_e" in metrics else None,
            "edge_iou":       edge_iou(pred_e, sk_e, matte)                                          if "edge_iou"       in metrics else None,
            "lpips":          hair_masked_lpips(pred, gt, matte)                                     if "lpips_gt"       in metrics else None,
            "bnd_lpips":      boundary_lpips(pred, gt, matte)                                        if "bnd_lpips"      in metrics else None,
            "delta_e_gt":     compute_delta_e_hue(pred, gt, hair, alpha)                             if "delta_e_gt"     in metrics else None,
            "psnr":           compute_psnr(pred, gt, alpha)                                          if "psnr"           in metrics else None,
            # --- R2 ---
            "bnd_lpips_k8":   boundary_band_lpips(pred, gt, matte, 8)                                if "bnd_lpips_k8"   in metrics else None,
            "bnd_lpips_k16":  boundary_band_lpips(pred, gt, matte, 16)                               if "bnd_lpips_k16"  in metrics else None,
            "psnr_bg":        bg_psnr(pred, gt, matte)                                               if "psnr_bg"        in metrics else None,
            "lpips_bg":       bg_lpips(pred, gt, matte)                                              if "lpips_bg"       in metrics else None,
            "arcface":        arcface_cos(pred, _load_face_ref(face_dir, gt_dir, stem, h, w))        if "arcface"        in metrics else None,
        })

        if "hair_fid" in metrics or "kid_hair" in metrics:
            hair_r.append(extract_region_crop(gt,   matte))
            hair_f.append(extract_region_crop(pred, matte))
        if "bnd_fid" in metrics:
            bnd_r.append(extract_region_crop(gt,   bnd_matte, min_px=16))
            bnd_f.append(extract_region_crop(pred, bnd_matte, min_px=16))
        if "full_fid" in metrics:
            full_r.append(gt)
            full_f.append(pred)

    return {"rows": rows, "hair_r": hair_r, "hair_f": hair_f,
            "bnd_r": bnd_r, "bnd_f": bnd_f, "full_r": full_r, "full_f": full_f}


def _compute_fids(parts: dict, metrics: frozenset = ALL_METRICS) -> dict:
    """통합 FID/KID 계산 (dims=2048). metrics에 포함된 것만 계산."""
    fid_targets = [k for k in ("hair_fid", "bnd_fid", "full_fid") if k in metrics]
    out = {"hair_fid": None, "bnd_fid": None, "full_fid": None,
           "kid_hair": None, "kid_hair_std": None, "kid_subset": None}
    if not fid_targets and "kid_hair" not in metrics:
        return out
    key_map = {
        "hair_fid": ("hair_r", "hair_f"),
        "bnd_fid":  ("bnd_r",  "bnd_f"),
        "full_fid": ("full_r", "full_f"),
    }
    if fid_targets:
        print("\nFID 계산 중 (통합, dims=2048)...")
        for k in fid_targets:
            rk, fk = key_map[k]
            out[k] = compute_fid(
                [x for x in parts[rk] if x is not None],
                [x for x in parts[fk] if x is not None],
            )
            print(f"  {k}: {_fmt(out[k])}")

    if "kid_hair" in metrics:
        real = [x for x in parts["hair_r"] if x is not None]
        fake = [x for x in parts["hair_f"] if x is not None]
        n = min(len(real), len(fake))
        subset = min(100, n)
        print(f"\nKID 계산 중 (hair crop, n={n}, subset_size={subset}, n_subsets=100)...")
        out["kid_hair"], out["kid_hair_std"] = compute_kid(real, fake, subset_size=subset)
        out["kid_subset"] = subset
        print(f"  kid_hair: {_fmt(out['kid_hair'])} ± {_fmt(out['kid_hair_std'])}"
              f"   (리포트에 subset_size={subset} 명기 의무)")
    return out


def _merge_parts(pb: dict, pu: dict) -> dict:
    return {k: pb[k] + pu[k] for k in ("hair_r", "hair_f", "bnd_r", "bnd_f", "full_r", "full_f")}


def _n_valid(rows):
    """pred가 실제로 존재해 지표가 하나라도 계산된 행 수.
    (특정 지표만 --metrics로 골라 돌려도 0이 되지 않도록 전 키를 본다.)"""
    return sum(1 for r in rows if any(r.get(k) is not None for k in PER_IMAGE_KEYS))


def _write_per_image(rows, path: Path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["stem", "split"] + PER_IMAGE_KEYS)
        w.writeheader()
        w.writerows(rows)


def _save_and_report(summary, rows, tag, out, n_b, n_u):
    print_summary(summary, tag, n_b, n_u)
    per_path = Path(f"{out}_per_image.csv")
    sum_path = Path(f"{out}_summary.csv")
    _write_per_image(rows, per_path)
    write_summary_csv(summary, tag, sum_path)
    print(f"\n저장 완료:\n  {per_path}\n  {sum_path}")


def main():
    global SPLITS      # --data-root로 교체 가능 (아래)
    parser = argparse.ArgumentParser(description="Evaluate braid/unbraid/combined split (7-metric spec).")
    parser.add_argument("--split",       required=True, choices=list(SPLITS.keys()),
                        help="'braid', 'unbraid', 'combined'")
    parser.add_argument("--pred",        required=True, nargs="+",
                        help="생성 이미지 디렉토리. combined는 'braid_dir unbraid_dir' 순서로 2개 지정")
    parser.add_argument("--pred-suffix", default="",
                        help="pred 파일명 접미사 (예: _full  →  stem_full.png)")
    parser.add_argument("--out",         default=None,
                        help="출력 경로 prefix (기본: eval_results/{split}_{pred_dir_name})")
    parser.add_argument("--tag",         default=None,
                        help="결과 테이블 컬럼 레이블")
    parser.add_argument("--sketch-dir",  default=None,
                        help="sketch 디렉토리 오버라이드 (기본: SPLITS[split]['sketch']). "
                             "combined 모드에서는 braid split에 적용.")
    parser.add_argument("--sketch-dir-unbraid", default=None,
                        help="unbraid split용 sketch 디렉토리 오버라이드. "
                             "combined 모드 전용. 미지정 시 --sketch-dir 값 사용.")
    parser.add_argument("--data-root",   default=None,
                        help="GT/matte/sketch 루트 (기본: dataset/). "
                             "{root}/{split}/{img|matte|sketch}/test/ 레이아웃을 전제한다. "
                             "원본이 플랫하게 놓여 있거나 파일명이 어긋날 때 심볼릭 링크로 "
                             "정규화한 스테이징 디렉터리를 지정하는 용도.")
    parser.add_argument("--face-dir",    default=None,
                        help="ArcFace 기준 얼굴 이미지 디렉터리. 미지정 시 GT(=same-identity "
                             "ceiling). cross-id 평가에서는 experiment_cross_id/face_links/{type} "
                             "을 지정해 'B의 얼굴 identity가 보존됐는가'를 잰다. "
                             "combined 모드에서는 braid split에 적용.")
    parser.add_argument("--face-dir-unbraid", default=None,
                        help="unbraid split용 face 디렉터리 오버라이드. combined 모드 전용. "
                             "미지정 시 --face-dir 값 사용.")
    parser.add_argument("--metrics",     default=None,
                        help="계산할 지표 (쉼표 구분). 기본: 전체. "
                             f"선택 가능: {','.join(sorted(ALL_METRICS))}")
    args = parser.parse_args()

    if args.data_root:
        SPLITS = build_splits(Path(args.data_root).resolve())
        print(f"data-root: {args.data_root}")

    suffix             = args.pred_suffix
    sketch_dir         = Path(args.sketch_dir)         if args.sketch_dir         else None
    sketch_dir_unbraid = Path(args.sketch_dir_unbraid) if args.sketch_dir_unbraid else sketch_dir
    face_dir           = Path(args.face_dir)           if args.face_dir           else None
    face_dir_unbraid   = Path(args.face_dir_unbraid)   if args.face_dir_unbraid   else face_dir
    metrics            = frozenset(args.metrics.split(",")) if args.metrics else ALL_METRICS
    unknown            = metrics - ALL_METRICS
    if unknown:
        print(f"[ERROR] 알 수 없는 metric: {unknown}. 가능: {ALL_METRICS}")
        sys.exit(1)

    if args.split == "combined":
        if len(args.pred) == 1:
            braid_dir = unbraid_dir = Path(args.pred[0])
            if not braid_dir.exists():
                print(f"[ERROR] pred 디렉토리 없음: {braid_dir}")
                sys.exit(1)
        elif len(args.pred) == 2:
            braid_dir, unbraid_dir = Path(args.pred[0]), Path(args.pred[1])
            for p in (braid_dir, unbraid_dir):
                if not p.exists():
                    print(f"[ERROR] pred 디렉토리 없음: {p}")
                    sys.exit(1)
        else:
            print("[ERROR] --split combined은 --pred를 1개(단일 폴더) 또는 2개(braid unbraid) 지정하세요")
            sys.exit(1)

        tag = args.tag or braid_dir.name
        out = Path(args.out) if args.out else ROOT / "eval_results" / f"combined_{braid_dir.name}"
        out.parent.mkdir(parents=True, exist_ok=True)

        print("split  : combined (braid + unbraid)")
        print(f"pred   : {braid_dir}" + (f"  |  {unbraid_dir}" if braid_dir != unbraid_dir else " (단일 폴더, 자동 분리)"))
        print(f"suffix : '{suffix}'")
        print(f"out    : {out}_*\n")

        print("braid 처리 중...")
        pb = _process_split("braid",   braid_dir,   suffix, sketch_dir,         metrics, face_dir)
        print("unbraid 처리 중...")
        pu = _process_split("unbraid", unbraid_dir, suffix, sketch_dir_unbraid, metrics, face_dir_unbraid)

        fid = _compute_fids(_merge_parts(pb, pu), metrics)
        summary = build_summary(pb["rows"], pu["rows"], fid)
        _save_and_report(summary, pb["rows"] + pu["rows"], tag,
                         out, _n_valid(pb["rows"]), _n_valid(pu["rows"]))

    else:
        if len(args.pred) != 1:
            print("[ERROR] braid/unbraid split은 --pred를 1개만 지정하세요")
            sys.exit(1)
        pred_dir = Path(args.pred[0])
        if not pred_dir.exists():
            print(f"[ERROR] pred 디렉토리 없음: {pred_dir}")
            sys.exit(1)
        if args.split == "braid":
            print("[WARN] braid 단독 FID는 2048-dim에서 rank-deficient(n=107<2048). "
                  "FID는 통합(573, --split combined)으로 보고 권장.")

        tag = args.tag or pred_dir.name
        out = Path(args.out) if args.out else ROOT / "eval_results" / f"{args.split}_{pred_dir.name}"
        out.parent.mkdir(parents=True, exist_ok=True)

        ds = SPLITS[args.split]
        print(f"split  : {args.split}")
        print(f"pred   : {pred_dir}")
        print(f"suffix : '{suffix}'")
        print(f"gt     : {ds['img']}")
        print(f"out    : {out}_*\n")

        parts = _process_split(args.split, pred_dir, suffix, sketch_dir, metrics, face_dir)
        fid = _compute_fids(parts, metrics)
        rb, ru = (parts["rows"], None) if args.split == "braid" else (None, parts["rows"])
        summary = build_summary(rb, ru, fid)
        n = _n_valid(parts["rows"])
        _save_and_report(summary, parts["rows"], tag, out,
                         n if args.split == "braid" else 0,
                         n if args.split == "unbraid" else 0)


if __name__ == "__main__":
    main()
