# run7_phase2 결과 (rawstart)

> 학습: `configs/run7_phase2_rawstart.yaml` / 체크포인트: `checkpoints/run7_phase2_rawstart/`
> 정성 inference: `outputs/0813/run7_phase2_rawstart/` · 정량 inference: `outputs/0813/quant50/run7_phase2_rawstart/`

## 요약 — 1차 run7_phase2는 폐기, EMA 시작 버그 수정 후 재학습

1차 `run7_phase2`(= `checkpoints/run7_phase2/`)는 **color sketch의 색 조건화가 phase2 epoch5부터
붕괴**했다. phase1 epoch40은 멀티컬러를 정확히 반영하는데 phase2 epoch5는 단색으로 나왔다.

**원인은 LR이 아니라 `resume_from`의 EMA 덮어쓰기였다.**

- `trainer.py`의 `resume_from`이 raw 가중치를 로드한 뒤 **EMA shadow로 다시 덮어쓰고** 있었다
  (e623ab0, [0724] planning §6 — "best.pth가 EMA 기준으로 선정되므로 시작 가중치도 EMA로 맞춘다").
- 그런데 best.pth 자동 저장은 이후 제거됐고([0729]retrain_plan_v2.md), 채택은 전 체크포인트
  inference로 하는데 그 inference는 `_infer.pth`(= **raw only**, `trainer.py:909`)를 쓴다.
  즉 **선정 근거가 EMA→raw로 바뀌었는데 EMA 시작 코드만 남아** 전제가 무너져 있었다.
- 실측 (`checkpoints/run7_phase1/epoch_40.pth`의 raw vs ema shadow):

| 레이어 | ‖ema‖/‖raw‖ |
|---|---:|
| `controlnet_blocks` (조건 신호 주입, zero-init) | **0.396x** |
| 일반 transformer 레이어 | 0.99x |
| `matte_cnn` | 0.994x |

  조건 주입 경로만 40% 세기로 깎여 있었다. `EMAModel`에 bias correction이 없고 decay=0.9999라
  수렴에 `1/(1-decay)=10,000` step이 필요한데 phase1은 7,480 step뿐이라 **EMA의 47.3%가 아직
  학습 전 초기값**이고, zero-init 레이어는 0에서 자라므로 EMA가 구조적으로 과소평가된다.
- 이 버그는 `0725_phase2_issues.md` §2에 "심각, 수정 완료"로 이미 기록돼 있었으나 **그 수정이
  커밋되지 않아 유실**됐고 이번에 재발했다. 재발 방지를 위해 제거 사유와 실측치를 코드 주석에
  남기고 커밋했다(`d60f32f`).
- mcs2가 같은 LR 2e-5로도 결과가 좋았던 이유도 여기서 설명된다 — mcs2는 6월 실험으로
  **EMA 로드 코드(e623ab0, 7/24) 도입 이전**이라 raw에서 시작했다.

**검증**: LR은 2e-5 그대로 두고 EMA 수정 **단일 변수만** 바꿔 재학습한 결과, epoch5에서 색이
복원됐다(아래 Colorful sketch 표 epoch5 열). 인과가 분리되어 확인된다.

부수적으로 `_perceptual_validate()`도 EMA 스왑을 제거해 raw 기준으로 측정하도록 고쳤다(`3d46fb6`).
채택은 raw로 하는데 측정만 EMA로 하던 불일치를 없앤 것이다. 다만 **이번 학습은 epoch1~5가 EMA
기준, epoch6~40이 raw 기준**이라 perceptual val 로그에 불연속이 있다(중간점검 재개 시점에 적용).

## 학습 조건

`configs/run7_phase2_rawstart.yaml` vs `configs/run7_phase1.yaml`

| 블록 | 키 | run7_phase1 | run7_phase2_rawstart | 상태 | 사유 |
|---|---|---|---|---|---|
| training | phase | pretrain | **finetune** | 변경 | edge loss 활성화 |
| training | dataset | unbraid | **replay** | 변경 | unbraid 3000 + braid 1000, 8:8 stratified |
| training | epochs | 40 | 40 | 동일 | |
| training | batch_size | 16 | 16 | 동일 | batch_sampler(8+8)가 실질 결정 |
| training | learning_rate | 1.0e-4 | **2.0e-5** | 변경 | mcs2 parity(2e-5). 5e-6은 미적용 — 아래 각주 |
| training | warmup_steps | 500 | 500 | 동일 | |
| training | resume | `run5_1_noisegate/epoch_15.pth` | null | 변경 | phase 이관은 resume_from 사용 |
| training | resume_from | — | `run7_phase1/epoch_40.pth` | 신규 | **weights-only (raw)**. EMA 덮어쓰기 제거됨 |
| loss_weights | flow | 1.0 | 1.0 | 동일 | |
| loss_weights | lpips | 0.002 | 0.002 | 동일 | |
| loss_weights | edge | 0.0 | **0.05** | 변경 | mcs2 parity 유지 (교수님 확정) |
| loss_weights | scale_sync / s_min / s_max | true / 20 / 120 | true / 20 / 120 | 동일 | |
| checkpointing | save_every | 5 | 5 | 동일 | epoch 5/10/…/40 + final |
| checkpointing | perceptual_every | 1 | 1 | 동일 | |

