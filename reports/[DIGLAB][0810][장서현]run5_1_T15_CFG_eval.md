# run5_1 T15 CFG eval

## 최상단 요약 (10줄 이내)

**지난 미팅 (2026-08-10, 교수님 지시)** — 키워드 3줄
- run5_1 × T15 densify(추론 시점만) × 50장 × seed 4개 테스트
- 50장 배치 기존 8장 dE·lpips 재계산
- CFG {7.5→5.0→3.5} 스윕 × seed42 × 문제 이미지 2장 테스트

**합의 사항 → 상태**
- [완료] T15 densify 50장×4seed 추론·지표 계산(§1)
- [완료] 기존 8장 dE·lpips 재계산(§2)
- [완료] CFG 구현·스윕(§3)

**이번 결과 / 막힌 것 / 다음**
- 결과: T15 densify, 50장 중 48장 개선, seed 불일치 13.14°→12.32°(-6.2%)(§1)
- 결과: CFG 2.0에서 GT 오차 최선(14.32°/14.66°), 두 이미지 일치 — 표준 CFG 관례(7.5)보다
  훨씬 낮은 지점(§3)
- 막힌 것: matte 밖 영역에 프리즌 prior의 얼굴 생성 확인(§3-2) — 원인·영향 범위 판단 필요
- 다음: CFG 1.5~2.0 사이 세분화 스윕

---

## 0. 지시사항 원문

```
-- run5_1 × T15 densify × 50장 × seed 4개 테스트
-- 50장 배치 안에서 기존 8장만 dE·lpips 재계산
-- CFG {7.5→5.0→3.5} 스윕 × seed42 × 문제의 이미지 두장 테스트
```

체크포인트: `checkpoints/run5_1_noisegate/epoch_15_infer.pth`, 20-step 샘플링, BLD 적용 공통.

---

## 1. run5_1 × T15 densify × 50장 × seed 4개

### 1-1. 방법

`data/densify_masks/` 로컬 부재로 50장용 T15 컬러 스케치 신규 생성.

1. 50장 원본 스케치(`dataset/sketch`) GT색 recolor(`recolor_sketch_from_gt`, densify
   전 수행 — 학습 순서와 동일)
2. `scripts/preprocess/densify_shs.py colored --thresholds 15` T15 색전파(SHS 공식
   `getSketchCompletion`, `threshold` 외 무수정) — 밀도 0.1291±0.0106, 기존 8장용
   T15(0.122~0.129)와 동일 대역
3. run5_1 × seed `{1,2,3,42}` × 50장 추론
4. 지표: `orientation_metric.py`(structure tensor, `sigma_i=3`, `erode_px=6`) +
   `eval_metrics.py`의 `compute_delta_e_hue`/`hair_masked_lpips` —
   `quant50_run5_1_run6.py`와 동일 정의

### 1-2. 결과 — macro 평균 (50장×4seed)

| set | GT 오차 [deg] | coherence | seed 불일치 [deg] | dE_unbraid | lpips_unbraid |
|---|---:|---:|---:|---:|---:|
| T∞ (densify 없음) | 14.95 | 0.769 | 13.14±4.64 | 4.5783 | 0.2222 |
| **T15** | **14.57** | **0.782** | **12.32±4.50** | 4.6546 | **0.2175** |

GT 오차 -2.5%, seed 불일치 -6.2%, coherence 상승.

### 1-3. per-image

50장 중 **48장 개선**(seed 불일치 감소), 2장 소폭 악화(R2_1424 +0.1%, R2_1720 +0.5%).
개선폭 최대: CM_1020(-17.6%), CM_1223(-13.8%), CM_1057(-13.6%), CM_1134(-12.8%).

`[DIGLAB][0804][장서현]densified_sketch_shs.md`의 8장(2장 상세) 기준 "밀도 증가 → seed
불일치 감소" 결과, run5_1 실제 체크포인트·50장 규모에서 재현.

개선 최대 4장 + 소폭 악화 1장 seed42 비교(스케치 → 결과):

