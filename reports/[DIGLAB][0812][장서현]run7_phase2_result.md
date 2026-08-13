# run7_phase2 결과

## 최상단 요약 (10줄 이내)

**이전 결정 사항** — 지시 ②③④ (아래 "학습 조건" 표 각주)
- weights-only로 phase1→phase2 전환 (②)
- LR은 5e-6 아닌 2e-5 유지 (③)
- 채택 기준은 방향 지표(GT 오차·seed 불일치) 필수, 색 지표는 참고용 (④)

**합의 사항 → 상태**
- [완료] weights-only + LR 2e-5로 epoch 40까지 재학습
- [부분] braid 정성·정량 괴리 — 현상만 확인(§분석 2), 원인 미확인
- [미착수] 채택 epoch 최종 확정

**이번 결과 / 막힌 것 / 다음**
- 결과: GT 오차 unbraid 14.13°(epoch5, 최저)~14.19°(epoch40), braid 21.80°→20.45°(epoch5→40, CRG+BLD 적용). mcs2 대비 run7_phase2는 sketch에 없는 색을 만들어 내는 경향이 약해짐(§분석 3)
- 막힌 것: `braid_2625`/`braid_2562_1` 등 일부 이미지·seed에서 정성적으로 epoch15 이후 품질 저하되는데 정량지표는 epoch25~35까지 계속 개선 — 원인 미확인 🔴
- 다음: 채택 epoch 확정(방향 지표 기준 epoch40)

## 학습 조건

`configs/run7_phase2.yaml` vs `configs/run7_phase1.yaml`

| 블록 | 키 | run7_phase1 | run7_phase2 | 상태 | 사유 |
|---|---|---|---|---|---|
| training | phase | pretrain | **finetune** | 변경 | edge loss 활성화 |
| training | dataset | unbraid | **replay** | 변경 | unbraid 3000 + braid 1000, 8:8 stratified |
| training | epochs | 40 | 40 | 동일 | |
| training | batch_size | 16 | 16 | 동일 | batch_sampler(8+8)가 실질 결정 |
| training | learning_rate | 1.0e-4 | **2.0e-5** | 변경 | mcs2 parity(2e-5) |
| training | resume | `run5_1_noisegate/epoch_15.pth` | null | 변경 | phase가 바뀔 때는 weights-only 사용 |
| training | resume_from | — | `run7_phase1/epoch_40.pth` | 신규 | **weights-only**.|
| loss_weights | flow | 1.0 | 1.0 | 동일 | |
| loss_weights | lpips | 0.002 | 0.002 | 동일 | |
| loss_weights | edge | 0.0 | **0.05** | 변경 | mcs2 parity 유지 |
| loss_weights | scale_sync / s_min / s_max | true / 20 / 120 | true / 20 / 120 | 동일 | |
| checkpointing | save_every | 5 | 5 | 동일 | epoch 5/10/…/40 + final |
| checkpointing | perceptual_every | 1 | 1 | 동일 | |

> **LR 5e-6 vs 2e-5 ( 지시 ③)**: 2e-5로 실행

> **resume 방식 (지시 ②)**: phase1에서 phase2로 넘어갈 때는 ControlNet weights-only checkpoint만 불러오고,
> optimizer와 LR scheduler 상태는 새로 시작했다.
>
> phase1 종료 checkpoint을 full resume하면 phase1에서 쓰던 LR scheduler(CosineAnnealingLR)
> 상태까지 복원되는데, 이 스케줄러는 주기함수라서 phase1이 끝난 지점 이후로 계속 진행시키면
> LR이 다시 올라간다 — 그대로 두면 phase2 LR 누적량이 원래 의도(2e-5 고정)보다 3.2배 커진다.(실측 확인)
> 그래서 phase가 바뀔 때는 full checkpoint resume을 쓰지 않았다.(mcs2에서도 optimizer와 LR scheduler 상태는 새로 시작함)
>
> 반면 같은 phase 학습이 중단되어 재시작하는 경우에는 optimizer·scheduler 상태를 그대로
> 이어야 하므로 full checkpoint resume을 사용한다.


