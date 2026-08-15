
## 최상단 요약 (10줄 이내)

**지난 미팅 (2026-08-14)** — soft gate 실험 수행(run8이라 정의) / matte 중심 평가
- soft gate: 학습 중 iteration마다 gate `a∈{0,1}`를 Bernoulli(0.5)로 샘플링
- 평가: 573장(Unbraid 466, Braid 107), CRG 1.5 + BLD full + Pixel Matte-Blend + Feathering OFF

**합의 사항 → 상태**
- [완료] run8_phase1 40epoch, run8_phase2 epoch20 수동 정지
- [완료] run7/run8 epoch15·20·40 정량 비교 및 정성표 작성
- [진행 중] GT 방향오차·seed 불일치 측정(n=573, seed 1/2/3/42)

**이번 결과 / 막힌 것 / 다음**
- 결과: run8_ep20은 run7_ep20 대비 PSNR 16.97→17.21, PSNR_bg 45.14→45.37로 상승했지만 Hair FID 33.68→35.67, KID_hair 0.0029→0.0048로 하락
- 막힌 것: gate ON/OFF 차이는 논문 Figure 4만큼 뚜렷하지 않음

## 학습 조건
### run7 대비 config diff

#### phase1
`configs/run7_phase1.yaml` vs `configs/run8_phase1.yaml` — 실질 변경 4개:

| 블록 | 키 | run7_phase1 | run8_phase1 | 사유 |
|---|---|---|---|---|
| training | gate_mode | (키 없음, 기본 fixed) | soft | 🆕 iteration마다 a∈{0,1} Bernoulli(0.5) |
| training | gate_dropout_p | (키 없음) | 0.5 | 🆕 |
| training | midtrain_eval | (키 없음, 기본 true) | false | 🆕 in-loop 평가 의미 없이 GPU만 잡아먹어 전면 off -> 남는 GPU로 정성평가 지표 돌림 |
| checkpointing | output_dir | checkpoints/run7_phase1/ | checkpoints/run8_phase1/ | 덮어쓰기 방지 |

#### phase2
`configs/run7_phase2_rawstart.yaml`(실제 완주본) vs `configs/run8_phase2.yaml` — 실질 변경 5개:

| 블록 | 키 | run7_phase2_rawstart | run8_phase2 | 사유 |
|---|---|---|---|---|
| training | gate_mode | (키 없음) | soft | 🆕 phase2도 유지 |
| training | gate_dropout_p | (키 없음) | 0.5 | 🆕 |
| training | midtrain_eval | (키 없음) | false | 🆕 |
| training | resume_from | checkpoints/run7_phase1/epoch_40.pth | checkpoints/run8_phase1/epoch_40.pth | phase1 산출물 교체 |
| checkpointing | output_dir | checkpoints/run7_phase2_rawstart/ | checkpoints/run8_phase2/ | 덮어쓰기 방지 |

run8_phase2는 epoch20에서 수동 정지(run7에서 epoch20에서 가장 좋은 성능 나옴)


## 논문에 표시된 GATE ON / OFF에 따른 효과
<img src="../outputs/0814/gate_on_off_paper_figure.png" width="720">

**정성적 효과(§4.8, Figure 4)**:
- **unbraid**: gate ON이 더 smoother, more seamless, more faithful to the sketched colors 
- **braid**: gate OFF가 residual을 더 강하게 남겨 가닥이 겹치는 부분(strand-crossing)과 매듭 경계(knot boundary)를 더 잘 표현

**정량적 효과(§4.8, §5)**: 게이팅은 Hair FID나 색 거리(color distance, ΔE2000)를 **개선하지
않는다**("Gating does not improve Hair FID or color distance") — 즉 논문 자체 지표로는 ON/OFF
사이에 일관된 우열이 없고, 선택은 순전히 정성적(스타일별 트레이드오프) 판단이다.


