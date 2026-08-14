# run8 — soft gate plan

## 목적
run7과 완전히 동일한 파이프라인에서 **matte gate 메커니즘만** 바꾼다: 고정 `gate_alpha=1.0` →
학습 iteration마다 `a ∈ {0,1}`을 Bernoulli(0.5)로 샘플하는 "gate dropout"(last_test.md 훈련 방침).
목적은 gate on/off 양쪽에서 모델이 정상 동작하는지 확인하는 것(선행 검증) — 통과하면 나머지
ablation(sketch-only 등)으로 확장.

## 범위
- **바꾸는 것 ①**: `gate_block_samples()`에 넘기는 `gate_alpha` 값의 결정 방식(학습 시에만).
- **바꾸는 것 ②**: 학습 루프 내 중간평가(`_validate`, `_perceptual_validate`) **전면 제거**.
  이유는 아래 "중간평가 제거" 절 참고.
- **안 바꾸는 것**: densify off, loss 구성(flow/lpips noise-gate/edge/scale-sync), replay 8:8,
  epoch/batch/lr 스케줄, `schedule: all`, checkpoint 저장(`save_every`).
- phase1 + phase2 **둘 다** soft gate 적용(run5_1 epoch15부터 재학습, run7과 동일 시작점).

## 중간평가(in-loop eval) 제거
run7까지는 `_perceptual_validate`가 매 epoch 학습 GPU에서 20-step 샘플링+VAE decode+지표
계산까지 다 하고, 그 로그로 phase 이관 epoch을 사후 선정했다. 그런데 이미 최종 채택 후보들은
`infer_custom.py`(CRG+BLD)+`eval_metrics.py`로 오프라인 재평가하고 있으므로, in-loop
perceptual_validate는 사실상 **같은 계산을 두 번** 하는 셈(코드도 실제로 `infer_custom.py`/
`eval_metrics.py`를 그대로 import해서 씀 — `trainer.py` `_perceptual_validate` 참고).

**결정(2026-08-14, 사용자 확인)**: run8부터 `_perceptual_validate`뿐 아니라 `_validate`(flow
loss만 계산, decode/샘플링 없음 — 사실 거의 공짜지만 이것도 제거)까지 **둘 다 끈다**.
대신 `save_every`마다 저장되는 `epoch_N.pth`가 나올 때마다, **남는 GPU에서
`infer_custom.py`+`eval_metrics.py`를 돌려 오프라인으로 평가**한다. phase 이관 epoch 사후
선정 기준(방향 지표 우선, run7과 동일)은 그대로 유지 — 로그 소스만 in-loop TensorBoard에서
오프라인 스윕 결과로 바뀔 뿐. 오프라인 평가 시 gate는 run7 리포트와 동일 관례(`gate_alpha=1.0`,
CRG 2.0 + BLD)로 고정해야 run7과 비교 가능.
(mcs2는 애초에 `_perceptual_validate` 도입〈`f8dc5a9`, 0724 retrain plan〉이전에 학습되어 이
메커니즘을 쓴 적이 없음 — git log 확인, 비교 대상 아님.)

## 코드 변경 — src/training/trainer.py
1. `Trainer.__init__`: `self.gate_mode = cfg["training"].get("gate_mode", "fixed")`,
   `self.gate_dropout_p = cfg["training"].get("gate_dropout_p", 0.5)`,
   `self.midtrain_eval = cfg["training"].get("midtrain_eval", True)`. 키 없으면 기존 configs는
   100% 동일 동작(하위호환, run1~7 무영향).
2. `_train_step()`: `gate_block_samples()` 호출 직전, `gate_mode == "soft"`면
   `a = 1.0 if random.random() < self.gate_dropout_p else 0.0`을 **iteration당 1회**(배치 단위,
   샘플 단위 아님) 샘플해 `gate_alpha` 자리에 사용. `"fixed"`면 기존 `self.gate_alpha` 그대로.
3. 로깅: `log_dict["gate_a"] = a` — `lpips_active_fraction`과 같은 패턴으로 실측 on-비율
   검증용(착수 직후 필수 확인 항목에 추가: `gate_a` 평균 ≈ 0.5±).