> **loss 설계**: phase1·phase2 공통으로 L_flow(matte로 가중한 flow matching loss)를 기본으로
> 하고, LPIPS를 timestep 기준으로 게이팅해서 더한다. phase2에서는 edge loss가 추가된다.
>
> LPIPS는 학습 step 수가 아니라 diffusion timestep(σ, 노이즈 강도)을 기준으로 켠다 —
> σ≤0.7일 때만 적용하는 noise-gate 방식이다.
> phase2에도 LPIPS를 동일하게 적용했고, edge loss만 phase2에서 새로 켰다(phase1은 w_edge=0).
>
> 두 phase에 공통으로 쓰는 항목(정의 동일):
> - `L_flow = Σ(m̃⊙(v_pred-v_target)²) / (‖m̃‖₁+ε)` — matte(헤어 영역)로 가중한 flow matching loss, matte L1 norm으로 정규화  
> s = clamp(numel(v_pred)/‖matte_latent‖₁, 20, 120)  (scale-sync, flow 항을 lpips/edge와 gradient 스케일 맞춤용, phase 무관 동일 적용)  
> 
> ```
> phase1: L_total = w_flow·(L_flow/s) + w_lpips·1[σ≤0.7]·L_LPIPS
>               = 1.0·(L_flow/s) + 0.002·1[σ≤0.7]·L_LPIPS     (w_edge=0)
>
> phase2: L_total = w_flow·(L_flow/s) + w_lpips·1[σ≤0.7]·L_LPIPS + w_edge·L_edge
>               = 1.0·(L_flow/s) + 0.002·1[σ≤0.7]·L_LPIPS + 0.05·L_edge
> ```

## 정량지표

> 조건: CRG 2 + BLD + `--recolor_from_gt`. 지표는 matte(마스크) 영역에만 계산
> BLD 배경은 GT(머리 있는) 사진을 그대로 사용

phase2는 replay(unbraid+braid 8:8) 학습이므로 **unbraid 유지력**과 **braid 습득**을 따로 측정한다.
unbraid만 보면 "안 까먹었나"만 알 뿐 phase2의 목적인 braid 품질은 알 수 없다.

### unbraid — 유지력 (n=50, seed 4개)

| epoch | GT 오차 평균 [deg] | coherence | seed 불일치 [deg] | dE_unbraid | lpips_unbraid |
|---:|---:|---:|---:|---:|---:|
| 5 | **14.13** | 0.793 | 9.35±2.71 | 1.6518 | 0.1864 |
| 10 | 14.28 | 0.782 | 9.23±2.62 | 1.5687 | 0.1847 |
| 15 | 14.18 | 0.779 | 8.92±2.60 | 1.7912 | 0.1851 |
| 20 | 14.19 | 0.775 | 8.85±2.55 | **1.2410** | **0.1796** |
| 25 | 14.21 | 0.776 | 8.56±2.48 | 1.4934 | 0.1817 |
| 30 | 14.25 | 0.776 | 8.55±2.48 | 1.5481 | 0.1797 |
| 35 | 14.22 | 0.772 | 8.45±2.46 | 1.4850 | 0.1804 |
| 40 | 14.19 | 0.773 | **8.35±2.45** | 1.4738 | 0.1807 |

**관측**(수치에서 직접 계산한 사실):

- 방향 지표 최적: GT 오차 epoch5, seed 불일치 epoch40
- 색/구조 지표 최적: dE_unbraid epoch20, lpips_unbraid epoch20
- GT 오차 단조 감소 여부: 아니오(epoch5가 최저, 이후 14.18~14.28 사이 등락) / seed 불일치 단조 감소 여부: 예
- coherence 범위: 0.772 ~ 0.793

### braid — 습득 (n=50, seed 4개)

inference 조건은 unbraid와 완전히 동일(CRG=2, BLD, pixel_blend).