| image | T∞ 스케치 | T∞ 결과 | T15 스케치 | T15 결과 | GT |
|---|---|---|---|---|---|
| CM_1020 (-17.6%) | <img src="../data/eval50_recolor_sketch/CM_1020.png" width="110"> | <img src="../outputs/0810/eval50_face/T_inf/42/CM_1020.png" width="110"> | <img src="../data/densified_shs_eval50/T15/CM_1020.png" width="110"> | <img src="../outputs/0810/eval50_face/T15/42/CM_1020.png" width="110"> | <img src="../dataset/img/CM_1020.png" width="110"> |
| CM_1223 (-13.8%) | <img src="../data/eval50_recolor_sketch/CM_1223.png" width="110"> | <img src="../outputs/0810/eval50_face/T_inf/42/CM_1223.png" width="110"> | <img src="../data/densified_shs_eval50/T15/CM_1223.png" width="110"> | <img src="../outputs/0810/eval50_face/T15/42/CM_1223.png" width="110"> | <img src="../dataset/img/CM_1223.png" width="110"> |
| CM_1057 (-13.6%) | <img src="../data/eval50_recolor_sketch/CM_1057.png" width="110"> | <img src="../outputs/0810/eval50_face/T_inf/42/CM_1057.png" width="110"> | <img src="../data/densified_shs_eval50/T15/CM_1057.png" width="110"> | <img src="../outputs/0810/eval50_face/T15/42/CM_1057.png" width="110"> | <img src="../dataset/img/CM_1057.png" width="110"> |
| CM_1134 (-12.8%) | <img src="../data/eval50_recolor_sketch/CM_1134.png" width="110"> | <img src="../outputs/0810/eval50_face/T_inf/42/CM_1134.png" width="110"> | <img src="../data/densified_shs_eval50/T15/CM_1134.png" width="110"> | <img src="../outputs/0810/eval50_face/T15/42/CM_1134.png" width="110"> | <img src="../dataset/img/CM_1134.png" width="110"> |
| R2_1424 (+0.1%) | <img src="../data/eval50_recolor_sketch/R2_1424.png" width="110"> | <img src="../outputs/0810/eval50_face/T_inf/42/R2_1424.png" width="110"> | <img src="../data/densified_shs_eval50/T15/R2_1424.png" width="110"> | <img src="../outputs/0810/eval50_face/T15/42/R2_1424.png" width="110"> | <img src="../dataset/img/R2_1424.png" width="110"> |

### 1-4. 한계

- outlier 개수(4-seed 평균 대비 1σ 초과): T∞ 37/200 → T15 33/200(-10.8%) — 오차 크기뿐
  아니라 outlier 발생 빈도도 소폭 감소
- dE_unbraid, T∞→T15에서 소폭 상승(4.578→4.655, +1.7%) — 변화폭 작아 표본 n=50
  하나만으로는 판단 보류

---

## 2. 기존 8장 dE·lpips 재계산

### 2-1. 지시 해석

"50장 평가와 동일 방법론을 기존 8장에 독립 적용"으로 해석. 50장 무작위 풀
(`eval50_stems.txt`, `dataset/img` 466장 중 `random.seed(42)` 추출)에 기존 8장 중
CM_1007만 포함, 나머지 7장 부재 — 배치 내 추출 불가로 배치 밖 독립 재계산.

### 2-2. 방법

- run5_1 × seed `{1,2,3,42}` × 기존 8장, `--recolor_from_gt`
- GT: `dataset/img`/`dataset/matte`(50장 평가와 동일 소스)

### 2-3. 결과

| set | GT 오차 [deg] | coherence | seed 불일치 [deg] | dE_unbraid | lpips_unbraid |
|---|---:|---:|---:|---:|---:|
| 기존 8장(n=8) | 15.42 | 0.762 | 13.82±2.54 | **3.7809** | 0.2517 |
| 50장(n=50) | 14.95 | 0.769 | 13.14±4.64 | 4.5783 | **0.2222** |

방향 지표 유사. 색 지표 상반 — dE_unbraid 8장 우세(3.78<4.58), lpips_unbraid 8장
열세(0.2517>0.2222) — 8장이 색 재현 기준 "쉬운" 이미지 위주일 가능성, 원인 미확인.

