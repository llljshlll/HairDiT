# 평가 결과 모델별 비교

## 모델 비교
sketch-only(mcs3) vs ours (gated)(mcs2) vs SHS vs hairClipV2 vs VividHair 모델 평가항목별 비교
4-seed(braid n=107 / unbraid n=466) 평균값 기준, 각 항목 화살표 방향(↑=클수록 좋음/↓=작을수록 좋음)에 따라 좋은 순서로 정렬. 
mcs2/mcs3/HairCLIPv2/SketchHairSalon/VividHairStyler 4-seed 표의 평균값을 그대로 비교.

**공통 경향 요약**:
- **HairCLIPv2**: Region/Boundary IoU(마스크 형태 자체)는 1위지만, 그 외 화질·GT 일치·배경보존·identity 지표에서는 braid·unbraid 거의 전 항목 5위(최하위) — 마스크 모양은 넓게/다르게 잡되 나머지 품질이 떨어지는 경향.
- **SketchHairSalon**: 배경보존(PSNR_bg/LPIPS_bg/Full-portrait FID)·identity(ArcFace)·Seed 불일치에서 압도적 1위권. 다만 Region/Boundary IoU·Sketch LPIPS·ΔE2000류 구조 지표는 중하위.
- **mcs2/mcs3(HairDiT)**: Hair FID·KID·경계밴드·PSNR_bg·ArcFace 등 다수 지표에서 1~2위 유지, 특히 mcs2(Ours, gated)가 Hair FID·KID·LPIPS(GT) 중심으로 mcs3(Sketch-only) 대비 근소 우위. mcs3는 ΔE2000(GT)·Edge IoU·GT 방향오차에서 강점.
- **VividHairStyler**: 대체로 중위권(2~4위)에 고르게 분포, 극단적 1위·5위 항목은 적음.

### braid (n=107, 4-seed)

##### 구조·색상·화질·리얼리즘
| 항목 | 순위 (좋은 순) |
|---|---|
| Sketch LPIPS ↓ | HairCLIPv2 > VividHairStyler > mcs2 > SketchHairSalon > mcs3 |
| Sketch ΔE2000 ↓ | HairCLIPv2 > VividHairStyler > SketchHairSalon > mcs2 > mcs3 |
| Edge IoU ↑ | mcs3 > SketchHairSalon > mcs2 > VividHairStyler > HairCLIPv2 |
| LPIPS(GT) ↓ | SketchHairSalon > mcs2 > mcs3 > VividHairStyler > HairCLIPv2 |
| ΔE2000(GT) ↓ | SketchHairSalon > mcs3 > VividHairStyler > mcs2 > HairCLIPv2 |
| PSNR ↑ | mcs2 > VividHairStyler > SketchHairSalon > mcs3 > HairCLIPv2 |
| Hair FID ↓ | mcs2 > mcs3 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| KID_hair ↓ | mcs2 > SketchHairSalon > mcs3 > VividHairStyler > HairCLIPv2 |

##### 경계밴드 B
| 항목 | 순위 (좋은 순) |
|---|---|
| Boundary LPIPS(legacy) ↓ | mcs3 > mcs2 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| Bnd LPIPS k=8 ↓ | mcs3 > mcs2 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| Bnd LPIPS k=16 ↓ | mcs2 > mcs3 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| Boundary FID ↓ | mcs3 > mcs2 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| Region IoU ↑ | HairCLIPv2 > mcs3 > SketchHairSalon > mcs2 > VividHairStyler |
| Boundary IoU ↑ | HairCLIPv2 > VividHairStyler > SketchHairSalon > mcs2 > mcs3 |

##### 배경 보존 · identity · 방향 안정성
| 항목 | 순위 (좋은 순) |
|---|---|
| PSNR_bg ↑ | mcs3 > mcs2 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| LPIPS_bg ↓ | mcs2 ≈ mcs3 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| ArcFace cos ↑ | mcs3 > mcs2 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| Full-portrait FID ↓ | SketchHairSalon > mcs2 > mcs3 > VividHairStyler > HairCLIPv2 |
| GT 방향오차 ↓ | mcs3 > SketchHairSalon > mcs2 > VividHairStyler > HairCLIPv2 |
| Seed 불일치 ↓ | SketchHairSalon > VividHairStyler > HairCLIPv2 > mcs2 > mcs3 |

### unbraid (n=466, 4-seed)

##### 구조·색상·화질·리얼리즘
| 항목 | 순위 (좋은 순) |
|---|---|
| Sketch LPIPS ↓ | HairCLIPv2 > VividHairStyler > mcs2 > mcs3 > SketchHairSalon |
| Sketch ΔE2000 ↓ | VividHairStyler > HairCLIPv2 > mcs2 > SketchHairSalon > mcs3 |
| Edge IoU ↑ | mcs3 ≈ SketchHairSalon > mcs2 > VividHairStyler > HairCLIPv2 |
| LPIPS(GT) ↓ | mcs2 > SketchHairSalon > mcs3 > VividHairStyler > HairCLIPv2 |
| ΔE2000(GT) ↓ | SketchHairSalon > VividHairStyler > mcs3 > mcs2 > HairCLIPv2 |
| PSNR ↑ | mcs2 > SketchHairSalon > VividHairStyler > mcs3 > HairCLIPv2 |
| Hair FID ↓ | SketchHairSalon > mcs3 > mcs2 > VividHairStyler > HairCLIPv2 |
| KID_hair ↓ | SketchHairSalon > mcs2 > mcs3 > VividHairStyler > HairCLIPv2 |

##### 경계밴드 B
| 항목 | 순위 (좋은 순) |
|---|---|
| Boundary LPIPS(legacy) ↓ | mcs3 > mcs2 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| Bnd LPIPS k=8 ↓ | mcs2 ≈ mcs3 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| Bnd LPIPS k=16 ↓ | mcs2 > mcs3 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| Boundary FID ↓ | mcs3 > mcs2 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| Region IoU ↑ | HairCLIPv2 > mcs3 > VividHairStyler > SketchHairSalon > mcs2 |
| Boundary IoU ↑ | HairCLIPv2 > VividHairStyler > SketchHairSalon > mcs3 > mcs2 |

##### 배경 보존 · identity · 방향 안정성
| 항목 | 순위 (좋은 순) |
|---|---|
| PSNR_bg ↑ | mcs3 > mcs2 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| LPIPS_bg ↓ | mcs3 > mcs2 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| ArcFace cos ↑ | mcs3 > mcs2 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| Full-portrait FID ↓ | SketchHairSalon > mcs2 > mcs3 > VividHairStyler > HairCLIPv2 |
| GT 방향오차 ↓ | mcs2 > mcs3 > SketchHairSalon > VividHairStyler > HairCLIPv2 |
| Seed 불일치 ↓ | SketchHairSalon > HairCLIPv2 > VividHairStyler > mcs2 > mcs3 |