> **LR 5e-6 vs 2e-5 (교수님 지시 ③)**: `[0721]loss_design_rationale.md`가 "phase2 @ 2e-5에서
> unbraid 훼손"을 근거로 replay + LR 5e-6을 처방했으나, 이번 색 소실의 실제 원인은 EMA 시작으로
> 밝혀졌다. mcs2(raw 시작, 2e-5)가 양호했던 전례가 있어 **2e-5를 유지하고 EMA 수정만 단일 변수로**
> 적용했다. LR 인하 필요 여부는 이번 결과의 unbraid 지표(dE_unbraid/lpips_unbraid)를 보고 판단한다.

> **resume 형태 (교수님 지시 ②)**: phase1→phase2 이관은 `resume_from` = **weights-only**(controlnet
> 가중치만, optimizer/lr_scheduler 미복원)이다. full checkpoint(`resume:`)를 쓰면 phase1의
> lr_scheduler state(T_max=6980/last_epoch=6980, 코사인 끝점)가 복원되는데, CosineAnnealingLR은
> 주기 특성상 그 지점부터 LR이 다시 **1e-6 → 8.2e-5로 상승**한다(시뮬레이션 실측). LR 총합 기준
> full resume은 2e-5 런보다도 3.2배 커서 이관에는 부적합하다. 단, **동일 run 중단 후 재개**에는
> full resume이 올바른 경로이며, 이번 epoch5 중간점검 후 재개에 실제로 사용했다.

## 정량지표

> 방법론은 `[DIGLAB][0810][장서현]run5_1_quant_eval.md` §3.0과 동일 — run7_phase1 정량지표와 같은 조건(50장 pool, face 합성·BLD·pixel_blend·cfg 미사용, `--recolor_from_gt`)으로 측정해 직접 비교 가능하다.

#### n=50

| epoch | GT 오차 평균 [deg] | coherence | seed 불일치 [deg] | dE_unbraid | lpips_unbraid |
|---:|---:|---:|---:|---:|---:|
| 5 | 14.85 | 0.765 | 11.76±4.13 | 2.4244 | 0.2192 |
| 10 | 14.85 | 0.757 | 11.47±3.98 | 2.1107 | **0.2176** |
| 15 | **14.73** | 0.750 | **11.19±3.97** | **1.9928** | 0.2195 |
| final | 14.73 | 0.750 | 11.19±3.97 | 1.9928 | 0.2195 |

**phase1 epoch40(= phase2 시작점) 대비**

| 지표 | phase1 ep40 | phase2 최저 | 최저 epoch |
|---|---:|---:|---:|
| GT 오차 [deg] | 14.74 | 14.73 | 15 |
| seed 불일치 [deg] | 11.48±4.11 | 11.19 | 15 |
| dE_unbraid | 2.2868 | 1.9928 | 15 |
| lpips_unbraid | 0.2199 | 0.2176 | 10 |

**기계적 관측**(수치에서 직접 계산한 사실):

- 방향 지표 최적: GT 오차 epoch15, seed 불일치 epoch15
- 색/구조 지표 최적: dE_unbraid epoch15, lpips_unbraid epoch10
- GT 오차 단조 감소 여부: 예 / seed 불일치 단조 감소 여부: 예
- coherence 범위: 0.750 ~ 0.765

> ⚠️ **채택 epoch 최종 판단은 사람이 확인 후 확정할 것.** 위는 계산된 사실만 나열한 것이고, 교수님 지시 ④(방향 지표 필수 포함, 색 지표는 참고)에 따른 선정은 정성지표와 함께 검토가 필요하다.

## 정성지표 — 결과 사진

> seed42 기준. inference 조건: `--num_steps 20 --bld_mode full --bld_soft_steps 18
> --pixel_blend --pixel_blend_alpha 0.75 --cfg_scale 2.0`

### gt sketch

> `dataset/test/sketch_gt`에 있는 7장은 해당 파일을 그대로 사용하고, 없는 braid 4장만
> `--recolor_from_gt`로 GT 색 재채색해 생성했다. (`CM_1082`는 `dataset/test/img`에 face가 없어 제외)