지표 정의는 braid 항목과 같다 —
`lpips_braid`는 GT 대비 질감 충실도(↓), **`edge_iou_braid`는 입력 스케치 대비 구조 충실도(↑)로
braid 형태를 따라갔는지를 보는 phase2의 핵심 지표**다.

| epoch | GT 오차 평균 [deg] | coherence | seed 불일치 [deg] | lpips_braid ↓ | edge_iou_braid ↑ |
|---:|---:|---:|---:|---:|---:|
| 5 | 21.80 | 0.718 | 16.28±3.66 | 0.1399 | 0.0943 |
| 10 | 21.26 | 0.721 | 14.87±3.27 | 0.1375 | 0.0940 |
| 15 | 21.09 | 0.709 | 14.46±3.41 | 0.1321 | 0.0951 |
| 20 | 21.04 | 0.705 | 13.59±3.04 | 0.1285 | 0.0947 |
| 25 | 20.73 | 0.707 | 12.75±2.84 | 0.1282 | 0.0951 |
| 30 | 20.55 | 0.704 | 12.23±2.75 | **0.1278** | 0.0955 |
| 35 | 20.48 | 0.700 | 11.98±2.71 | 0.1283 | **0.0959** |
| 40 | **20.45** | 0.700 | **11.87±2.68** | 0.1283 | 0.0958 |

**관측**(수치에서 직접 계산한 사실):

- 방향 지표 최적: GT 오차 epoch40, seed 불일치 epoch40 (둘 다 단조 감소)
- seed 불일치 16.28° → 11.87°로 **27% 감소**
- edge_iou_braid는 epoch35에서 최고(0.0959), epoch40은 0.0958로 거의 동일
- lpips_braid는 epoch30에서 최저(0.1278), epoch35~40은 0.1283으로 거의 동일
- coherence 범위: 0.700 ~ 0.721

### 두 축 종합

| 축 | 지표 | 최적 epoch |
|---|---|---:|
| braid 습득 | GT 오차 / seed 불일치 | **40 / 40** |
| | edge_iou_braid / lpips_braid | 35 / 30 |
| unbraid 유지 | GT 오차 / seed 불일치 | 5 / **40** |
| | dE_unbraid / lpips_unbraid | 20 / 20 |

**두 축이 크게 상충하지 않는다.** unbraid GT 오차만 epoch5가 근소하게 최저(14.13, epoch40은
14.19로 차이 0.06°)이고 나머지 지표는 대체로 epoch 20~40 구간이 낫다. braid는 방향 지표
둘 다 epoch40이 최적이다.

`lpips`/`dE` 계열이 epoch20~30에서 최저를 찍지만 변동폭이 좁아 노이즈 범위로 보이며, 지시 ④가
색 지표는 참고용으로 한정했으므로 선정 근거로 쓰지 않는다.


## 정성지표 — 결과 사진

> seed42 기준, 모든 run7 정성평가 지표에 CRG = 2 적용

### gt sketch


| 파일명 | img | sketch | epoch5 | epoch10 | epoch15 | epoch20 | epoch25 | epoch30 | epoch35 | epoch40 |
|---|---|---|---|---|---|---|---|---|---|---|
| CM_1007 | <img src="../dataset/test/img/CM_1007.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/CM_1007.png" width="70"> |
| CM_1027 | <img src="../dataset/test/img/CM_1027.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/CM_1027.png" width="70"> |
| CM_1033 | <img src="../dataset/test/img/CM_1033.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/CM_1033.png" width="70"> |
| CM_1067 | <img src="../dataset/test/img/CM_1067.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/CM_1067.png" width="70"> |
| CM_1068 | <img src="../dataset/test/img/CM_1068.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/CM_1068.png" width="70"> |
| CM_1084 | <img src="../dataset/test/img/CM_1084.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/CM_1084.png" width="70"> |
| CM_1172 | <img src="../dataset/test/img/CM_1172.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/CM_1172.png" width="70"> |
| braid_2548 | <img src="../dataset/test/img/braid_2548.png" width="70"> | <img src="../dataset/test/sketch/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/braid_2548.png" width="70"> |
| braid_2562_1 | <img src="../dataset/test/img/braid_2562_1.png" width="70"> | <img src="../dataset/test/sketch/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/braid_2562_1.png" width="70"> |
| braid_2625 | <img src="../dataset/test/img/braid_2625.png" width="70"> | <img src="../dataset/test/sketch/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/braid_2625.png" width="70"> |
| braid_4156 | <img src="../dataset/test/img/braid_4156.png" width="70"> | <img src="../dataset/test/sketch/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/braid_4156.png" width="70"> |

