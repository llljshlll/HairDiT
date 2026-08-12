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

> 방법론은 `[DIGLAB][0810][장서현]run5_1_quant_eval.md` §3.0과 동일(`infer_custom.py
> --recolor_from_gt`, `orientation_metric.py` structure tensor sigma_i=3/erode_px=6,
> `eval_metrics.py`의 compute_delta_e_hue/hair_masked_lpips). seed `{1,2,3,42}`, 20 step.
> epoch5/10/15는 이번 정량 추론 대상에서 제외됨(quant50 pool이 epoch20부터 추론) —
> run7_phase1의 epoch5/10/15는 resume 이전 run5_1과 가중치가 동일하므로 그
> 리포트(§3.1/§3.2, epoch15 n=50: GT err 15.29° / coh 0.779 / seed_dis 13.15±4.58 /
> dE_unbraid 5.2417 / lpips_unbraid 0.2497)로 대체 참고 가능하나, **거기 쓰인 50장 pool이
> 이번 `_pool50`과 동일한 이미지 집합인지 확인되지 않아 직접 비교는 보류**.

#### n=50 (quant50 pool, `dataset/unbraid` GT, `python scripts/eval/quant50_run7.py --epochs 20 25 30 35 40`)

| epoch | GT 오차 평균 [deg] | coherence | seed 불일치 [deg] | dE_unbraid | lpips_unbraid |
|---:|---:|---:|---:|---:|---:|
| 20 | 16.03 | 0.767 | 14.54±4.70 | 3.6836 | 0.2345 |
| 25 | 15.62 | 0.753 | 13.75±4.86 | 3.4561 | 0.2349 |
| 30 | 14.99 | 0.763 | 12.40±4.27 | 2.6363 | 0.2240 |
| 35 | 14.81 | 0.754 | 11.73±4.11 | 2.4092 | 0.2217 |
| **40** | **14.74** | 0.756 | **11.48±4.11** | **2.2868** | **0.2199** |

방향 지표(GT 오차·seed 불일치)는 epoch20→40 단조 감소, coherence는 뚜렷한 추세 없이 좁은
범위(0.753~0.767)에서 진동. 색/구조 지표(dE_unbraid·lpips_unbraid)도 방향 지표와 같은
방향(epoch가 늘수록 개선)으로 움직여 — `run5_1_quant_eval.md` §3.3에서 관찰된 "방향 vs
색/구조 지표 상충"이 이번엔 **재현되지 않음**.

**선정 기준(교수님 지시 ④) 적용**: 방향 지표 기준으로 epoch40이 최선이고 색/구조 지표도
epoch40에서 최선이라 상충 없이 **epoch40이 방향 지표 최적점**. 다만 이번 평가는 epoch20~40
구간만 다뤄 epoch5~15 구간과의 비교는 위 주석의 한계 하에서만 가능.

**epoch35 vs epoch40 — 정성지표와 동일하게 정량지표도 유의미한 차이 없음.**
epoch35→40 변화폭이 seed 불일치의 표준편차(±4.11°)보다 훨씬 작음(GT 오차 −0.07°(−0.5%),
seed 불일치 −0.25°(−2.1%), dE −0.12(−5%), lpips −0.0018(−0.8%)) — 노이즈 범위 안.
epoch30→35 구간의 개선폭(GT 오차 −0.18°, seed 불일치 −0.67°, dE −0.23)이 35→40보다
뚜렷이 컸던 것과 비교하면 개선이 이미 epoch35 부근에서 수렴한 것으로 판단됨. →
**정성·정량 모두 epoch35=epoch40이라, phase2는 epoch35에서 진행해도 무방.**

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

> epoch5/10/15는 당시 recolor_sketch(자연색) 조건만 추론되어 colorful sketch 결과가 없음 — epoch20부터 시작.

| 파일명 | img | sketch | epoch20 | epoch25 | epoch30 | epoch35 | epoch40 |
|---|---|---|---|---|---|---|---|
| CM_1007 | <img src="../dataset/test/img/CM_1007.png" width="70"> | <img src="../dataset/test/sketch/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1007.png" width="70"> |
| CM_1027 | <img src="../dataset/test/img/CM_1027.png" width="70"> | <img src="../dataset/test/sketch/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1027.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1027.png" width="70"> |
| CM_1033 | <img src="../dataset/test/img/CM_1033.png" width="70"> | <img src="../dataset/test/sketch/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1033.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1033.png" width="70"> |
| CM_1067 | <img src="../dataset/test/img/CM_1067.png" width="70"> | <img src="../dataset/test/sketch/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1067.png" width="70"> |
| CM_1068 | <img src="../dataset/test/img/CM_1068.png" width="70"> | <img src="../dataset/test/sketch/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1068.png" width="70"> |
| CM_1082 | <img src="../dataset/test/img/CM_1082.png" width="70"> | <img src="../dataset/test/sketch/CM_1082.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1082.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1082.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1082.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1082.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1082.png" width="70"> |
| CM_1084 | <img src="../dataset/test/img/CM_1084.png" width="70"> | <img src="../dataset/test/sketch/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1084.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1084.png" width="70"> |
| CM_1172 | <img src="../dataset/test/img/CM_1172.png" width="70"> | <img src="../dataset/test/sketch/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch20/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch25/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch30/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch35/CM_1172.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1172.png" width="70"> |
