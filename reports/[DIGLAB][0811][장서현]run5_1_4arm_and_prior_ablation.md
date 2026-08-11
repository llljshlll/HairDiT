# run5_1 4-arm eval + backbone prior ablation (mcs2 vs run5_1)

## 최상단 요약 (10줄 이내)

**지난 미팅 (2026-08-11)** 
- 4-arm(T∞/T15 × w=1/CRG2.0) 확장 평가 설계, 정량 50장×4seed·정성 8장×2버전
- mcs2("CN=전체 내용 지정자") vs run5_1("CN=조향자, backbone prior 활성") 가설 검증

**합의 사항 → 상태**
- [완료] 실험1: 4-arm 정량(50장×4seed) + 정성(8장×GT색/color 스케치)
- [완료] 실험2: mcs2·run5_1 BLD 없음·CRG 없음 8장 비교

**이번 결과**
- 결과: 4-arm 전부 arm4(T15+CRG2.0)가 방향 지표 전 항목 최선(§1.1)
- 결과 : T15/CRG2.0 일 때 정량평가 결과가 가장 좋지만, 정성평가에서는 오히려 T∞/CRG2.0가 더 자연스러워보임(§1.2)
- 결과: run5_1 15epoch로 colorful sketch에 대해 생성했을 때, colorful sketch 무시하고 자연색 생성, run4(40epoch)는 원색 그대로 재현 => epoch 수 늘리면 color 재현할 것으로 예상(§1.3) 
- 결과: run5_1은 BLD·CRG 없이도 matte 밖에 얼굴 구조 생성, mcs2는 격자 텍스처로 붕괴(§2)

---

## 1. 실험 1: 4-arm 평가

"4-arm" = T∞/T15(densify) × w=1/CRG2.0(guidance) 조합 4종 비교.

| arm | densify | guidance | 목적 |
|---|---|---|---|
| 1 | T∞ | w=1 | 기준선 |
| 2 | T15 | w=1 | T15 단독 효과 |
| 3 | T∞ | CRG 2.0 | CRG 단독 효과 |
| 4 | T15 | CRG 2.0 | 결합 — 핵심 arm |

### 1.1 정량평가

**방법**: 50장(GT색 recolor 스케치 T∞ / SHS T15 densify 스케치) × seed{1,2,3,42} ×
run5_1, BLD 포함. 

| arm | GT오차[deg] | coherence | seed불일치[deg] | outlier[/200] | dE_unbraid | lpips_unbraid |
|---|---:|---:|---:|---:|---:|---:|
| 1: T∞/w=1 | 14.95 | 0.769 | 13.14±4.64 | 37 | 4.5783 | 0.2222 |
| 2: T15/w=1 | 14.57 | 0.782 | 12.32±4.50 | 33 | 4.6546 | 0.2175 |
| 3: T∞/CRG2.0 | 13.77 | 0.813 | 10.00±3.15 | 28 | 5.0656 | 0.2208 |
| **4: T15/CRG2.0** | **13.57** | **0.832** | **9.28±3.10** | 33 | 5.1077 | **0.2154** |

**결과**
- 방향 지표 3종(GT오차·coherence·seed불일치), arm1→4 단조 개선: GT오차 -9.2%, coherence
  +8.2%, seed불일치 -29.4%
- dE_unbraid는 반대로 단조 악화(+11.6%) 
- lpips_unbraid는 arm4 최저(0.2154)로 최선, dE와 반대 방향
- outlier, arm3(28) 대비 arm4(33) 소폭 증가 — 방향 정확도 개선과 outlier 억제 불일치
>outlier : 이미지 하나당 4개 seed로 만든 결과들의 GT오차 평균을 구하고, 그 평균보다 1σ 이상 벗어난 (이미지, seed) 조합을 outlier로 셈

### 1.2 정성평가(GT sketch)

**방법**: 기존 8장 sketch 4-arm 각 1회 생성, seed42.

결과 : 3: T∞/CRG2.0가 제일 자연스러워보임