### Colorful sketch

| 파일명 | img | sketch | epoch5 | epoch10 | epoch15 | epoch20 | epoch25 | epoch30 | epoch35 | epoch40 |
|---|---|---|---|---|---|---|---|---|---|---|
| CM_1007 | <img src="../dataset/test/img/CM_1007.png" width="70"> | <img src="../dataset/test/sketch/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/CM_1007.png" width="70"> |
| CM_1027 | <img src="../dataset/test/img/CM_1027.png" width="70"> | <img src="../dataset/test/sketch/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/CM_1027.png" width="70"> |
| CM_1033 | <img src="../dataset/test/img/CM_1033.png" width="70"> | <img src="../dataset/test/sketch/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/CM_1033.png" width="70"> |
| CM_1067 | <img src="../dataset/test/img/CM_1067.png" width="70"> | <img src="../dataset/test/sketch/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/CM_1067.png" width="70"> |
| CM_1068 | <img src="../dataset/test/img/CM_1068.png" width="70"> | <img src="../dataset/test/sketch/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/CM_1068.png" width="70"> |
| CM_1084 | <img src="../dataset/test/img/CM_1084.png" width="70"> | <img src="../dataset/test/sketch/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/CM_1084.png" width="70"> |
| CM_1172 | <img src="../dataset/test/img/CM_1172.png" width="70"> | <img src="../dataset/test/sketch/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/CM_1172.png" width="70"> |
| braid_2548 | <img src="../dataset/test/img/braid_2548.png" width="70"> | <img src="../dataset/test/sketch/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/braid_2548.png" width="70"> |
| braid_2562_1 | <img src="../dataset/test/img/braid_2562_1.png" width="70"> | <img src="../dataset/test/sketch/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/braid_2562_1.png" width="70"> |
| braid_2625 | <img src="../dataset/test/img/braid_2625.png" width="70"> | <img src="../dataset/test/sketch/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/braid_2625.png" width="70"> |
| braid_4156 | <img src="../dataset/test/img/braid_4156.png" width="70"> | <img src="../dataset/test/sketch/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/braid_4156.png" width="70"> |


## 분석

### 1. phase1 epoch40 vs phase2 epoch 5 비교

**gt sketch (braid, `--recolor_from_gt`)**
phase1에 없던 braid hair 대한 능력 학습

| 파일명 | img | sketch | phase1 epoch40 | phase2 epoch5 |
|---|---|---|---|---|
| braid_2548 | <img src="../dataset/test/img/braid_2548.png" width="70"> | <img src="../dataset/test/sketch/braid_2548.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch40/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_2548.png" width="70"> |
| braid_2562_1 | <img src="../dataset/test/img/braid_2562_1.png" width="70"> | <img src="../dataset/test/sketch/braid_2562_1.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch40/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_2562_1.png" width="70"> |
| braid_4156 | <img src="../dataset/test/img/braid_4156.png" width="70"> | <img src="../dataset/test/sketch/braid_4156.png" width="70"> | <img src="../outputs/0812/run7_phase1/gt/42/epoch40/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_4156.png" width="70"> |

**Colorful sketch(unbraid)**
색 반영 능력 미세하게 향상되거나(CM_1007), 유지