| 파일명 | img | sketch | epoch5 | epoch10 | epoch15 | epochfinal |
|---|---|---|---|---|---|---|
| CM_1007 | <img src="../dataset/test/img/CM_1007.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epochfinal/CM_1007.png" width="70"> |
| CM_1027 | <img src="../dataset/test/img/CM_1027.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epochfinal/CM_1027.png" width="70"> |
| CM_1033 | <img src="../dataset/test/img/CM_1033.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epochfinal/CM_1033.png" width="70"> |
| CM_1067 | <img src="../dataset/test/img/CM_1067.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epochfinal/CM_1067.png" width="70"> |
| CM_1068 | <img src="../dataset/test/img/CM_1068.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epochfinal/CM_1068.png" width="70"> |
| CM_1084 | <img src="../dataset/test/img/CM_1084.png" width="70"> | <img src="../dataset/test/sketch_gt/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epochfinal/CM_1084.png" width="70"> |
| CM_1172 | <img src="../dataset/test/img/CM_1172.jpg" width="70"> | <img src="../dataset/test/sketch_gt/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epochfinal/CM_1172.png" width="70"> |
| braid_2548 | <img src="../dataset/test/img/braid_2548.png" width="70"> | <img src="../dataset/test/sketch/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epochfinal/braid_2548.png" width="70"> |
| braid_2562_1 | <img src="../dataset/test/img/braid_2562_1.png" width="70"> | <img src="../dataset/test/sketch/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epochfinal/braid_2562_1.png" width="70"> |
| braid_2625 | <img src="../dataset/test/img/braid_2625.png" width="70"> | <img src="../dataset/test/sketch/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epochfinal/braid_2625.png" width="70"> |
| braid_4156 | <img src="../dataset/test/img/braid_4156.png" width="70"> | <img src="../dataset/test/sketch/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch5/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch10/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epoch15/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/gt/42/epochfinal/braid_4156.png" width="70"> |

### Colorful sketch

| 파일명 | img | sketch | epoch5 | epoch10 | epoch15 | epochfinal |
|---|---|---|---|---|---|---|
| CM_1007 | <img src="../dataset/test/img/CM_1007.png" width="70"> | <img src="../dataset/test/sketch/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1007.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epochfinal/CM_1007.png" width="70"> |
| CM_1027 | <img src="../dataset/test/img/CM_1027.png" width="70"> | <img src="../dataset/test/sketch/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1027.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epochfinal/CM_1027.png" width="70"> |
| CM_1033 | <img src="../dataset/test/img/CM_1033.png" width="70"> | <img src="../dataset/test/sketch/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1033.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epochfinal/CM_1033.png" width="70"> |
| CM_1067 | <img src="../dataset/test/img/CM_1067.png" width="70"> | <img src="../dataset/test/sketch/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1067.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epochfinal/CM_1067.png" width="70"> |
| CM_1068 | <img src="../dataset/test/img/CM_1068.png" width="70"> | <img src="../dataset/test/sketch/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1068.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epochfinal/CM_1068.png" width="70"> |
| CM_1084 | <img src="../dataset/test/img/CM_1084.png" width="70"> | <img src="../dataset/test/sketch/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1084.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epochfinal/CM_1084.png" width="70"> |
| CM_1172 | <img src="../dataset/test/img/CM_1172.jpg" width="70"> | <img src="../dataset/test/sketch/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/CM_1172.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epochfinal/CM_1172.png" width="70"> |
| braid_2548 | <img src="../dataset/test/img/braid_2548.png" width="70"> | <img src="../dataset/test/sketch/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/braid_2548.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epochfinal/braid_2548.png" width="70"> |
| braid_2562_1 | <img src="../dataset/test/img/braid_2562_1.png" width="70"> | <img src="../dataset/test/sketch/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/braid_2562_1.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epochfinal/braid_2562_1.png" width="70"> |
| braid_2625 | <img src="../dataset/test/img/braid_2625.png" width="70"> | <img src="../dataset/test/sketch/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/braid_2625.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epochfinal/braid_2625.png" width="70"> |
| braid_4156 | <img src="../dataset/test/img/braid_4156.png" width="70"> | <img src="../dataset/test/sketch/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch5/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch10/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epoch15/braid_4156.png" width="70"> | <img src="../outputs/0813/run7_phase2_rawstart/color/42/epochfinal/braid_4156.png" width="70"> |

> **epoch5 열이 1차 run7_phase2 대비 핵심 비교 지점이다.** 동일 epoch·동일 seed·동일 LR에서
> EMA 시작이면 단색, raw 시작이면 멀티컬러가 나온다.

## 채택 epoch

> ⚠️ 위 정량지표와 정성 이미지를 함께 보고 확정할 것. 교수님 지시 ④에 따라 방향 지표
> (GT 오차·seed 불일치)를 필수로 포함하고 색 지표는 참고로만 사용한다.