| | CM_1007 | CM_1027 | CM_1033 | CM_1067 | CM_1068 | CM_1082 | CM_1084 | CM_1172 |
|---|---|---|---|---|---|---|---|---|
| GT | <img src="../dataset/img/CM_1007.png" width="100"> | <img src="../dataset/img/CM_1027.png" width="100"> | <img src="../dataset/img/CM_1033.png" width="100"> | <img src="../dataset/img/CM_1067.png" width="100"> | <img src="../dataset/img/CM_1068.png" width="100"> | <img src="../dataset/img/CM_1082.png" width="100"> | <img src="../dataset/img/CM_1084.png" width="100"> | <img src="../dataset/img/CM_1172.png" width="100"> |
| GT색 스케치 | <img src="../data/test/recolor_sketch/CM_1007.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1027.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1033.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1067.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1068.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1082.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1084.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1172.png" width="100"> |
| 1: T∞/w=1 | <img src="../outputs/0811/eval8_gt/T_inf_w1/42/CM_1007.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_w1/42/CM_1027.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_w1/42/CM_1033.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_w1/42/CM_1067.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_w1/42/CM_1068.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_w1/42/CM_1082.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_w1/42/CM_1084.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_w1/42/CM_1172.png" width="100"> |
| 2: T15/w=1 | <img src="../outputs/0811/eval8_gt/T15_w1/42/CM_1007.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_w1/42/CM_1027.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_w1/42/CM_1033.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_w1/42/CM_1067.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_w1/42/CM_1068.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_w1/42/CM_1082.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_w1/42/CM_1084.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_w1/42/CM_1172.png" width="100"> |
| 3: T∞/CRG2.0 | <img src="../outputs/0811/eval8_gt/T_inf_crg2/42/CM_1007.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_crg2/42/CM_1027.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_crg2/42/CM_1033.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_crg2/42/CM_1067.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_crg2/42/CM_1068.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_crg2/42/CM_1082.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_crg2/42/CM_1084.png" width="100"> | <img src="../outputs/0811/eval8_gt/T_inf_crg2/42/CM_1172.png" width="100"> |
| 4: T15/CRG2.0 | <img src="../outputs/0811/eval8_gt/T15_crg2/42/CM_1007.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_crg2/42/CM_1027.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_crg2/42/CM_1033.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_crg2/42/CM_1067.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_crg2/42/CM_1068.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_crg2/42/CM_1082.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_crg2/42/CM_1084.png" width="100"> | <img src="../outputs/0811/eval8_gt/T15_crg2/42/CM_1172.png" width="100"> |

### 1.3 정성평가(color sketch)

**방법**: 동일 8장, sketch를 GT색으로 바꾸지 않고 원본 색(colorful sketch) 그대로 4-arm 생성(run5_1,
epoch15), seed42.

| | CM_1007 | CM_1027 | CM_1033 | CM_1067 | CM_1068 | CM_1082 | CM_1084 | CM_1172 |
|---|---|---|---|---|---|---|---|---|
| color 스케치 | <img src="../data/test/sketch/CM_1007.png" width="100"> | <img src="../data/test/sketch/CM_1027.png" width="100"> | <img src="../data/test/sketch/CM_1033.png" width="100"> | <img src="../data/test/sketch/CM_1067.png" width="100"> | <img src="../data/test/sketch/CM_1068.png" width="100"> | <img src="../dataset/sketch/CM_1082.png" width="100"> | <img src="../data/test/sketch/CM_1084.png" width="100"> | <img src="../data/test/sketch/CM_1172.png" width="100"> |
| 1: T∞/w=1 | <img src="../outputs/0811/eval8_raw/T_inf_w1/42/CM_1007.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_w1/42/CM_1027.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_w1/42/CM_1033.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_w1/42/CM_1067.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_w1/42/CM_1068.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_w1/42/CM_1082.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_w1/42/CM_1084.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_w1/42/CM_1172.png" width="100"> |
| 2: T15/w=1 | <img src="../outputs/0811/eval8_raw/T15_w1/42/CM_1007.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_w1/42/CM_1027.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_w1/42/CM_1033.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_w1/42/CM_1067.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_w1/42/CM_1068.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_w1/42/CM_1082.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_w1/42/CM_1084.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_w1/42/CM_1172.png" width="100"> |
| 3: T∞/CRG2.0 | <img src="../outputs/0811/eval8_raw/T_inf_crg2/42/CM_1007.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_crg2/42/CM_1027.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_crg2/42/CM_1033.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_crg2/42/CM_1067.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_crg2/42/CM_1068.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_crg2/42/CM_1082.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_crg2/42/CM_1084.png" width="100"> | <img src="../outputs/0811/eval8_raw/T_inf_crg2/42/CM_1172.png" width="100"> |
| 4: T15/CRG2.0 | <img src="../outputs/0811/eval8_raw/T15_crg2/42/CM_1007.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_crg2/42/CM_1027.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_crg2/42/CM_1033.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_crg2/42/CM_1067.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_crg2/42/CM_1068.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_crg2/42/CM_1082.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_crg2/42/CM_1084.png" width="100"> | <img src="../outputs/0811/eval8_raw/T15_crg2/42/CM_1172.png" width="100"> |

**관찰**: run5_1, 8장 전부 raw 스케치 원색(녹색·무지개 등) 무시, 자연스러운 갈색·금발
톤으로 생성 — CRG·densify 여부와 무관하게 일관.

run5_1은 epoch15 체크포인트. `[DIGLAB][0730][장서현]
run4_results.md`, `reports/[0726]results_analysis.md`, `reports/[0718]results.md`의 "Colorful sketch" 표를 보면, run2, 3, 4모두에서 epoch30 이후에 색이 뚜렷해지는 관찰 존재 — epoch15
시점에는 색 조건 학습 미완성 가능성 있음. 40epoch까지 학습한 run4로 동일 4-arm 추가 생성(같은 raw
스케치·seed42, T15 densify 스케치는 run5_1과 공유).