| 파일명 | img | sketch | phase1 epoch40 | phase2 epoch5 |
|---|---|---|---|---|
| CM_1007 | <img src="../dataset/test/img/CM_1007.png" width="70"> | <img src="../dataset/test/sketch/CM_1007.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1007.png" width="70"> |
| CM_1067 | <img src="../dataset/test/img/CM_1067.png" width="70"> | <img src="../dataset/test/sketch/CM_1067.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1067.png" width="70"> |
| CM_1068 | <img src="../dataset/test/img/CM_1068.png" width="70"> | <img src="../dataset/test/sketch/CM_1068.png" width="70"> | <img src="../outputs/0812/run7_phase1/color/42/epoch40/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1068.png" width="70"> |


### 2. unbraid은 유지, braid는 정성·정량 괴리 (정성: ~15epoch 이후 정체·저하 / 정량: ~30epoch까지 개선)

**unbraid**: 능력 거의 그대로 유지 — GT 오차는 epoch5(14.13)가 최저, dE_unbraid는 epoch20
(1.24)이 최저(위 "unbraid — 유지력" 표 참고).

**braid — 정성 관찰(일부 seed·이미지)**: 정량지표와 별개로, 육안으로는 15epoch 전후부터
오히려 품질 저하되는 사례가 보인다.

- `braid_2625`(Colorful sketch, seed 1/2/42 ): epoch가 올라갈수록 일부 머릿결이 노이즈처럼 깨짐
- `braid_2562_1`(gt sketch, seed 42): epoch가 올라갈수록 땋은 머리 경계가 옅어짐

**braid_2625 (Colorful sketch) — seed 1 / 2 / 42**

| seed | epoch5 | epoch10 | epoch15 | epoch20 | epoch25 | epoch30 | epoch35 | epoch40 |
|---|---|---|---|---|---|---|---|---|
| 1 | <img src="../outputs/0813/run7_phase2_rawstart/color/1/epoch5/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/1/epoch10/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/1/epoch15/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/1/epoch_20/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/1/epoch_25/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/1/epoch_30/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/1/epoch_35/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/1/epoch_40/braid_2625.png" width="90"> |
| 2 | <img src="../outputs/0813/run7_phase2_rawstart/color/2/epoch5/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/2/epoch10/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/2/epoch15/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/2/epoch_20/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/2/epoch_25/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/2/epoch_30/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/2/epoch_35/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/2/epoch_40/braid_2625.png" width="90"> |
| 42 | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_20/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_25/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_30/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_35/braid_2625.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/braid_2625.png" width="90"> |

**braid_2562_1 (gt sketch) — seed 42**

| seed | epoch5 | epoch10 | epoch15 | epoch20 | epoch25 | epoch30 | epoch35 | epoch40 |
|---|---|---|---|---|---|---|---|---|
| 42 | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_2562_1.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/braid_2562_1.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/braid_2562_1.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_20/braid_2562_1.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_25/braid_2562_1.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_30/braid_2562_1.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_35/braid_2562_1.png" width="90"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch_40/braid_2562_1.png" width="90"> |

**정량지표와의 괴리**: 반면 braid 정량지표(edge_iou_braid, lpips_braid)는 epoch25~35까지 계속
개선된다(위 "braid — 습득" 표 참고 — edge_iou_braid 최고 epoch35, lpips_braid 최저 epoch25).
n=50 평균에서는 개선되는데 위 두 stem처럼 개별 이미지·seed 단위에서는 일부이미지에서 품질 저하가 보임. 
정량지표(평균)가 이런 개별 사례의 품질 저하를 못 잡아내고 있을 가능성이 있다 — 원인·재현 범위는 미확인.

### 3. 색 반영

**unbraid: mcs2는 sketch에 없는 색까지 만들어내는 경향이 있었는데 run7_phase2는 sketch에 없는 색을 만들어 내는 경향이 약해짐**

>seed 42

| 파일명 | sketch | run7_phase2 epoch40 (color) | mcs2 (color) |
|---|---|---|---|
| CM_1084 | <img src="../dataset/test/sketch/CM_1084.png" width="110"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/CM_1084.png" width="110"> | <img src="../outputs/0813/mcs2_ref_seed42/color/CM_1084.png" width="110"> |
| CM_1067 | <img src="../dataset/test/sketch/CM_1067.png" width="110"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/CM_1067.png" width="110"> | <img src="../outputs/0813/mcs2_ref_seed42/color/CM_1067.png" width="110"> |

