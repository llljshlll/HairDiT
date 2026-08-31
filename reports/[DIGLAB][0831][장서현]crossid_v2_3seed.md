# Cross-Identity v2 — 베이스라인 4종 3seed 평가

[[DIGLAB][0828][장서현]baseline_eval.md](./[DIGLAB][0828][장서현]baseline_eval.md)(seed 3 단일)의 후속.
seed 1·2를 추가 생성·평가해 3seed로 집계했다.

---

## 0. 방법론

[[DIGLAB][0829][장서현]quant_eval_check.md](./[DIGLAB][0829][장서현]quant_eval_check.md) 방식 그대로:

> **시드별로 braid·unbraid를 하나의 값으로 통합 → 그 시드별 값들의 mean ± population std**

| 지표 | 시드별 통합 방식 | braid:unbraid 가중치 |
|---|---|---|
| Sketch LPIPS·ΔE2000·Edge IoU·PSNR·ArcFace | **macro = (braid+unbraid)/2** | 50:50 |
| Hair FID·KID_hair | **pooled573** (braid n=107<2048, 공분산 rank-deficient라 macro 대신 pooled) | 107:466 |

± 는 population std(ddof=0, `statistics.pstdev`) — 3개 시드값을 표본이 아니라 전체로 취급.
데이터·매핑·모델·스케치 조건은 [0828]과 동일(§1 참조), 시드만 {1,2,3} 3개.

---

## 1. Baseline vs mcs2 (3seed)

[[DIGLAB][0829][장서현]quant_eval_check.md](./[DIGLAB][0829][장서현]quant_eval_check.md) §1 표를 갱신.
baseline 3종의 (cross) 컬럼을 본 리포트의 3seed 값으로 교체했다(기존 표는 seed3 단일값).

| 모델 | Hair KID(same) ↓ | Hair KID(cross) ↓ | Sketch ΔE2000 ↓(cross) | Edge IoU ↑(cross) | ArcFace cos ↑(cross) |
|---|:---:|:---:|:---:|:---:|:---:|
| SketchHairSalon | **0.0026±0.0000** | 0.1040±0.0002 | 12.01±0.003 | **0.0749±0.0000** | **0.7437±0.0002** |
| HairCLIPv2 | 0.0194±0.0002 | **0.0285±0.0003** | 12.20±0.003 | 0.0530±0.0001 | 0.5038±0.0011 |
| VividHairStyler | 0.0088±0.0001 | 0.0562±0.0003 | 13.45±0.036 | 0.0517±0.0002 | 0.5984±0.0041 |
| **mcs2 (Ours)** | 0.0029±0.0004 | 0.0920±0.0010 | **11.44±0.27** | 0.0687±0.0002 | 0.9491±0.0062 |


- baseline (cross) 4열 모두 이번 3seed 재계산치로 교체 — 값 자체는 §1과 동일, 유효자릿수만 정리.
- Sketch ΔE2000(cross)의 SD35_controlNet은 시드 분산이 커서(§2) 이 표에는 제외(3종만 비교 대상인
  원표 구성을 유지). 필요하면 §1-1 표에서 확인.



## 2. 전체 결과 (3seed mean ± population std)

### 2-1. macro 지표

| 모델 | Sketch LPIPS ↓ | Sketch ΔE2000 ↓ | Edge IoU ↑ | PSNR (hair) ↑ | ArcFace cos ↑ |
|---|:---:|:---:|:---:|:---:|:---:|
| HairCLIPv2 | **0.4721±0.0002** | 12.2046±0.0028 | 0.0530±0.0001 | **10.7572±0.0011** | 0.5038±0.0011 |
| SketchHairSalon | 0.6241±0.0002 | 12.0064±0.0031 | **0.0749±0.0000** | 10.4735±0.0007 | **0.7437±0.0002** |
| VividHairStyler | 0.5209±0.0003 | 13.4489±0.0360 | 0.0517±0.0002 | 10.1173±0.0104 | 0.5984±0.0041 |
| SD35_controlNet | 0.5693±0.0107 | 17.0460±1.5726 | 0.0703±0.0014 | 9.6639±0.2179 | 0.6991±0.0315 |

### 2-2. Hair FID·KID_hair (pooled573)

| 모델 | Hair FID ↓ | KID_hair ↓ |
|---|:---:|:---:|
| **HairCLIPv2** | **80.8956±0.3479** | **0.0285±0.0003** |
| VividHairStyler | 113.2486±0.2615 | 0.0562±0.0003 |
| SD35_controlNet | 123.2649±5.6987 | 0.0795±0.0069 |
| SketchHairSalon | 141.3379±0.3326 | 0.1040±0.0002 |

### 2-3. 시드별 원값 (참고)

| 모델 | 지표 | seed1 | seed2 | seed3 |
|---|---|:---:|:---:|:---:|
| SD35_controlNet | Sketch ΔE2000 | 16.4427 | 19.2015 | 15.4939 |
| SD35_controlNet | PSNR | 9.3909 | 9.6768 | 9.9241 |
| SD35_controlNet | Hair FID | 129.3604 | 124.7830 | 115.6513 |
| HairCLIPv2 | Hair FID | 80.8312 | 80.5054 | 81.3503 |

---