## 정량지표
Unbraid: 466장, Braid: 107장, 총 573장 사용
CRG 1.5 + BLD full (step 20) + Pixel Matte-Blend + Feathering OFF (0), gate_alpha 1.0(GATE ON)으로 비교
정량지표 추가됨.
Sketch LPIPS ↓, Edge IoU ↑, Hair FID ↓, LPIPS(GT) ↓, Boundary FID ↓, Boundary LPIPS ↓, Full-portrait FID ↓는 이전 방식(논문 방식) 그대로 사용. 
GT 방향오차· seed 불일치도 run5부터 써온 방식 그대로 사용

kid_hair, bnd_lpips_k8/k16, psnr_bg/lpips_bg, arcface 신설. 

### 구조·색상·화질·리얼리즘 (matte 내부)

| Run | Epoch | Sketch LPIPS ↓ | Sketch ΔE2000 ↓ | Edge IoU ↑ | LPIPS(GT) ↓ | ΔE2000(GT) ↓ | PSNR ↑ | Hair FID ↓ | KID_hair ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| run7 | 15 | 0.5774 | 13.2912 | 0.0714 | 0.1475 | 2.0616 | 16.8048 | 35.4634 | 0.0048±0.0021 |
| run7 | **20** | 0.5711 | 12.6153 | 0.0710 | 0.1434 | 1.8139 | 16.9718 | 33.6777 | 0.0029±0.0017 |
| run7 | 40 | 0.5767 | 13.0633 | 0.0716 | 0.1457 | 1.9940 | 17.0065 | 33.8825 | 0.0033±0.0017 |
| run8 | 15 | 0.5700 | 13.0917 | 0.0712 | 0.1420 | 2.0530 | 17.1559 | 35.3270 | 0.0045±0.0020 |
| run8 | **20** | 0.5714 | 13.3046 | 0.0710 | 0.1428 | 1.9434 | 17.2134 | 35.6650 | 0.0048±0.0020 |

### 경계밴드 B

| Run | Epoch | Boundary LPIPS ↓(legacy) | Bnd LPIPS k=8 ↓ | Bnd LPIPS k=16 ↓ | Boundary FID ↓ |
|---|---:|---:|---:|---:|---:|
| run7 | 15 | 0.0063 | 0.0056 | 0.0224 | 2.4568 |
| run7 | **20** | 0.0061 | 0.0053 | 0.0217 | 2.3738 |
| run7 | 40 | 0.0064 | 0.0055 | 0.0221 | 2.5017 |
| run8 | 15 | 0.0060 | 0.0052 | 0.0214 | 2.3712 |
| run8 | **20** | 0.0060 | 0.0053 | 0.0214 | 2.3988 |


### 배경 보존(matte 외부) · identity(얼굴) · 전역 조화

| Run | Epoch | PSNR_bg ↑ | LPIPS_bg ↓ | ArcFace cos ↑ (유효 n, braid/unbraid) | Full-portrait FID ↓ |
|---|---:|---:|---:|---:|---:|
| run7 | 15 | 45.0009 | 0.0009 | 0.9464 (17/107, 428/466) | 15.3320 |
| run7 | **20** | 45.1408 | 0.0009 | 0.9456 (18/107, 428/466) | 15.0565 |
| run7 | 40 | 45.0298 | 0.0009 | 0.9488 (18/107, 427/466) | 15.3088 |
| run8 | 15 | 45.3731 | 0.0009 | 0.9509 (18/107, 426/466) | 14.8808 |
| run8 | **20** | 45.3663 | 0.0009 | 0.9478 (19/107, 427/466) | 15.2123 |

**run7 20, run8 20 비교**:   
run8_ep20이 run7_ep20 대비 우세한 지표 — PSNR(hair) 17.21>16.97, PSNR_bg 45.37>45.14, ArcFace 0.9478≈0.9456(거의 동일), Full-portrait FID 15.21<15.06(근소 열세).   
run7_ep20이 우세한 지표 — Hair FID 33.68<35.67, KID_hair 0.0029<0.0048, LPIPS(GT) 0.1434<0.1428(거의 동일), Sketch ΔE2000 12.62<13.30, 경계밴드(Bnd LPIPS k8/k16, Boundary FID) 전부.   
즉 **리얼리즘·색상·경계 지표는 run7이, 화질·배경보존은 run8이 근소 우세** — 어느 한쪽이 전 지표를 이기지 않는다.


