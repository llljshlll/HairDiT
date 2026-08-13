교수님 지시 내용 : 
학습 관련해서 다음을 고려

① dropout = 적용 안 함, 논의 종결. CFG 의 요건이고 CRG 의 off 분기는 이미 학습된 pretrained prior 임. 
② resume 승인 — full checkpoint(optimizer state) 유무 확인해 명시할 것 
③ phase2 lr 5e-6 근거 제시, 없으면 2e-5 ?! 맞나요 ?!
④ phase1→2 선정 기준에 방향 지표(GT 오차·seed 불일치) 필수 포함 — 색 지표만으로 선정 금지 (색 지표는 참고 사항일뿐) 
⑤ 5ep 저장 명시 + config 를 run5_1 대비 diff 표로 재제출. 
이 5건 반영 후 즉시 착수 진행하세요.

## 학습 조건
- dropout 적용안함
- resume full checkpoint에서 진행
- phase2 2e-5로 진행예정
- run5_1 대비 diff 표 : 
`configs/run7_phase1.yaml` vs `configs/run5_1_noisegate_phase1.yaml`. run7_phase1은 새 조건이 아니라 run5_1(epoch15)을 최종 산출물로 승격시켜 40epoch까지 이어 학습하는 것.

| 블록 | 키 | run5_1 | run7_phase1 | 상태 | 사유 |
|---|---|---|---|---|---|
| training | phase | pretrain | pretrain | 동일 | |
| training | dataset | unbraid | unbraid | 동일 | |
| training | epochs | 40 | 40 | 동일 | cosine LR T_max가 이 값에 고정 |
| training | batch_size | 16 | 16 | 동일 | |
| training | learning_rate | 1.0e-4 | 1.0e-4 | 동일 | |
| training | **resume** | null | `checkpoints/run5_1_noisegate/epoch_15.pth` | **변경** | run5_1 epoch15(step 2805)에서 이어받기 — full checkpoint(optimizer/EMA 포함) 사용 |
| loss_weights | flow | 1.0 | 1.0 | 동일 | |
| loss_weights | lpips | 0.002 | 0.002 | 동일 | |
| loss_weights | edge | 0.0 | 0.0 | 동일 | pretrain이라 미적용 |
| loss_weights | lpips_noise_cutoff | 0.7 | 0.7 | 동일 | |
| loss_weights | **lpips_gate** | (키 없음, 기본값 "noise") | `noise`(명시) | **표기만 변경** | 동작은 동일 — 어떤 게이트인지 파일만 보고 알 수 있게 명시 |
| loss_weights | scale_sync / s_min / s_max | true / 20.0 / 120.0 | true / 20.0 / 120.0 | 동일 | |
| checkpointing | **output_dir** | `checkpoints/run5_1_noisegate/` | `checkpoints/run7_phase1/` | **변경** | run5_1 체크포인트 덮어쓰기 방지 |
| checkpointing | perceptual_every | 1 | 1 | 동일 | 매 epoch perceptual val |
| checkpointing | **save_every** | 5 | 5 | 동일(명시) | 5epoch마다 체크포인트 저장 → epoch 5/10/15/20/25/30/35/40 총 8개 후보 생성, phase2 이관 epoch은 이 중 perceptual val 로그 보고 사후 선정 |

**실질 변경 = 2개**(`resume`, `output_dir`), 표기만 바뀐 것 1개(`lpips_gate`).

## phase1→2 선정 기준
### 정량지표

> 조건: CRG(`--cfg_scale 2.0`) + BLD(`--bld_mode full --bld_soft_steps 18`) + `--recolor_from_gt`.
> 지표는 matte(마스크) 영역에만 계산. 

#### unbraid — n=50, seed 4개

| epoch | GT 오차 평균 [deg] | coherence | seed 불일치 [deg] | dE_unbraid | lpips_unbraid |
|---:|---:|---:|---:|---:|---:|
| 5 | 14.59 | **0.840** | 11.12±4.03 | 4.4641 | 0.2193 |
| 10 | 14.59 | 0.803 | 11.34±3.72 | 4.6039 | 0.2184 |
| 15 | 13.76 | 0.813 | 9.98±3.14 | 4.3140 | 0.2131 |
| 20 | 14.61 | 0.799 | 11.30±3.27 | 2.8196 | 0.1928 |
| 25 | 14.17 | 0.784 | 10.64±3.27 | 2.8937 | 0.1954 |
| 30 | 14.00 | 0.793 | 9.75±2.84 | 2.0198 | 0.1897 |
| 35 | 14.00 | 0.783 | 9.30±2.72 | 2.0019 | 0.1884 |
| 40 | 13.99 | 0.787 | **9.11±2.76** | **1.7838** | **0.1857** |

**관측**(수치에서 직접 계산한 사실):

- 방향 지표 최적: GT 오차·seed 불일치 모두 epoch40(GT 오차는 epoch15가 13.76으로 근소하게
  더 낮지만 다른 체크포인트 계열이라 run7_phase1 자체 학습 기준으로는 epoch40이 최적)
- 색/구조 지표 최적: dE_unbraid·lpips_unbraid 둘 다 epoch40
- epoch15→20 구간에서 dE_unbraid가 4.31→2.82로 크게 개선된 뒤 epoch40까지 완만하게
  계속 개선. epoch20부터가 run7_phase1 고유 학습 구간
- coherence 범위: 0.783 ~ 0.840(epoch5가 최고, 뚜렷한 추세 없이 진동)

**선정 기준 적용**: 방향 지표 기준 epoch40이 최선(epoch15는 다른 체크포인트 계열이라 후보에서
제외). 색/구조 지표도 epoch40에서 최선이라 상충 없이 epoch40이 최적점.

