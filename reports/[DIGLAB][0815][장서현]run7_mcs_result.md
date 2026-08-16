

## 학습 조건
기존의 mcs1, mcs3, mcs5, mcs6을 새로운 방식으로 진행.

기존 방식 :
| 논문 이름 | Matte-CNN | Raw Matte | Gate | (내부) |
|---|:---:|:---:|:---:|:---:|
| Ours | ✓ | ✓ | ✗ | mcs1 |
| Ours + Gate | ✓ | ✓ | ✓ | mcs2 |
| Sketch-only | ✗ | ✗ | ✗ | mcs3 |
| Sketch-only + Gate | ✗ | ✗ | ✓ | mcs4 |
| Raw-only | ✗ | ✓ | ✗(새로운 방식에서는 ✓로 바꿈) | mcs5 |
| Matte-CNN-only | ✓ | ✗ | ✗(새로운 방식에서는 ✓로 바꿈) | mcs6 |

기존 방식에서 mcs2를 run7이라고 생각.
이제부터 새로운 mcs 방식을 run7_mcs1, run7_mcs2, run7_mcs3 이런식으로 명명.
즉, run_mcs2가 지금 학습되어있는 run7_mcs2.
모든 방식은 run7_mcs2를 따르지만 하나 다른건, phase1에서 resume으로 시작하지 않는것(epoch1부터 학습), 중요 - EMA도 절대 사용 금지

run7_mcs1은 run7_mcs2에서 gate만 off한 것.(phase1 resume제외하고, 다른 거 아무것도 바꾸면 안됨)

run7_mcs3은 gate 짜피 못쓰니까(matte가 없으니) gate 없이 진행.
run7_mcs2에서 입력을 sketch만 넣고 진행.

run7_5, run7_6은 기존 방식과 달리, GATE ON(hard gate)로 진행. 즉, GATE설정을 run7_2에서 바꾸면 안됨. 각각 Matte-CNN, Raw Matte를 끄는 건 그대로 진행. 단, 현재 매커니즘에 맞게 진행.

**중요** run7과 지시한 것 빼고 다른 매커니즘은 다 똑같아야 함.


## 논문에 표시된 각 실험에 따른 효과
논문 §4.2는 MatteCNN bias × RawMatte anchor의 2×2 factorial만 정식 ablation으로 두고, gate는 직교하는 별도 축(§4.8)으로 분리함.
수치는 Cross-identity Hair FID(§4.6, Table 1, leakage-free, 3 seed) / GT-bg(§4.7, Table 2) 기준.

1. gate on/off : ON이면 unbraid가 더 매끄럽고 스케치 색에 충실, OFF면 잔차가 강해 braid의 strand-crossing·knot boundary 표현이 좋음
2. Sketch-only (mcs3) : matte 신호가 전혀 없는 baseline. Hair FID **159.95로 최악**, 텍스처가 거칠고 strand flow가 덜 일관됨(§4.5, Fig.2). 단 ΔE2000은 2.1550으로 최고 — 스트로크 색을 가장 문자 그대로 따라가기 때문(fidelity vs realism 트레이드오프, §5). 반대로 GT-bg 프로토콜에서는 배경 누수 덕에 **오히려 최고로 보이는 ranking inversion**이 발생(§4.6, Fig.3) → 논문 contribution 3번의 근거
3. RawMatte (mcs5) : sketch latent + raw matte anchor 단독. Hair FID 159.95 → **148.73**. pixel unshuffle + 1×1 conv로 편집 영역의 명시적 기하 정보를 줌(§3.3.2)
4. MatteCNN (mcs6) : sketch latent + zero-init 학습형 region-aware bias 단독. Hair FID 159.95 → **148.10**. 3·4 어느 한쪽만 넣어도 ~11점 개선되고 둘 다 넣으면(Ours, mcs1) **140.11±3.10**으로 최고 → 논문은 두 신호가 역할 분담이 아니라 같은 목표로 latent를 미는 **additive**한 관계라고 규정(§5). GT-bg에서도 Ours가 PSNR 14.2263·Edge IoU 0.0728로 최고  

단, 논문에 나온 방식은 mcs1이 ours라고 정의. 현재는 mcs2가 ours라고 정의하며, mcs5, 6도 gate on


## 정량지표
Unbraid: 466장, Braid: 107장, 총 573장 사용  
CRG 1.5 + BLD full (step 20) + Pixel Matte-Blend + Feathering OFF (0), epoch20 기준  
mcs2(Ours)는 기존 run7 phase2 rawstart epoch20 결과와 동일하게 비교