| | CM_1007 | CM_1027 | CM_1033 | CM_1067 | CM_1068 | CM_1082 | CM_1084 | CM_1172 |
|---|---|---|---|---|---|---|---|---|
| color 스케치 | <img src="../data/test/sketch/CM_1007.png" width="100"> | <img src="../data/test/sketch/CM_1027.png" width="100"> | <img src="../data/test/sketch/CM_1033.png" width="100"> | <img src="../data/test/sketch/CM_1067.png" width="100"> | <img src="../data/test/sketch/CM_1068.png" width="100"> | <img src="../dataset/sketch/CM_1082.png" width="100"> | <img src="../data/test/sketch/CM_1084.png" width="100"> | <img src="../data/test/sketch/CM_1172.png" width="100"> |
| 1: T∞/w=1 | <img src="../outputs/0811/epoch40_run4_eval8_raw/42/CM_1007.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw/42/CM_1027.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw/42/CM_1033.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw/42/CM_1067.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw/42/CM_1068.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw/42/CM_1082.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw/42/CM_1084.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw/42/CM_1172.png" width="100"> |
| 2: T15/w=1 | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_w1/42/CM_1007.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_w1/42/CM_1027.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_w1/42/CM_1033.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_w1/42/CM_1067.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_w1/42/CM_1068.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_w1/42/CM_1082.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_w1/42/CM_1084.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_w1/42/CM_1172.png" width="100"> |
| 3: T∞/CRG2.0 | <img src="../outputs/0811/epoch40_run4_eval8_raw_Tinf_crg2/42/CM_1007.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_Tinf_crg2/42/CM_1027.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_Tinf_crg2/42/CM_1033.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_Tinf_crg2/42/CM_1067.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_Tinf_crg2/42/CM_1068.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_Tinf_crg2/42/CM_1082.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_Tinf_crg2/42/CM_1084.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_Tinf_crg2/42/CM_1172.png" width="100"> |
| 4: T15/CRG2.0 | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_crg2/42/CM_1007.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_crg2/42/CM_1027.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_crg2/42/CM_1033.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_crg2/42/CM_1067.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_crg2/42/CM_1068.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_crg2/42/CM_1082.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_crg2/42/CM_1084.png" width="100"> | <img src="../outputs/0811/epoch40_run4_eval8_raw_T15_crg2/42/CM_1172.png" width="100"> |

**관찰**: run4(40epoch), 8장 전부 스케치 원색 그대로 재현(무지개색 포함) - run5_1도 epoch 30이후에는 색 적용 될것으로 추정

---

## 2. 실험 2: backbone prior 비교 (mcs2 vs run5_1)

**지침**: mcs2는 학습 당시 timestep 관례가 어긋나 프리즌 DiT prior가 사실상 무력화된 상태였고, 그 빈자리를 ControlNet이 메워 머리 구조를 통째로 만들어낸 것으로 추정(CN=전체 내용 지정자). run5 계열은 이후 timestep을 정상화해 backbone이 직접 생성 엔진 역할을 하고 ControlNet은 완만한 조향자 수준에 그친다는 게 가설.  
검증: BLD·CRG 없이 sketch·matte만 준 상태로 matte 밖(비-헤어) 영역을 비교 — 가설대로라면 run5_1은 자연스러운 얼굴, mcs2는 구조 붕괴로 나와야 함.

**방법**: BLD 없음·, CRG 없음, sketch·matte는 GT색
recolor 스케치로 정상 입력. 8장, seed42. 

### 2.1 결과 이미지

| | CM_1007 | CM_1027 | CM_1033 | CM_1067 | CM_1068 | CM_1082 | CM_1084 | CM_1172 |
|---|---|---|---|---|---|---|---|---|
| GT색 스케치(입력) | <img src="../data/test/recolor_sketch/CM_1007.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1027.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1033.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1067.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1068.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1082.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1084.png" width="100"> | <img src="../data/test/recolor_sketch/CM_1172.png" width="100"> |
| mcs2 | <img src="../outputs/0811/exp2_noCRG_gt/mcs2/42/CM_1007.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/mcs2/42/CM_1027.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/mcs2/42/CM_1033.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/mcs2/42/CM_1067.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/mcs2/42/CM_1068.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/mcs2/42/CM_1082.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/mcs2/42/CM_1084.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/mcs2/42/CM_1172.png" width="100"> |
| run5_1 | <img src="../outputs/0811/exp2_noCRG_gt/run5_1/42/CM_1007.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/run5_1/42/CM_1027.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/run5_1/42/CM_1033.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/run5_1/42/CM_1067.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/run5_1/42/CM_1068.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/run5_1/42/CM_1082.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/run5_1/42/CM_1084.png" width="100"> | <img src="../outputs/0811/exp2_noCRG_gt/run5_1/42/CM_1172.png" width="100"> |

### 2.2 관찰, 해석

- run5_1: 일부 사진 matte 밖 영역에 얼굴 구조 생성(일부 사진은 얼굴이 생성 안되고, matte 바깥이 검정색으로 나타남)
- mcs2: matte 밖 영역, 8장 전부 동일한 격자(lattice) 텍스처로 붕괴. sketch가 달라도 배경
  결과 거의 동일.
- 예측("run5_1 prior 강함 / mcs2 prior 침묵") 방향과 일치