**braid: 색 반영이 약함 — mcs2에서도 있던 문제가 이번에도 재현** — unbraid는 sketch 색을 거의
그대로 따라가지만, braid는 두 모델 다 색 반영이 약하다.

| 파일명 | sketch | run7_phase2 epoch40 (color) | mcs2 (color) |
|---|---|---|---|
| braid_4156 | <img src="../dataset/test/sketch/braid_4156.png" width="110"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/braid_4156.png" width="110"> | <img src="../outputs/0813/mcs2_ref_seed42/color/braid_4156.png" width="110"> |
| braid_2548 | <img src="../dataset/test/sketch/braid_2548.png" width="110"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch_40/braid_2548.png" width="110"> | <img src="../outputs/0813/mcs2_ref_seed42/color/braid_2548.png" width="110"> |


### 4. 경계 블러

헤어 경계 부분 블러 문제 해결

#### 기존 방식

경계 처리는 두 단계로 이루어진다 — 18step까지는 매 스텝 BLD 적용, 18~20step은 순수 배경
(matte=0)만 계속 BLD 적용하고 경계(0<matte<1) 구간은 자유 생성. 이후 decoder를 통과한 뒤
pixel space에서 한 번 더 matte로 합성한다(합성식은 아래 참고):

| 단계 | 시점 | 파라미터 | 코드 |
|---|---|---|---|
| ① latent BLD | 매 디노이징 스텝(`bld_mode=full`) | `bld_soft_steps=18`(20스텝 중), `bld_alpha=1.0`(기본, 미지정) | :273-280 |
| ② pixel blend | VAE decode 직후 1회 | `pixel_blend_alpha=0.75` | :456-474 |

> ① `latents = m·latents + (1-m)·noised_bg`,  `noised_bg = (1-σ)·x0_bg + σ·noise`  
> `m = mask_lat` (i<18) / `m = 1[mask_lat>1e-4]` (i≥18, 순수 배경만 유지·경계는 자유 생성)
>
> ② `eff_matte = α·matte + (1-α)`  (α=`pixel_blend_alpha`)  
> `result = eff_matte·hair_img + (1-eff_matte)·face_img`

**원인 분석**:
1. **pixel blend(alpha)** — ②의 `eff_matte` 식이 문제. matte=0인 순수 배경 픽셀에서도
   `eff_matte=(1-α)`로 고정되는데, 이 값은 헤어로부터의 거리와 무관한 상수. 즉 α<1이면
   경계 근처뿐 아니라 이미지 전체 배경에 생성 이미지(hair_img)가 (1-α) 비율로 균일하게
   섞여 들어감 — 경계만 부드럽게 해야 하는데 전역 블렌딩이 되고 있었음.
2. **BLD step ablation** — 경계 영역은 18step까지 BLD를 적용하고
   나머지 2step만 자유 생성하는데, 여러 이미지에서 18이 아닌 다른 step 값과의 비교 필요.

#### 1. matte feathering

matte 경계에 해당하는 부분에만 국소적으로 가우시안 블러 적용.

matte feathering 식 : 
> `eff_matte = gaussian_blur(matte, σ=feather_px)`  
> `result = eff_matte·hair_img + (1-eff_matte)·face_img`
> hair_img : 모델이 생성한 이미지 / face_img : 민머리 사진(배경 원본)

결과 비교(seed42, epoch40, color sketch):

