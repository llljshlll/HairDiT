

## 학습 조건
기존 mcs1, mcs3, mcs5, mcs6을 새로운 방식으로 재구성하여 진행

기존 방식:
| 논문 명칭 | Matte-CNN | Raw Matte | Gate | 내부 명칭 |
|---|:---:|:---:|:---:|:---:|
| Ours | ✓ | ✓ | ✗ | mcs1 |
| Ours + Gate | ✓ | ✓ | ✓ | mcs2 |
| Sketch-only | ✗ | ✗ | ✗ | mcs3 |
| Sketch-only + Gate | ✗ | ✗ | ✓ | mcs4 |
| Raw-only | ✗ | ✓ | ✗ (새로운 방식에서는 ✓로 변경) | mcs5 |
| Matte-CNN-only | ✓ | ✗ | ✗ (새로운 방식에서는 ✓로 변경) | mcs6 |

기존 방식의 mcs2를 run7의 기준 설정으로 둔다.    
새로운 mcs 방식은 run7_mcs1, run7_mcs2, run7_mcs3과 같이 명명한다.
따라서 현재 학습된 run_mcs2는 run7_mcs2를 의미한다.

모든 방식은 run7_mcs2의 설정을 따른다.
- run7_mcs1은 run7_mcs2에서 gate만 끈 설정이다. phase1 resume 여부를 제외한 다른 설정은 변경하지 않는다.
- un7_mcs3은 matte가 없으므로 gate 없이 진행하며, run7_mcs2에서 입력으로 sketch만 사용한다.
- run7_mcs5와 run7_mcs6은 기존 방식과 달리 gate on(hard gate)으로 진행한다. 따라서 run7_mcs2의 gate 설정을 변경하지 않는다. Matte-CNN 또는 Raw Matte를 끄는 설정만 각각 적용하되, 현재 메커니즘에 맞춰 진행한다.



## 정량지표
Unbraid: 466장, Braid: 107장, 총 573장 사용  
CRG 1.5 + BLD full (step 20) + Pixel Matte-Blend + Feathering OFF (0), epoch20 기준  
mcs2(Ours)는 기존 run7 phase2 rawstart epoch20 결과와 동일하게 비교

### braid (n=107)

#### 구조·색상·화질·리얼리즘 (matte 내부)

| Run | 설정 | Sketch LPIPS ↓ | Sketch ΔE2000 ↓ | Edge IoU ↑ | LPIPS(GT) ↓ | ΔE2000(GT) ↓ | PSNR ↑ | Hair FID ↓ | KID_hair ↓ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mcs1 | Gate OFF | 0.4843 | 13.8734 | **0.0961** | 0.1319 | 3.1991 | 16.3227 | 대기 | 대기 |
| mcs2 | Ours | 0.4668 | **12.8527** | 0.0952 | 0.1141 | 2.0913 | 16.6502 | **69.7901** | 0.0002±0.0004 |
| mcs3 | Sketch-only | 0.4908 | 13.0287 | 0.0956 | 0.1208 | **1.7154** | 16.1589 | 대기 | 대기 |
| mcs5 | RawMatte + Gate | 0.4777 | 13.5523 | 0.0953 | **0.1139** | 2.0726 | **16.7095** | 대기 | 대기 |
| mcs6 | MatteCNN + Gate | **0.4562** | 13.3729 | 0.0944 | 0.1140 | 3.4606 | 16.5351 | 대기 | 대기 |

#### 경계밴드 B

| Run | 설정 | Boundary LPIPS ↓(legacy) | Bnd LPIPS k=8 ↓ | Bnd LPIPS k=16 ↓ | Boundary FID ↓ | Region IoU ↑ | Boundary IoU ↑ |
|---|---|---:|---:|---:|---:|---:|---:|
| mcs1 | Gate OFF | 0.0063 | 0.0084 | 0.0273 | 대기 | **0.1629** | **0.1159** |
| mcs2 | Ours | 0.0057 | 0.0076 | 0.0245 | **3.8197** | 0.1433 | 0.1011 |
| mcs3 | Sketch-only | **0.0052** | **0.0070** | 0.0248 | 대기 | 0.1602 | 0.1019 |
| mcs5 | RawMatte + Gate | 0.0056 | 0.0072 | **0.0242** | 대기 | 0.1413 | 0.0955 |
| mcs6 | MatteCNN + Gate | 0.0063 | 0.0082 | 0.0256 | 대기 | 0.1538 | 0.1137 |

