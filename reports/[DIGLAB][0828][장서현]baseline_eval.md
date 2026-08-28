# Cross-Identity v2 — 베이스라인 4종 정량평가

0825 보고서가 남긴 공백("베이스라인 3종은 cross-identity 평가가 진행되지 않아 mcs1-6끼리만 비교")을
메우는 실험. 설계: `HairDiT/planning/[0827]crossid_v2_design.md`.


---

## 1. 실험 개요

| 항목 | 내용 |
|---|---|
| 목적 | 배경 인물을 바꿔도 출력 헤어가 sketch에 충실한가(외형 누설) + 배경의 얼굴 identity가 보존되는가 |
| A(sketch·matte) | `dataset/{braid,unbraid}/{sketch,matte}/test` — braid 107 + unbraid 466 = 573 |
| B(배경 얼굴) | `dataset_tuning/unbraid/img/test` (ArcFace 검출 가능 풀, 418장) |
| 매핑 | braid: cross-TYPE 107→418 중복없음 / unbraid: cross-ID 466→418, 48장만 2회 재사용, `A_id≠B_id` 강제 |
| 스케치 | 원본 컬러 스케치 그대로(recolor·densify 없음) |
| 시드 | 3 (단일) |
| 모델 | HairCLIPv2 · SketchHairSalon · VividHairStyler · SD35_controlNet |
| 생성량 | 573장 × 4모델 = 2,292장 (전량 생성 확인) |

**마스킹**: GT matte(A 기준)로 헤어 영역 격리. ΔE·PSNR·FID·KID = soft-alpha, Edge IoU = binary.
Sketch LPIPS/ΔE2000/Edge IoU/PSNR은 braid/unbraid 분리 + macro-avg, Hair FID/KID는 2048-dim 공분산이
소표본에서 rank-deficient하므로 **통합(573)만** 보고.

---

## 2. 결과 (seed 3 단일 — ± 없음)

### 2-1. Braid (n=107)

| 모델 | Sketch LPIPS ↓ | Sketch ΔE2000 ↓ | Edge IoU ↑ | PSNR (hair) ↑ |
|---|:---:|:---:|:---:|:---:|
| HairCLIPv2 | 0.4035 | 12.19 | 0.0669 | **10.88** |
| SketchHairSalon | 0.5055 | **9.98** | **0.0983** | 10.62 |
| VividHairStyler | **0.4048** | 12.55 | 0.0558 | 10.38 |
| SD35_controlNet | 0.4887 | 16.02 | 0.0900 | 10.12 |

### 2-2. Unbraid (n=466)

| 모델 | Sketch LPIPS ↓ | Sketch ΔE2000 ↓ | Edge IoU ↑ | PSNR (hair) ↑ |
|---|:---:|:---:|:---:|:---:|
| HairCLIPv2 | **0.5404** | 12.22 | 0.0389 | **10.64** |
| SketchHairSalon | 0.7423 | 14.02 | **0.0514** | 10.32 |
| VividHairStyler | 0.6362 | 14.40 | 0.0470 | 9.88 |
| SD35_controlNet | 0.6625 | **14.97** | 0.0543 | 9.73 |

### 2-3. Macro-avg = (braid + unbraid) / 2

| 모델 | Sketch LPIPS ↓ | Sketch ΔE2000 ↓ | Edge IoU ↑ | PSNR (hair) ↑ |
|---|:---:|:---:|:---:|:---:|
| **HairCLIPv2** | **0.4719** | 12.21 | 0.0529 | **10.76** |
| SketchHairSalon | 0.6239 | **12.00** | **0.0749** | 10.47 |
| VividHairStyler | 0.5205 | 13.48 | 0.0514 | 10.13 |
| SD35_controlNet | 0.5756 | 15.49 | 0.0721 | 9.92 |

### 2-4. Hair FID (통합 573, unpaired)

| 모델 | Hair FID ↓ |
|---|:---:|
| **HairCLIPv2** | **81.35** |
| VividHairStyler | 113.07 |
| SD35_controlNet | 115.65 |
| SketchHairSalon | 140.87 |

### 2-5. KID_hair (통합 573, unpaired, subset_size=100)

| 모델 | KID_hair ↓ |
|---|:---:|
| **HairCLIPv2** | **0.0289±0.0031** |
| VividHairStyler | 0.0559±0.0038 |
| SD35_controlNet | 0.0702±0.0058 |
| SketchHairSalon | 0.1037±0.0066 |

=> Hair FID와 KID 순위(HairCLIPv2 < VividHairStyler < SD35 < SketchHairSalon)가 완전히 동일.

### 2-6. ArcFace cos ↑ (기준 = B 이미지) — v2 신규 지표

| 모델 | braid | unbraid | macro | 검출 유효 n(braid/unbraid) |
|---|:---:|:---:|:---:|:---:|
| HairCLIPv2 | 0.4743 | 0.5361 | 0.5052 | 86/107 · 432/466 |
| SketchHairSalon | **0.7023** | **0.7849** | **0.7436** | 93/107 · 412/466 |
| VividHairStyler | 0.6086 | 0.5846 | 0.5966 | 99/107 · 455/466 |
| SD35_controlNet | 0.7211 | 0.7644 | 0.7427 | 94/107 · 431/466 |

- 기준은 **B 이미지**(`--face-dir` = stage_face의 img, 즉 실제로 배경으로 합성한 인물). A GT가 아니다.
- 검출 유효 n은 573 중 얼굴이 실제로 검출된 표본 수(ArcFace 자체가 얼굴을 못 찾으면 NaN 처리 후 평균에서 제외).