🔴 **진행 중**: run8_phase2의 GT 방향오차·seed 불일치(run5부터 써온 structure-tensor 방식, 이 리포트 작성 시점 기준 측정 중 — CRG1.5+BLD+Pixel Matte-Blend+Feather0+gate1.0). 완료되는대로 추가 예정


## 정성지표
### phase1
#### gt sketch

| image | sketch | epoch5 | epoch10 | epoch15 | epoch20 | epoch25 | epoch30 | epoch35 | epoch40 |
|---|---|---|---|---|---|---|---|---|---|
| CM_1007 | <img src="../data/unbraid_new/sketch/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/gt/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/gt/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/gt/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/gt/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/gt/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/gt/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/gt/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/gt/gate1/CM_1007.png" width="80"> |
| CM_1027 | <img src="../data/unbraid_new/sketch/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/gt/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/gt/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/gt/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/gt/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/gt/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/gt/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/gt/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/gt/gate1/CM_1027.png" width="80"> |
| CM_1033 | <img src="../outputs/figure/sketch_gt/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/gt/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/gt/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/gt/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/gt/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/gt/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/gt/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/gt/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/gt/gate1/CM_1033.png" width="80"> |
| CM_1067 | <img src="../outputs/figure/sketch_gt/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/gt/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/gt/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/gt/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/gt/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/gt/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/gt/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/gt/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/gt/gate1/CM_1067.png" width="80"> |
| CM_1068 | <img src="../outputs/figure/sketch_gt/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/gt/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/gt/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/gt/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/gt/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/gt/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/gt/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/gt/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/gt/gate1/CM_1068.png" width="80"> |
| CM_1084 | <img src="../outputs/figure/sketch_gt/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/gt/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/gt/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/gt/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/gt/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/gt/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/gt/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/gt/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/gt/gate1/CM_1084.png" width="80"> |
| CM_1172 | <img src="../outputs/figure/sketch_gt/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/gt/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/gt/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/gt/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/gt/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/gt/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/gt/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/gt/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/gt/gate1/CM_1172.png" width="80"> |

#### Colorful sketch
| image | sketch | epoch5 | epoch10 | epoch15 | epoch20 | epoch25 | epoch30 | epoch35 | epoch40 |
|---|---|---|---|---|---|---|---|---|---|
| CM_1007 | <img src="../data/unbraid_new/sketch/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/color/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/color/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/color/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/color/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/color/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/color/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/color/gate1/CM_1007.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/color/gate1/CM_1007.png" width="80"> |
| CM_1027 | <img src="../data/unbraid_new/sketch/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/color/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/color/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/color/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/color/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/color/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/color/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/color/gate1/CM_1027.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/color/gate1/CM_1027.png" width="80"> |
| CM_1033 | <img src="../outputs/figure/sketch_color/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/color/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/color/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/color/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/color/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/color/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/color/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/color/gate1/CM_1033.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/color/gate1/CM_1033.png" width="80"> |
| CM_1067 | <img src="../outputs/figure/sketch_color/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/color/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/color/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/color/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/color/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/color/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/color/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/color/gate1/CM_1067.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/color/gate1/CM_1067.png" width="80"> |
| CM_1068 | <img src="../outputs/figure/sketch_color/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/color/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/color/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/color/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/color/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/color/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/color/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/color/gate1/CM_1068.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/color/gate1/CM_1068.png" width="80"> |
| CM_1084 | <img src="../outputs/figure/sketch_color/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/color/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/color/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/color/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/color/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/color/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/color/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/color/gate1/CM_1084.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/color/gate1/CM_1084.png" width="80"> |
| CM_1172 | <img src="../outputs/figure/sketch_color/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch5/color/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch10/color/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch15/color/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch20/color/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch25/color/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch30/color/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch35/color/gate1/CM_1172.png" width="80"> | <img src="../outputs/0814/run8_phase1/epoch40/color/gate1/CM_1172.png" width="80"> |

### phase2
#### gt sketch