| 파일명 | img | 적용 안함(α=0) | 기존 방식(α=0.75) | matte feathering |
|---|---|---|---|---|
| CM_1067 | <img src="../dataset/test/img/CM_1067.png" width="100"> | <img src="../outputs/0813/matte_blending/0/color/seed42_epoch40/CM_1067.png" width="100"> | <img src="../outputs/0813/matte_blending/0.75/color/CM_1067.png" width="100"> | <img src="../outputs/0814/matte_blending_feather/0/color/CM_1067.png" width="100"> |
| CM_1033 | <img src="../dataset/test/img/CM_1033.png" width="100"> | <img src="../outputs/0813/matte_blending/0/color/seed42_epoch40/CM_1033.png" width="100"> | <img src="../outputs/0813/matte_blending/0.75/color/CM_1033.png" width="100"> | <img src="../outputs/0814/matte_blending_feather/0/color/CM_1033.png" width="100"> |
| CM_1172 | <img src="../dataset/test/img/CM_1172.png" width="100"> | <img src="../outputs/0813/matte_blending/0/color/seed42_epoch40/CM_1172.png" width="100"> | <img src="../outputs/0813/matte_blending/0.75/color/CM_1172.png" width="100"> | <img src="../outputs/0814/matte_blending_feather/0/color/CM_1172.png" width="100"> |

결과 : 큰 차이 없음

#### 2. BLD step ablation study

경계 영역을 몇 step까지 BLD로 묶어둘지에 대한 비교(seed42, epoch40, color sketch, matte feathering 적용), 위에서 한 것들은 step 18적용:

| 파일명 | img | step 0 | step 10 | step 15 | step 18 | step 20 |
|---|---|---|---|---|---|---|
| CM_1007 | <img src="../dataset/test/img/CM_1007.png" width="90"> | <img src="../outputs/0814/bld/0/color/CM_1007.png" width="90"> | <img src="../outputs/0814/bld/10/color/CM_1007.png" width="90"> | <img src="../outputs/0814/bld/15/color/CM_1007.png" width="90"> | <img src="../outputs/0814/matte_blending_feather/0/color/CM_1007.png" width="90"> | <img src="../outputs/0814/bld/20/color/CM_1007.png" width="90"> |
| CM_1033 | <img src="../dataset/test/img/CM_1033.png" width="90"> | <img src="../outputs/0814/bld/0/color/CM_1033.png" width="90"> | <img src="../outputs/0814/bld/10/color/CM_1033.png" width="90"> | <img src="../outputs/0814/bld/15/color/CM_1033.png" width="90"> | <img src="../outputs/0814/matte_blending_feather/0/color/CM_1033.png" width="90"> | <img src="../outputs/0814/bld/20/color/CM_1033.png" width="90"> |
| CM_1067 | <img src="../dataset/test/img/CM_1067.png" width="90"> | <img src="../outputs/0814/bld/0/color/CM_1067.png" width="90"> | <img src="../outputs/0814/bld/10/color/CM_1067.png" width="90"> | <img src="../outputs/0814/bld/15/color/CM_1067.png" width="90"> | <img src="../outputs/0814/matte_blending_feather/0/color/CM_1067.png" width="90"> | <img src="../outputs/0814/bld/20/color/CM_1067.png" width="90"> |
| CM_1084 | <img src="../dataset/test/img/CM_1084.png" width="90"> | <img src="../outputs/0814/bld/0/color/CM_1084.png" width="90"> | <img src="../outputs/0814/bld/10/color/CM_1084.png" width="90"> | <img src="../outputs/0814/bld/15/color/CM_1084.png" width="90"> | <img src="../outputs/0814/matte_blending_feather/0/color/CM_1084.png" width="90"> | <img src="../outputs/0814/bld/20/color/CM_1084.png" width="90"> |
| CM_1172 | <img src="../dataset/test/img/CM_1172.png" width="90"> | <img src="../outputs/0814/bld/0/color/CM_1172.png" width="90"> | <img src="../outputs/0814/bld/10/color/CM_1172.png" width="90"> | <img src="../outputs/0814/bld/15/color/CM_1172.png" width="90"> | <img src="../outputs/0814/matte_blending_feather/0/color/CM_1172.png" width="90"> | <img src="../outputs/0814/bld/20/color/CM_1172.png" width="90"> |

결과 : step 20(matte 경계부분 자유생성 미적용)이 제일 경계부분 자연스러움