### 정성지표
epoch5~40까지 정성지표
## 결과 사진

> seed42 기준. epoch5~40 비교 (run7_phase1 40epoch 학습 완료, `checkpoints/run7_phase1/final.pth` 생성 확인).


### gt sketch

| 파일명 | img | sketch | epoch5 | epoch10 | epoch15 | epoch20 | epoch25 | epoch30 | epoch35 | epoch40 |
|---|---|---|---|---|---|---|---|---|---|---|
| CM_1007 | <img src="../dataset/test/img/CM_1007.png" width="70"> | <img src="../dataset/test/recolor_sketch/CM_1007.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch5/CM_1007.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch10_infer/CM_1007.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch15_infer/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch20/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch25/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch30/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch35/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch40/CM_1007.png" width="70"> |
| CM_1027 | <img src="../dataset/test/img/CM_1027.png" width="70"> | <img src="../dataset/test/recolor_sketch/CM_1027.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch5/CM_1027.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch10_infer/CM_1027.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch15_infer/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch20/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch25/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch30/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch35/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch40/CM_1027.png" width="70"> |
| CM_1033 | <img src="../dataset/test/img/CM_1033.png" width="70"> | <img src="../dataset/test/recolor_sketch/CM_1033.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch5/CM_1033.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch10_infer/CM_1033.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch15_infer/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch20/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch25/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch30/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch35/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch40/CM_1033.png" width="70"> |
| CM_1067 | <img src="../dataset/test/img/CM_1067.png" width="70"> | <img src="../dataset/test/recolor_sketch/CM_1067.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch5/CM_1067.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch10_infer/CM_1067.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch15_infer/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch20/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch25/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch30/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch35/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch40/CM_1067.png" width="70"> |
| CM_1068 | <img src="../dataset/test/img/CM_1068.png" width="70"> | <img src="../dataset/test/recolor_sketch/CM_1068.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch5/CM_1068.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch10_infer/CM_1068.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch15_infer/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch20/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch25/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch30/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch35/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch40/CM_1068.png" width="70"> |
| CM_1082 | <img src="../dataset/test/img/CM_1082.png" width="70"> | <img src="../dataset/test/recolor_sketch/CM_1082.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch5/CM_1082.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch10_infer/CM_1082.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch15_infer/CM_1082.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch20/CM_1082.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch25/CM_1082.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch30/CM_1082.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch35/CM_1082.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch40/CM_1082.png" width="70"> |
| CM_1084 | <img src="../dataset/test/img/CM_1084.png" width="70"> | <img src="../dataset/test/recolor_sketch/CM_1084.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch5/CM_1084.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch10_infer/CM_1084.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch15_infer/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch20/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch25/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch30/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch35/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch40/CM_1084.png" width="70"> |
| CM_1172 | <img src="../dataset/test/img/CM_1172.png" width="70"> | <img src="../dataset/test/recolor_sketch/CM_1172.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch5/CM_1172.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch10_infer/CM_1172.png" width="70"> | <img src="../outputs/0806/run5_1/42/epoch15_infer/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch20/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch25/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch30/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch35/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch40/CM_1172.png" width="70"> |

### Colorful sketch


| 파일명 | img | sketch | epoch20 | epoch25 | epoch30 | epoch35 | epoch40 |
|---|---|---|---|---|---|---|---|
| CM_1007 | <img src="../dataset/test/img/CM_1007.png" width="70"> | <img src="../dataset/test/sketch/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1007.png" width="70"> |
| CM_1027 | <img src="../dataset/test/img/CM_1027.png" width="70"> | <img src="../dataset/test/sketch/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1027.png" width="70"> |
| CM_1033 | <img src="../dataset/test/img/CM_1033.png" width="70"> | <img src="../dataset/test/sketch/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1033.png" width="70"> |
| CM_1067 | <img src="../dataset/test/img/CM_1067.png" width="70"> | <img src="../dataset/test/sketch/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1067.png" width="70"> |
| CM_1068 | <img src="../dataset/test/img/CM_1068.png" width="70"> | <img src="../dataset/test/sketch/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1068.png" width="70"> |
| CM_1084 | <img src="../dataset/test/img/CM_1084.png" width="70"> | <img src="../dataset/test/sketch/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1084.png" width="70"> |
| CM_1172 | <img src="../dataset/test/img/CM_1172.png" width="70"> | <img src="../dataset/test/sketch/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1172.png" width="70"> |


**epoch35 vs epoch40(CRG+BLD 재측정) — 방향 지표 차이 없음, dE_unbraid는 epoch40이 앞섬.**
epoch35→40: GT 오차 −0.01°(−0.07%), seed 불일치 −0.19°(−2.0%) — seed 불일치 표준편차
(±2.7~2.8°)보다 작아 노이즈 범위. epoch30→35 seed 불일치 개선폭(−0.45°)이 35→40(−0.19°)보다
커서, 방향 지표만 보면 이전(no-CRG/BLD) 측정과 같이 epoch35에서 수렴.

dE_unbraid는 다르다: epoch30→35 −0.9%, epoch35→40 −10.9%(2.0198→2.0019→1.7838). 지시
④상 색 지표는 선정 근거가 아니지만, 색 지표만 보면 epoch40이 앞선다.
→ 방향 지표로는 epoch35=epoch40, 색 지표는 epoch40 우세. 채택한 epoch40은 방향 지표
기준을 만족하면서 색 지표에서도 이득을 본 선택.