| image | sketch | epoch5 | epoch10 | epoch15 | epoch20 |
|---|---|---|---|---|---|
| CM_1007 | <img src="../data/unbraid_new/sketch/CM_1007.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/gt/gate1/CM_1007.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/gt/gate1/CM_1007.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/gt/gate1/CM_1007.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/CM_1007.png" width="105"> |
| CM_1027 | <img src="../data/unbraid_new/sketch/CM_1027.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/gt/gate1/CM_1027.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/gt/gate1/CM_1027.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/gt/gate1/CM_1027.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/CM_1027.png" width="105"> |
| CM_1033 | <img src="../outputs/figure/sketch_gt/CM_1033.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/gt/gate1/CM_1033.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/gt/gate1/CM_1033.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/gt/gate1/CM_1033.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/CM_1033.png" width="105"> |
| CM_1067 | <img src="../outputs/figure/sketch_gt/CM_1067.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/gt/gate1/CM_1067.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/gt/gate1/CM_1067.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/gt/gate1/CM_1067.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/CM_1067.png" width="105"> |
| CM_1068 | <img src="../outputs/figure/sketch_gt/CM_1068.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/gt/gate1/CM_1068.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/gt/gate1/CM_1068.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/gt/gate1/CM_1068.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/CM_1068.png" width="105"> |
| CM_1084 | <img src="../outputs/figure/sketch_gt/CM_1084.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/gt/gate1/CM_1084.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/gt/gate1/CM_1084.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/gt/gate1/CM_1084.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/CM_1084.png" width="105"> |
| CM_1172 | <img src="../outputs/figure/sketch_gt/CM_1172.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/gt/gate1/CM_1172.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/gt/gate1/CM_1172.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/gt/gate1/CM_1172.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/CM_1172.png" width="105"> |
| braid_2548 | <img src="../data/unbraid_new/sketch/braid_2548.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/gt/gate1/braid_2548.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/gt/gate1/braid_2548.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/gt/gate1/braid_2548.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/braid_2548.png" width="105"> |
| braid_4156 | <img src="../data/unbraid_new/sketch/braid_4156.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/gt/gate1/braid_4156.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/gt/gate1/braid_4156.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/gt/gate1/braid_4156.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/braid_4156.png" width="105"> |

#### Colorful sketch

| image | sketch | epoch5 | epoch10 | epoch15 | epoch20 |
|---|---|---|---|---|---|
| CM_1007 | <img src="../data/unbraid_new/sketch/CM_1007.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/color/gate1/CM_1007.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/color/gate1/CM_1007.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/color/gate1/CM_1007.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/color/gate1/CM_1007.png" width="105"> |
| CM_1027 | <img src="../data/unbraid_new/sketch/CM_1027.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/color/gate1/CM_1027.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/color/gate1/CM_1027.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/color/gate1/CM_1027.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/color/gate1/CM_1027.png" width="105"> |
| CM_1033 | <img src="../outputs/figure/sketch_color/CM_1033.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/color/gate1/CM_1033.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/color/gate1/CM_1033.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/color/gate1/CM_1033.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/color/gate1/CM_1033.png" width="105"> |
| CM_1067 | <img src="../outputs/figure/sketch_color/CM_1067.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/color/gate1/CM_1067.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/color/gate1/CM_1067.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/color/gate1/CM_1067.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/color/gate1/CM_1067.png" width="105"> |
| CM_1068 | <img src="../outputs/figure/sketch_color/CM_1068.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/color/gate1/CM_1068.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/color/gate1/CM_1068.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/color/gate1/CM_1068.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/color/gate1/CM_1068.png" width="105"> |
| CM_1084 | <img src="../outputs/figure/sketch_color/CM_1084.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/color/gate1/CM_1084.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/color/gate1/CM_1084.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/color/gate1/CM_1084.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/color/gate1/CM_1084.png" width="105"> |
| CM_1172 | <img src="../outputs/figure/sketch_color/CM_1172.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/color/gate1/CM_1172.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/color/gate1/CM_1172.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/color/gate1/CM_1172.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/color/gate1/CM_1172.png" width="105"> |
| braid_2548 | <img src="../data/unbraid_new/sketch/braid_2548.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/color/gate1/braid_2548.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/color/gate1/braid_2548.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/color/gate1/braid_2548.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/color/gate1/braid_2548.png" width="105"> |
| braid_4156 | <img src="../data/unbraid_new/sketch/braid_4156.png" width="90"> | <img src="../outputs/0814/run8_phase2/epoch5/color/gate1/braid_4156.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch10/color/gate1/braid_4156.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch15/color/gate1/braid_4156.png" width="105"> | <img src="../outputs/0814/run8_phase2/epoch20/color/gate1/braid_4156.png" width="105"> |