#### 배경 보존 · identity · 방향 안정성

| Run | 설정 | PSNR_bg ↑ | LPIPS_bg ↓ | ArcFace cos ↑ | Full-portrait FID ↓ | GT 방향오차 ↓ | Seed 불일치 ↓ |
|---|---|---:|---:|---:|---:|---:|---:|
| mcs1 | Gate OFF | 47.4563 | 0.0004 | **0.9572** | 대기 | **19.53±4.55** | **12.92±3.07** |
| mcs2 | Ours | 47.8856 | **0.0003** | 0.9194 | **40.6367** | 21.19±4.71 | 14.96±3.15 |
| mcs3 | Sketch-only | **48.0490** | **0.0003** | 0.8997 | 대기 | 19.90±4.70 | 16.15±3.92 |
| mcs5 | RawMatte + Gate | 47.9759 | **0.0003** | 0.9248 | 대기 | 19.56±4.65 | 14.33±3.45 |
| mcs6 | MatteCNN + Gate | 47.5576 | 0.0004 | 0.9022 | 대기 | 19.56±4.61 | 13.15±3.22 |

### unbraid (n=466)

#### 구조·색상·화질·리얼리즘 (matte 내부)

| Run | 설정 | Sketch LPIPS ↓ | Sketch ΔE2000 ↓ | Edge IoU ↑ | LPIPS(GT) ↓ | ΔE2000(GT) ↓ | PSNR ↑ | Hair FID ↓ | KID_hair ↓ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mcs1 | Gate OFF | 0.7000 | 13.1133 | 0.0485 | 0.1852 | 2.4115 | 16.7622 | 대기 | 대기 |
| mcs2 | Ours | 0.6755 | **12.3779** | 0.0468 | 0.1726 | 1.5365 | 17.2934 | **34.2327** | 0.0051±0.0023 |
| mcs3 | Sketch-only | 0.7051 | 12.4818 | **0.0495** | 0.1895 | **1.3229** | 16.7114 | 대기 | 대기 |
| mcs5 | RawMatte + Gate | 0.7040 | 12.7311 | 0.0494 | 0.1805 | 1.3797 | 17.1794 | 대기 | 대기 |
| mcs6 | MatteCNN + Gate | **0.6694** | 13.0178 | 0.0466 | **0.1718** | 1.8958 | **17.4436** | 대기 | 대기 |

#### 경계밴드 B

| Run | 설정 | Boundary LPIPS ↓(legacy) | Bnd LPIPS k=8 ↓ | Bnd LPIPS k=16 ↓ | Boundary FID ↓ | Region IoU ↑ | Boundary IoU ↑ |
|---|---|---:|---:|---:|---:|---:|---:|
| mcs1 | Gate OFF | 0.0074 | 0.0033 | 0.0212 | 대기 | **0.1402** | **0.0978** |
| mcs2 | Ours | 0.0066 | **0.0029** | **0.0190** | **2.5609** | 0.1199 | 0.0815 |
| mcs3 | Sketch-only | **0.0064** | **0.0029** | 0.0198 | 대기 | 0.1398 | 0.0908 |
| mcs5 | RawMatte + Gate | 0.0066 | **0.0029** | 0.0192 | 대기 | 0.1253 | 0.0826 |
| mcs6 | MatteCNN + Gate | 0.0069 | 0.0031 | 0.0194 | 대기 | 0.1200 | 0.0852 |

#### 배경 보존 · identity · 방향 안정성

| Run | 설정 | PSNR_bg ↑ | LPIPS_bg ↓ | ArcFace cos ↑ | Full-portrait FID ↓ | GT 방향오차 ↓ | Seed 불일치 ↓ |
|---|---|---:|---:|---:|---:|---:|---:|
| mcs1 | Gate OFF | 41.8648 | 0.0015 | 0.9698 | 대기 | **12.90±3.91** | 7.88±2.56 |
| mcs2 | Ours | 42.3961 | 0.0015 | 0.9718 | **13.5973** | 13.28±3.89 | 8.66±2.51 |
| mcs3 | Sketch-only | **42.4717** | **0.0014** | **0.9738** | 대기 | 13.42±4.08 | 10.36±3.37 |
| mcs5 | RawMatte + Gate | 42.4202 | 0.0015 | 0.9723 | 대기 | 13.21±3.94 | 9.25±2.90 |
| mcs6 | MatteCNN + Gate | 42.3103 | 0.0015 | 0.9713 | 대기 | **12.90±3.89** | **7.76±2.57** |