### 2-4. per-image (기존 8장)

| image | dE_unbraid | lpips_unbraid | seed 불일치 [deg] |
|---|---:|---:|---:|
| CM_1007 | 4.5873 | 0.2191 | 15.68±0.97 |
| CM_1027 | 2.4152 | 0.2364 | 13.55±0.25 |
| CM_1033 | 5.4668 | 0.2324 | 13.52±1.22 |
| CM_1067 | 3.3823 | 0.3089 | 12.92±0.88 |
| CM_1068 | 2.6195 | 0.2582 | 14.86±1.00 |
| CM_1082 | 2.7000 | 0.2777 | 14.02±0.86 |
| CM_1084 | 6.0433 | 0.2726 | 17.39±1.06 |
| CM_1172 | 3.0325 | 0.2081 | 8.62±0.59 |

seed42 결과:

| | CM_1007 | CM_1027 | CM_1033 | CM_1067 | CM_1068 | CM_1082 | CM_1084 | CM_1172 |
|---|---|---|---|---|---|---|---|---|
| GT | <img src="../dataset/img/CM_1007.png" width="110"> | <img src="../dataset/img/CM_1027.png" width="110"> | <img src="../dataset/img/CM_1033.png" width="110"> | <img src="../dataset/img/CM_1067.png" width="110"> | <img src="../dataset/img/CM_1068.png" width="110"> | <img src="../dataset/img/CM_1082.png" width="110"> | <img src="../dataset/img/CM_1084.png" width="110"> | <img src="../dataset/img/CM_1172.png" width="110"> |
| 생성 결과(seed42) | <img src="../outputs/0810/eval8_orig_face/run5_1/42/CM_1007.png" width="110"> | <img src="../outputs/0810/eval8_orig_face/run5_1/42/CM_1027.png" width="110"> | <img src="../outputs/0810/eval8_orig_face/run5_1/42/CM_1033.png" width="110"> | <img src="../outputs/0810/eval8_orig_face/run5_1/42/CM_1067.png" width="110"> | <img src="../outputs/0810/eval8_orig_face/run5_1/42/CM_1068.png" width="110"> | <img src="../outputs/0810/eval8_orig_face/run5_1/42/CM_1082.png" width="110"> | <img src="../outputs/0810/eval8_orig_face/run5_1/42/CM_1084.png" width="110"> | <img src="../outputs/0810/eval8_orig_face/run5_1/42/CM_1172.png" width="110"> |

---

## 3. CFG {7.5→5.0→3.5} × seed42 × CM_1027/CM_1067

### 3-1. 구현

Unconditional 분기 = "ControlNet residual 없는 프리즌 transformer 단독 forward"
(`block_controlnet_hidden_states=None`). 매 스텝 uncond/cond 2-pass,
`v = v_uncond + w·(v_cond - v_uncond)` blend(`--cfg_scale`, 비용 약 1.4~1.5배).

한계: conditioning dropout 학습 이력 부재 — uncond 분기, 학습된 null 분포 아님.
표준 CFG 스케일 관례(7.5 등) 적용 미보장 — §3-3에서 확인.

### 3-2. 발견 — matte 밖 프리즌 prior의 얼굴 생성

CFG 검증 중 BLD 없이 CM_1027 순수 생성 확인 결과, matte=0(비-헤어) 영역에 눈·코·입
출현(`outputs/0810/cfg_sweep/none/CM_1027.png`). `FlowMatchingLoss`(`outside_weight=0.0`)의
matte 밖 supervision 배제 — 프리즌 SD3.5 prior의 무제약 출력.

BLD 매 스텝 블렌딩이 matte 안쪽 헤어 생성에도 개입 — 동일 seed·이미지, BLD 유무
대조 시 matte 안쪽 픽셀 평균 절대차 **9.4/255**(std 12.7). §1·§2는 이 결과를
반영해 전량 BLD 조건으로 생성.