### 구조·색상·화질·리얼리즘 (matte 내부)

| Run | 설정 | Sketch LPIPS ↓ | Sketch ΔE2000 ↓ | Edge IoU ↑ | LPIPS(GT) ↓ | ΔE2000(GT) ↓ | PSNR ↑ | Hair FID ↓ | KID_hair ↓ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mcs1 | Gate OFF | 0.5922 | 13.4934 | 0.0723 | 0.1586 | 2.8053 | 16.5425 | 37.8911 | 0.0055±0.0022 |
| mcs2 | Ours | 0.5711 | 12.6153 | 0.0710 | 0.1434 | 1.8139 | 16.9718 | **33.6777** | **0.0029±0.0017** |
| mcs3 | Sketch-only | 0.5980 | **12.7553** | **0.0726** | 0.1551 | **1.5192** | 16.4352 | 35.1382 | 0.0045±0.0019 |
| mcs5 | RawMatte + Gate | 0.5909 | 13.1417 | 0.0724 | 0.1472 | 1.7261 | 16.9445 | N/A | N/A |
| mcs6 | MatteCNN + Gate | **0.5628** | 13.1954 | 0.0705 | **0.1429** | 2.6782 | **16.9894** | 36.3541 | 0.0050±0.0022 |

### 경계밴드 B

| Run | 설정 | Boundary LPIPS ↓(legacy) | Bnd LPIPS k=8 ↓ | Bnd LPIPS k=16 ↓ | Boundary FID ↓ | Region IoU ↑ | Boundary IoU ↑ |
|---|---|---:|---:|---:|---:|---:|---:|
| mcs1 | Gate OFF | 0.0069 | 0.0059 | 0.0243 | 2.6583 | **0.1445** | **0.1012** |
| mcs2 | Ours | 0.0061 | 0.0053 | **0.0217** | 2.3738 | N/A | N/A |
| mcs3 | Sketch-only | **0.0058** | **0.0049** | 0.0223 | **2.1565** | 0.1436 | 0.0928 |
| mcs5 | RawMatte + Gate | 0.0061 | 0.0050 | **0.0217** | N/A | 0.1283 | 0.0850 |
| mcs6 | MatteCNN + Gate | 0.0066 | 0.0056 | 0.0225 | 2.5956 | 0.1263 | 0.0905 |

### 배경 보존 · identity · 방향 안정성

| Run | 설정 | PSNR_bg ↑ | LPIPS_bg ↓ | ArcFace cos ↑ | Full-portrait FID ↓ | GT 방향오차 ↓ | Seed 불일치 ↓ |
|---|---|---:|---:|---:|---:|---:|---:|
| mcs1 | Gate OFF | 44.6605 | 0.0010 | **0.9635** | 17.5989 | **14.14±4.79** | 8.82±3.31 |
| mcs2 | Ours | **45.1408** | **0.0009** | 0.9456 | **15.0565** | N/A | N/A |
| mcs3 | Sketch-only | 45.2603 | **0.0009** | 0.9367 | 16.6079 | 14.63±4.90 | 11.44±4.15 |
| mcs5 | RawMatte + Gate | 45.1981 | **0.0009** | 0.9486 | N/A | 14.39±4.78 | 10.19±3.60 |
| mcs6 | MatteCNN + Gate | 44.9339 | **0.0009** | 0.9367 | 15.9009 | **14.14±4.80** | **8.76±3.42** |

**요약**: 기존 Ours(mcs2)는 Hair FID/KID와 Full-portrait FID가 가장 좋고, mcs6은 Sketch LPIPS·LPIPS(GT)·PSNR(hair)와 seed 안정성이 좋게 나옴. mcs3는 색상 ΔE와 일부 경계 지표가 좋지만 seed 불일치가 가장 커서 안정성은 떨어짐. mcs1은 Region/Boundary IoU와 ArcFace는 높지만 리얼리즘 지표는 상대적으로 약함.  
mcs5는 이번 수집본에서 Hair FID/KID/Boundary FID/Full-portrait FID가 비어 있어 해당 항목은 N/A로 둠.


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


### 분석
1. mcs1 (Gate OFF) vs mcs2(Ours)

2. mcs3(Sketch-Only) vs mcs2(Ours)
논문에서만큼의 큰 차이는 없음


3. mcs5(RawMatte) vs mcs6 (MatteCNN) vs mcs2(Ours)