**braid FID/KID 계산 대기**: mcs1·mcs3·mcs5·mcs6의 Hair FID/KID_hair/Boundary FID/Full-portrait FID braid·unbraid 분리값은 573장 생성 이미지가 아직 남아 있는 원격 서버에서 재계산 예정이다 — 절차는 `planning/[0816]braid_unbraid_fid_split.md` 참고. mcs2는 로컬(`outputs/eval573/`)에 원본 생성 이미지가 남아 있어 우선 계산했다(위 표에 반영). 단 braid n=107 KID(0.0002±0.0004)는 subset_size=100이 표본(107장)의 대부분을 덮어 MMD 추정이 깨진 값으로 보이며 참고용일 뿐 신뢰하지 않는다 — unbraid(n=466) KID(0.0051±0.0023)는 통합값(0.0029)과 같은 자릿수라 상대적으로 덜 불안정하다.

### Cross-Identity 

## 정성지표
### gt sketch
| sketch | mcs1 (Gate OFF) | mcs2(Ours) | mcs3(Sketch-Only) |  mcs5(RawMatte) | mcs6(MatteCNN) |
|---|---|---|---|---|---|
| <img src="../dataset/test/recolor_sketch/CM_1007.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/CM_1007.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/CM_1007.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/CM_1007.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/CM_1007.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/CM_1007.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/CM_1027.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/CM_1027.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/CM_1027.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/CM_1027.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/CM_1027.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/CM_1027.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/CM_1033.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/CM_1033.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/CM_1033.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/CM_1033.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/CM_1033.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/CM_1033.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/CM_1067.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/CM_1067.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/CM_1067.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/CM_1067.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/CM_1067.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/CM_1067.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/CM_1068.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/CM_1068.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/CM_1068.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/CM_1068.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/CM_1068.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/CM_1068.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/CM_1082.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/CM_1082.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/CM_1082.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/CM_1082.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/CM_1082.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/CM_1082.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/CM_1084.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/CM_1084.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/CM_1084.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/CM_1084.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/CM_1084.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/CM_1084.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/CM_1172.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/CM_1172.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/CM_1172.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/CM_1172.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/CM_1172.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/CM_1172.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/braid_2548.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/braid_2548.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/braid_2548.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/braid_2548.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/braid_2548.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/braid_2548.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/braid_2562_1.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/braid_2562_1.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/braid_2562_1.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/braid_2562_1.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/braid_2562_1.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/braid_2562_1.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/braid_2625.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/braid_2625.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/braid_2625.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/braid_2625.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/braid_2625.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/braid_2625.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/braid_4156.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/braid_4156.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/braid_4156.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/braid_4156.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/braid_4156.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/braid_4156.png" width="70"> |
| <img src="../dataset/test/recolor_sketch/braid_4276.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/braid_4276.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/braid_4276.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/gt/seed42/braid_4276.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/gt/42/braid_4276.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/gt/42/braid_4276.png" width="70"> |