| 입력 스케치 | matte | BLD 없이 본 결과(CFG 없음, seed42) |
|---|---|---|
| <img src="../data/test/recolor_sketch/CM_1027.png" width="160"> | <img src="../data/test/matt/CM_1027.png" width="160"> | <img src="../outputs/0810/cfg_sweep/none/CM_1027.png" width="160"> |

### 3-3. 결과 (seed42)

| CFG | CM_1027 GT오차 | CM_1027 coherence | CM_1067 GT오차 | CM_1067 coherence |
|---|---:|---:|---:|---:|
| 없음(기존) | 16.67 | 0.731 | 16.64 | 0.748 |
| 1.5 | 14.91 | 0.782 | 14.95 | 0.779 |
| **2.0** | **14.32** | 0.794 | **14.66** | 0.798 |
| 3.5 | 15.18 | 0.804 | 14.79 | 0.825 |
| 5.0 | 15.92 | 0.793 | 15.40 | 0.830 |
| 7.5 | 16.18 | 0.828 | 16.62 | 0.826 |

coherence, 스케일 증가에 따라 단조 증가. GT 오차는 두 이미지 모두 **2.0에서 최선**,
그 위·아래 모두 재악화 — 비단조, 최적점이 U자형 곡선의 저점. 정성: 1.5·2.0은 3.5
이상 대비 색 드리프트(주황/구리색 과포화)가 뚜렷이 약함, 스케일 더 올릴수록 결
선명도는 계속 오르지만 색·경계 아티팩트가 함께 커짐.

| CFG | CM_1027 (GT오차/coh) | CM_1067 (GT오차/coh) |
|---|---|---|
| 없음(기존) — 16.67/0.731, 16.64/0.748 | <img src="../outputs/0810/cfg_sweep_composited/none/CM_1027.png" width="160"> | <img src="../outputs/0810/cfg_sweep_composited/none/CM_1067.png" width="160"> |
| 1.5 — 14.91/0.782, 14.95/0.779 | <img src="../outputs/0810/cfg_sweep_composited/1.5/CM_1027.png" width="160"> | <img src="../outputs/0810/cfg_sweep_composited/1.5/CM_1067.png" width="160"> |
| **2.0** — 14.32/0.794, 14.66/0.798 | <img src="../outputs/0810/cfg_sweep_composited/2.0/CM_1027.png" width="160"> | <img src="../outputs/0810/cfg_sweep_composited/2.0/CM_1067.png" width="160"> |
| 3.5 — 15.18/0.804, 14.79/0.825 | <img src="../outputs/0810/cfg_sweep_composited/3.5/CM_1027.png" width="160"> | <img src="../outputs/0810/cfg_sweep_composited/3.5/CM_1067.png" width="160"> |
| 5.0 — 15.92/0.793, 15.40/0.830 | <img src="../outputs/0810/cfg_sweep_composited/5.0/CM_1027.png" width="160"> | <img src="../outputs/0810/cfg_sweep_composited/5.0/CM_1067.png" width="160"> |
| 7.5 — 16.18/0.828, 16.62/0.826 | <img src="../outputs/0810/cfg_sweep_composited/7.5/CM_1027.png" width="160"> | <img src="../outputs/0810/cfg_sweep_composited/7.5/CM_1067.png" width="160"> |

### 3-4. 해석

최적점 CFG≈2.0, 두 이미지 일치. uncond 분기 미학습(§3-1) 고려 시 표준 CFG
스케일(7.5)은 과도, 이 아키텍처의 적정 구간은 표준 관례보다 낮음. 다음 스윕:
1.5~2.0 사이 세분화(1.75 등) 제안.

---

## 4. 한계 / 다음

- 지난 세션 run5_1/run6_1/run6_2 50장 비교, §3-2 발견(BLD가 matte 안쪽 생성에도
  개입) 적용 여부 재작업 필요 판단 🔴
- §1-4 outlier 개수 계산 필요
- CFG 표본 seed42·이미지 2장·1 seed — 확장 시 판단 안정화
- T15 densify, dose-response 성격 — 낮은 threshold(T12) 확장 시 개선폭 확인 가능