### Gate ON vs Gate OFF
phase2 epoch20에서 gate on / off 비교  
(CRG 1.5 + BLD full (step 20) + Pixel Matte-Blend + Feathering OFF (0))  
육안상 논문 figure만큼 뚜렷한 차이 없음

| image | Gate OFF | Gate ON |
|---|---|---|
| CM_1172 (color) | <img src="../outputs/0814/run8_phase2/epoch20/color/gate0/CM_1172.png" width="130"> | <img src="../outputs/0814/run8_phase2/epoch20/color/gate1/CM_1172.png" width="130"> |
| CM_1082 (GT) | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate0/CM_1082.png" width="130"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/CM_1082.png" width="130"> |
| braid_2548 (GT) | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate0/braid_2548.png" width="130"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/braid_2548.png" width="130"> |
| CM_1084 (GT) | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate0/CM_1084.png" width="130"> | <img src="../outputs/0814/run8_phase2/epoch20/gt/gate1/CM_1084.png" width="130"> |
| CM_1067 (color) | <img src="../outputs/0814/run8_phase2/epoch20/color/gate0/CM_1067.png" width="130"> | <img src="../outputs/0814/run8_phase2/epoch20/color/gate1/CM_1067.png" width="130"> |


## (추가)EMA 관련 에러(run7에서 발생했었음)
EMA : EMA는 매 step의 raw weight를 바로 쓰는 게 아니라 `ema = decay * old_ema + (1-decay) * current_raw`로 누적한 지수이동평균 가중치임. 원래는 mini-batch마다 gradient가 달라 raw weight가 step마다 조금씩 흔들릴 수 있어서, 여러 step의 weight를 평균낸 더 안정적인 validation용 가중치를 쓰기 위해 checkpoint 안에 `controlnet` raw weight와 별도로 `ema.shadow`를 저장했음.  
근데 **phase1에서 phase2로 넘어갈 때 phase1의 EMA 가중치로 덮어쓰여져서 넘어감** => EMA는 충분한 step으로 학습하지 않으면 현재 학습된 weight를 따라잡지 못하고 초기 weight의 영향이 크게 남음. 특히 zero-init인 condition residual 레이어는 EMA가 raw를 매우 느리게 따라가서 `controlnet_blocks`의 ‖ema‖/‖raw‖가 0.396x 수준으로 작았음. 또한, raw weight가 아니라 EMA 가중치에서 학습을 이어간 건 스케치 조건 신호가 약 40% 세기로 깎여 시작한 것과 다름 없음. 때문에 phase1에서는 색 뚜렷하게 나타났는데 phase2에서 사실상 색 초기화 일어남 => **수정 후, 현재 학습/추론 기준에서는 EMA 관련 코드가 필요없어 관련 코드 폐기 후 실수 재발 방지**

run7 phase2 epoch5에 대해 EMA로 덮어쓰여져 학습한 모델 vs raw weight로 학습한 모델(color sketch, seed42)

| image | run7 phase2 EMA 시작 | run7 phase2 raw 시작 |
|---|---|---|
| CM_1067 | <img src="../outputs/0812/run7_phase2/color/42/epoch_5/CM_1067.png" width="150"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1067.png" width="150"> |
| CM_1007 | <img src="../outputs/0812/run7_phase2/color/42/epoch_5/CM_1007.png" width="150"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1007.png" width="150"> |
| CM_1172 | <img src="../outputs/0812/run7_phase2/color/42/epoch_5/CM_1172.png" width="150"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1172.png" width="150"> |