### color sketch
| sketch | mcs1 (Gate OFF) | mcs2(Ours) | mcs3(Sketch-Only) |  mcs5(RawMatte) | mcs6(MatteCNN) |
|---|---|---|---|---|---|
| <img src="../dataset/test/sketch/CM_1007.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/CM_1007.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/CM_1007.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/CM_1007.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/CM_1007.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/CM_1007.png" width="70"> |
| <img src="../dataset/test/sketch/CM_1027.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/CM_1027.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/CM_1027.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/CM_1027.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/CM_1027.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/CM_1027.png" width="70"> |
| <img src="../dataset/test/sketch/CM_1033.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/CM_1033.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/CM_1033.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/CM_1033.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/CM_1033.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/CM_1033.png" width="70"> |
| <img src="../dataset/test/sketch/CM_1067.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/CM_1067.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/CM_1067.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/CM_1067.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/CM_1067.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/CM_1067.png" width="70"> |
| <img src="../dataset/test/sketch/CM_1068.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/CM_1068.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/CM_1068.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/CM_1068.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/CM_1068.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/CM_1068.png" width="70"> |
| <img src="../dataset/test/sketch/CM_1082.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/CM_1082.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/CM_1082.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/CM_1082.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/CM_1082.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/CM_1082.png" width="70"> |
| <img src="../dataset/test/sketch/CM_1084.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/CM_1084.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/CM_1084.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/CM_1084.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/CM_1084.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/CM_1084.png" width="70"> |
| <img src="../dataset/test/sketch/CM_1172.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/CM_1172.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/CM_1172.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/CM_1172.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/CM_1172.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/CM_1172.png" width="70"> |
| <img src="../dataset/test/sketch/braid_2548.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/braid_2548.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/braid_2548.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/braid_2548.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/braid_2548.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/braid_2548.png" width="70"> |
| <img src="../dataset/test/sketch/braid_2562_1.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/braid_2562_1.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/braid_2562_1.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/braid_2562_1.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/braid_2562_1.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/braid_2562_1.png" width="70"> |
| <img src="../dataset/test/sketch/braid_2625.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/braid_2625.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/braid_2625.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/braid_2625.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/braid_2625.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/braid_2625.png" width="70"> |
| <img src="../dataset/test/sketch/braid_4156.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/braid_4156.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/braid_4156.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/braid_4156.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/braid_4156.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/braid_4156.png" width="70"> |
| <img src="../dataset/test/sketch/braid_4276.png" width="70"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/braid_4276.png" width="70"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/braid_4276.png" width="70"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/braid_4276.png" width="70"> | <img src="../outputs/0815/run7_mcs5_phase2/epoch20/color/42/braid_4276.png" width="70"> | <img src="../outputs/0815/run7_mcs6_phase2/epoch20/color/42/braid_4276.png" width="70"> |



## 논문에 표시된 각 실험에 따른 효과 vs 실제 효과
논문 §4.2는 MatteCNN bias × RawMatte anchor의 2×2 factorial만 정식 ablation으로 두고, gate는 직교하는 별도 축(§4.8)으로 분리함.
수치는 Cross-identity Hair FID(§4.6, Table 1, leakage-free, 3 seed) / GT-bg(§4.7, Table 2) 기준.

1. gate on/off

<img src="../outputs/0814/gate_on_off_paper_figure.png" width="700">

- 논문(정성지표) : ON이면 unbraid가 더 매끄럽고 스케치 색에 충실, OFF면 잔차가 강해 braid의 strand-crossing·knot boundary 표현이 좋음    
- 실제(정성지표) : gate off면, boundary 표현이 더 좋음

| | CM_1082(GT) | CM_1172(color) | braid_2548(GT) | braid_2562_1(color) |
|---|---|---|---|---|
| mcs1 | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/CM_1082.png" width="120"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/CM_1172.png" width="120"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/gt/42/braid_2548.png" width="120"> | <img src="../outputs/0815/run7_mcs1_phase2/epoch20/color/42/braid_2562_1.png" width="120"> |
| mcs2 | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/CM_1082.png" width="120"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/CM_1172.png" width="120"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/gt/42/braid_2548.png" width="120"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/braid_2562_1.png" width="120"> |

- 논문(정량지표) : gate on/off 큰 차이 없음    
- 실제(정량지표) : 논문과 달리 차이가 작지 않음. Hair FID mcs1 37.89 → mcs2 **33.68**(4.2pt 개선, 논문에서 raw matte·matte-cnn 신호를 하나씩 추가할 때 개선폭 ~11pt의 절반 수준). KID_hair도 0.0055→**0.0029**로 거의 절반, Full-portrait FID도 17.60→**15.06**로 크게 개선 — realism/분포 지표에서는 gate ON이 뚜렷하게 좋음. 반대로 구조 지표는 gate OFF가 더 좋음: Region IoU **0.1445**·Boundary IoU **0.1012**로 5개 중 최고 — mcs2는 각각 0.1242·0.0851로 더 낮아(약 14~16%↓, mcs2도 로컬 재현으로 계산 완료·`### 경계밴드 B` 참고) gate ON이 구조 충실도를 깎는다는 게 수치로도 확인됨. ArcFace cos도 **0.9635**로 최고(identity 보존), GT 방향오차도 **14.14**로 최고. 즉 "큰 차이 없음"이 아니라 **realism vs 구조 충실도의 트레이드오프가 뚜렷**하며, 위 정성지표(실제)의 "gate off가 boundary 표현이 더 좋음" 관찰과도 방향이 일치함  