4. `midtrain_eval=False`일 때 `train()`에서 건너뛸 것:
   - `_setup_perceptual_eval()` 호출(`__init__`) 자체를 스킵 — held-out 배치 준비도 불필요.
   - `train()` 시작부의 epoch-0 baseline `_perceptual_validate()` 호출.
   - `eval_every`마다의 `_validate()` 블록(flow val, `best_val_loss` 갱신).
   - `perceptual_every`마다의 `_perceptual_validate()` 블록(early-stopping patience 로직 포함
     — 어차피 run7/run8 모두 `early_stopping: false`라 실질 영향 없음).
5. `gate_block_samples()` 자체(controlnet_sd35.py)는 미변경 — `a`는 이미 `[0,1]` 스칼라
   파라미터로 받게 설계돼 있음(`r̂_k = r_k ⊙ [a·m̃+(1-a)]`).

## 신규 config
- `configs/run8_phase1.yaml`: run7_phase1.yaml 복사 + `gate_mode: soft`,
  `gate_dropout_p: 0.5`, `midtrain_eval: false` 추가. 나머지(resume:
  `run5_1_noisegate/epoch_15.pth` full ckpt, lr 1e-4, epoch 40 등) 전부 동일.
- `configs/run8_phase2.yaml`: run7_phase2.yaml 복사 + `gate_mode: soft`,
  `gate_dropout_p: 0.5`, `midtrain_eval: false` 추가.
  - **learning_rate: 2.0e-5** — committed yaml의 5e-6이 아니라 실제 승인·실행된 run7_phase2
    값을 따름(교수님 지시 ③, 방금 확인).
  - `resume_from`: run8_phase1 완주 후 오프라인 스윕 결과 보고 사후 결정(placeholder,
    run7과 동일 관례).
  - `resume`: 미사용 — phase 전환은 weights-only만(아래 EMA 항목 참고).

## EMA 버그 — 조용히 넘어가지 말 것 (last_test.md 명시 지시)
- 사실관계: phase1→phase2 전환에서 EMA shadow로 넘겼더니 사실상 처음부터 재학습되는 결과가
  나온 적이 있음(`checkpoints/joint_phase2_EMA_mistake/`가 그 실제 산출물).
- 현재 코드 상태(확인 완료): `src/training/ema.py` 삭제, trainer.py에서 EMA 참조 全제거.
  `resume_from`은 `ckpt["controlnet"]` state_dict만 로드(weights-only), optimizer/lr_scheduler는
  새로 시작(trainer.py `_setup_models` 내 `resume_from` 분기). run7도 이미 이 방식으로 실행됨.
- **run8도 이 방식 그대로 유지**(별도 변경 불필요, 이미 고쳐진 상태) — 단, run8 결과 리포트에
  "EMA 기반 phase 전환은 처음부터 재학습되는 버그였고 이후 weights-only 전환으로 수정함"을
  명시적으로 기록할 것(지시사항, 생략 금지).

## 실행 순서
1. trainer.py에 `gate_mode`/`gate_dropout_p`/`midtrain_eval` 구현. 기본값(미지정 시)으로 기존
   run과 100% 동일 출력 나오는지 확인(회귀 방지).
2. `configs/run8_phase1.yaml`, `run8_phase2.yaml` 작성.
3. run8_phase1 착수 → 학습 로그에서 `gate_a` 평균 ≈0.5 확인(트레이너 GPU에는 중간평가가 없으므로
   순수 학습 스루풋만 나옴).
4. `save_every`마다 나오는 epoch 체크포인트를 **남는 GPU에서** `infer_custom.py`+
   `eval_metrics.py`로 오프라인 스윕(gate_alpha=1.0, CRG+BLD 고정 — run7 리포트와 동일 조건).
   그 결과로 phase2 이관 epoch 사후 선정(방향지표 우선, run7과 동일 기준).
5. run8_phase2 착수(`resume_from` 확정 후, lr=2e-5) → 동일하게 저장되는 체크포인트마다
   오프라인 스윕.
6. 완료 후 gate on/off(및 CRG on/off) 조합 inference 스윕으로 "on/off 모두 정상 동작"하는지
   정성·정량 확인(last_test.md 목적) → 통과 시 나머지 ablation(sketch-only 등) 착수.
7. EMA 버그 기록 + run8 결과 리포트 작성.
