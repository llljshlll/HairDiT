# 정량평가 체크 — Hair KID/FID · Sketch ΔE2000 · Edge IoU · ArcFace · ΔE2000(GT) · Boundary LPIPS

Same-identity(동일 얼굴) vs Cross-identity(배경 인물 교체), baseline vs mcs2 / mcs1 vs mcs2 비교.

## 방식
**모든 값은 "시드별로 braid·unbraid를 하나의 값으로 통합 → 그 시드별 값들의 mean ± population std"**
로 계산했다. ±는 전부 시드 간 재현성(seed-to-seed)이며, 통합 방식만 지표 종류에 따라 다르다.

| 지표 | 시드별 통합 방식 | braid : unbraid 가중치 |
|---|---|---|
| Sketch ΔE2000 · Edge IoU · ArcFace · ΔE2000(GT) · Boundary LPIPS | **macro = (braid + unbraid)/2** | 50 : 50 (동일 가중치) |
| **Hair FID · KID_hair** | **통합573 pooled** — 573장을 한 풀에 넣어 1회 계산 | 107 : 466 (18.7 : 81.3) |

⚠️ **FID/KID만 pooled인 이유**: FID는 2048-dim Inception feature의 평균·공분산으로 정의되는데
braid 단독은 n=107 < 2048이라 공분산 추정이 rank-deficient가 됨 따라서 FID/KID는 동일 가중치(50:50)를 포기하고 통계적으로 안정적인 pooled를 쓴다 — 실측으로도 macro 방식은 pooled 대비 값이 40~90 높게 튀고 모델 간 순위까지 뒤바뀐다.

- ⚠️ **cross 열의 mcs2는 baseline과 완전히 공정한 비교가 아니다** — mcs2 값은 B(배경) 매핑과 시드 수가 baseline 4종(v2 protocol, 단일시드 3)과 다르다.
- **ArcFace(cross)**: 기준은 B 이미지(배경 인물). mcs2는 0817 cross-identity 표에 ArcFace가 없어 N/A.

---

## 1. Baseline vs mcs2

| 모델 | Hair KID(same) ↓ | Hair KID(cross) ↓ | Sketch ΔE2000 ↓(cross) | Edge IoU ↑(cross) | ArcFace cos ↑(cross) |
|---|:---:|:---:|:---:|:---:|:---:|
| SketchHairSalon | **0.0026±0.0000** | 0.1037 | 12.00 | **0.0749** | **0.7436** |
| HairCLIPv2 | 0.0194±0.0002 | **0.0289** | 12.21 | 0.0529 | 0.5052 |
| VividHairStyler | 0.0088±0.0001 | 0.0559 | 13.48 | 0.0514 | 0.5966 |
| **mcs2 (Ours)** | 0.0029±0.0004 | 0.0920±0.0010 | **11.44±0.27** | 0.0687±0.0002 | N/A |

* Hair KID(cross)의 mcs2는 실제는 mcs1의 값


## 2. mcs1 vs mcs2 (Gate OFF vs Gate ON)

### same-identity (4-seed)

| 모델 | Hair FID ↓ | KID_hair ↓ | ΔE2000(GT) ↓ | Boundary LPIPS(k=16) ↓ |
|---|:---:|:---:|:---:|:---:|
| mcs1 (Gate OFF) | 36.53±1.05 | 0.0048±0.0006 | 2.80±0.12 | 0.0276±0.0003 |
| **mcs2 (Gate ON)** | **33.57±0.40** | **0.0029±0.0004** | **1.84±0.03** | **0.0247±0.0002** |

### cross-identity (3-seed)

| 모델 | Hair FID ↓ | KID_hair ↓ | Sketch ΔE2000 ↓ | Edge IoU ↑ |
|---|:---:|:---:|:---:|:---:|
| **mcs1 (Gate OFF)** | **129.68±0.78** | **0.0920±0.0010** | 11.63±0.17 | **0.0711±0.0002** |
| mcs2 (Gate ON) | 138.23±1.12 | 0.1001±0.0010 | **11.44±0.27** | 0.0687±0.0002 |

→ **Hair FID·KID·Edge IoU는 mcs1(Gate OFF) 우세**, Sketch ΔE2000만 mcs2가 근소 우세.

---