2. Sketch-only (mcs3)

<img src="../outputs/0814/sketch_only_paper_figure.png" width="400">

- 논문(정성지표) : 텍스처가 거칠고 strand flow가 덜 일관됨(§4.5, Fig.2). 스트로크 색을 가장 문자 그대로 따라감(색 fidelity ↔ realism 트레이드오프, §5)    
- 실제(정성지표) : 논문에서 제기된 것에 비해 텍스처가 거칠지 않고, GT image에서는 다른지표와 거의 구분할 수 없음, 색 학습이 가장 잘 되어보이고, 형광색 stroke에 대해 잘 표현함  

| | braid_2562_1(color) | CM_1067(color) | CM_1068(color) | braid_4156(color) |
|---|---|---|---|---|
| mcs3 | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/braid_2562_1.png" width="120"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/CM_1067.png" width="120"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/CM_1068.png" width="120"> | <img src="../outputs/0815/run7_mcs3_phase2/epoch20/color/seed42/braid_4156.png" width="120"> |
| mcs2 | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/braid_2562_1.png" width="120"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/CM_1067.png" width="120"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/CM_1068.png" width="120"> | <img src="../outputs/0815/run7_mcs2_phase2/epoch20/color/42/braid_4156.png" width="120"> |

- 논문(정량지표) : matte 신호가 전혀 없는 baseline. Hair FID **159.95로 최악**. ΔE2000은 2.1550으로 최고. GT-bg 프로토콜에서는 배경 누수 덕에 **오히려 최고로 보이는 ranking inversion**이 발생(§4.6, Fig.3) → 논문 contribution 3번의 근거  
- 실제(정량지표) : Hair FID **35.14로 5개 중 2위**(1위 mcs2 33.68) — mcs1(37.89)보다도 낮아 논문의 "최악" 서술과 반대. Sketch ΔE2000(12.76)·ΔE2000(GT)(1.52)·Edge IoU(0.0726)는 실제로도 5개 중 최고 — 색 fidelity 우위는 재현됨. PSNR_bg도 45.26으로 5개 중 최고 — 배경 쪽에서 가장 유리하게 나오는 경향은 paper의 ranking inversion과 방향이 일치(단, 평가 프로토콜 자체는 paper의 GT-bg와 다르므로 동일 메커니즘이라 단정은 어려움)   

3. RawMatte (mcs5)

- 논문(정량지표) : sketch latent + raw matte anchor 단독. Hair FID 159.95 → **148.73**. pixel unshuffle + 1×1 conv로 편집 영역의 명시적 기하 정보를 줌(§3.3.2)   
- 실제(정량지표) : Hair FID **35.89로 5개 중 4위** — mcs3(sketch-only, 35.14)보다도 나빠 "raw matte 추가가 sketch-only보다 낫다"는 논문 서열과 반대. 단, 실제는 gate ON이 같이 걸려 있어 논문과 세팅이 다름  

4. MatteCNN (mcs6)

- 논문(정량지표) : sketch latent + zero-init 학습형 region-aware bias 단독. Hair FID 159.95 → **148.10**. RawMatte·MatteCNN 어느 한쪽만 넣어도 ~11점 개선, 둘 다 넣으면(Ours, mcs1) **140.11±3.10**으로 최고 → 두 신호는 역할 분담이 아니라 같은 목표로 latent를 미는 **additive** 관계(§5). GT-bg에서도 Ours가 PSNR 14.2263·Edge IoU 0.0728로 최고  
- 실제(정량지표) : mcs6 Hair FID **36.35로 5개 중 3위**. 논문에서 "최고"라던 mcs1(=RawMatte+MatteCNN 둘 다, gate off)은 실제로 Hair FID **37.89로 5개 중 최하위** — 논문의 additive 최적 조합 서열이 재현되지 않음  
  
단, 논문에 나온 방식은 mcs1이 ours라고 정의. 현재는 mcs2가 ours라고 정의하며, mcs5, 6도 gate on으로 설정 되어있음.
