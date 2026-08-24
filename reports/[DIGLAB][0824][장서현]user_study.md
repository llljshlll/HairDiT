## 통계 방법

- **비교 모델(5개)**: Sketch-only(mcs3) / SHS(SketchHairSalon) / HairCLIPv2 / VividHair(VividHairStyler) / **Ours**(gated, mcs2)
- **문항(세트당 3개)**: Hair Realism / Structure Fidelity / Color Fidelity
    - 입력 스케치를 참고했을 때, 머리카락이 가장 자연스럽고 실제처럼 보이는 결과를 선택해 주세요.
    - 입력 스케치와 비교했을 때, 머리 모양과 머릿결의 방향을 가장 잘 따라간 결과를 선택해 주세요.
    - 입력 스케치와 비교했을 때, 머리카락 색을 가장 잘 따라간 결과를 선택해 주세요.
- **세트**: 총 20세트 = GT 10세트(braid 5 / unbraid 5) + COLOR 10세트(braid 4 / unbraid 6)
- **응답자**: 33명
- **공정성 확보**: 세트마다 5개 모델을 A~E로 랜덤 셔플해 제시. → 집계는 실제 모델명을 복원한 뒤 집계함.
- **% 계산**: 그룹별 각 문항의 모델별 득표수 ÷ (그룹 세트 수 × 33명). 예) braid(GT)는 5세트 × 33명 = 165표가 분모.

## 전체 결과
(20세트 × 33명 = 660표/문항)

| Method      | Hair Realism ↑ | Structure Fidelity ↑ | Color Fidelity ↑ |
| ----------- | -------------: | -------------------: | ---------------: |
| Sketch-only |           27.3% |                 36.7% |             44.8% |
| SHS         |            7.3% |                 10.6% |             13.8% |
| HairCLIPv2  |           11.4% |                  5.2% |              4.2% |
| VividHair   |           15.2% |                  8.5% |              8.6% |
| Ours        |       **38.9%** |             **39.1%** |         **28.5%** |

Hair Realism, Structure Fidelity는 Ours(mcs2)가 1위  
Color Fidelity는 Sketch-only(mcs3)가 1위


## 개별 결과

### braid(GT)
(5세트 × 33명 = 165표/문항)

| Method      | Hair Realism ↑ | Structure Fidelity ↑ | Color Fidelity ↑ |
| ----------- | -------------: | -------------------: | ---------------: |
| Sketch-only |           47.3% |                 51.5% |             55.8% |
| SHS         |            9.7% |                 13.3% |             12.7% |
| HairCLIPv2  |            5.5% |                  3.6% |              2.4% |
| VividHair   |            9.1% |                  0.0% |              2.4% |
| Ours        |       **28.5%** |             **31.5%** |         **26.7%** |


### braid(COLOR)
(4세트 × 33명 = 132표/문항)

| Method      | Hair Realism ↑ | Structure Fidelity ↑ | Color Fidelity ↑ |
| ----------- | -------------: | -------------------: | ---------------: |
| Sketch-only |           17.4% |                 25.0% |             43.9% |
| SHS         |            6.8% |                 12.9% |             17.4% |
| HairCLIPv2  |            6.8% |                  1.5% |              1.5% |
| VividHair   |            5.3% |                  2.3% |              0.8% |
| Ours        |       **63.6%** |             **58.3%** |         **36.4%** |

### unbraid(GT)
(5세트 × 33명 = 165표/문항)

| Method      | Hair Realism ↑ | Structure Fidelity ↑ | Color Fidelity ↑ |
| ----------- | -------------: | -------------------: | ---------------: |
| Sketch-only |           26.7% |                 34.5% |             33.9% |
| SHS         |            6.7% |                  9.7% |             10.3% |
| HairCLIPv2  |           14.5% |                  9.7% |             10.9% |
| VividHair   |           38.2% |                 24.2% |             24.8% |
| Ours        |       **13.9%** |             **21.8%** |         **20.0%** |


### unbraid(COLOR)
(6세트 × 33명 = 198표/문항)

| Method      | Hair Realism ↑ | Structure Fidelity ↑ | Color Fidelity ↑ |
| ----------- | -------------: | -------------------: | ---------------: |
| Sketch-only |           17.7% |                 33.8% |             45.5% |
| SHS         |            6.1% |                  7.6% |             15.2% |
| HairCLIPv2  |           16.7% |                  5.1% |              2.0% |
| VividHair   |            7.6% |                  6.6% |              5.6% |
| Ours        |       **52.0%** |             **47.0%** |         **31.8%** |

## 요약
- **전체**적으로는 Ours가 Hair Realism·Structure Fidelity 1위(각 38.9%/39.1%), Color Fidelity는 Sketch-only가 1위(44.8%, Ours 28.5%로 2위) — Sketch-only/SHS/HairCLIPv2/VividHair 대비 Ours가 대체로 우세하지만 색상 재현만큼은 gating 없는 Sketch-only가 근소하게 더 좋은 평가를 받음.
- **COLOR 세트(braid/unbraid 모두**)에서는 Ours가 Hair Realism·Structure Fidelity에서 압도적 1위(braid 63.6%/58.3%, unbraid 52.0%/47.0%) — 색상 스케치가 입력으로 주어질 때 Ours의 이득이 가장 크게 나타남.
- **braid(GT**)에서도 Ours가 전 문항 2위권으로 준수하나, Sketch-only가 3문항 모두 1위(47.3~55.8%)로 가장 강세.
- **unbraid(GT)에서만 Ours가 4개 조합 중 유일하게 열세** — Hair Realism은 VividHair(38.2%) > Sketch-only(26.7%) > HairCLIPv2(14.5%) > **Ours(13.9%)** > SHS 순으로 Ours가 최하위권까지 밀림. Structure·Color Fidelity는 Ours가 2위이나 Sketch-only(34.5%/33.9%)에 못 미침. 
- 종합하면 SHS·HairCLIPv2는 전 조합에서 하위권(대부분 5~15%)에 머무르고, VividHair는 unbraid(GT)에서만 예외적으로 두드러진 강세(Hair Realism 1위)를 보임.


### 사용한 이미지 그리드 모음

각 세트는 위쪽 sketch(입력) + 아래 A-E 5분할 결과 그리드로 구성. A-E와 실제 모델 매핑은 세트마다 랜덤이며, 아래 "정답 키"에 표시.

#### 1. GT · unbraid · CM_1121
- 정답 키: A=Ours, B=Sketch-only, C=VividHair, D=HairCLIPv2, E=SHS

<img src="../outputs/0824/user_study/gt/grid/CM_1121.png" alt="1. GT - CM_1121 - unbraid" width="480">

#### 2. COLOR · unbraid · CM_1028
- 정답 키: A=Sketch-only, B=Ours, C=VividHair, D=SHS, E=HairCLIPv2

<img src="../outputs/0824/user_study/color/grid/CM_1028.png" alt="2. COLOR - CM_1028 - unbraid" width="480">

#### 3. GT · braid · braid_2548
- 정답 키: A=HairCLIPv2, B=SHS, C=Ours, D=VividHair, E=Sketch-only

<img src="../outputs/0824/user_study/gt/grid/braid_2548.png" alt="3. GT - braid_2548 - braid" width="480">

#### 4. COLOR · unbraid · CM_1055
- 정답 키: A=Sketch-only, B=SHS, C=HairCLIPv2, D=VividHair, E=Ours

<img src="../outputs/0824/user_study/color/grid/CM_1055.png" alt="4. COLOR - CM_1055 - unbraid" width="480">

#### 5. COLOR · braid · braid_2562_1_2
- 정답 키: A=Sketch-only, B=HairCLIPv2, C=VividHair, D=SHS, E=Ours

<img src="../outputs/0824/user_study/color/grid/braid_2562_1_2.png" alt="5. COLOR - braid_2562_1_2 - braid" width="480">

#### 6. GT · braid · braid_3276
- 정답 키: A=Sketch-only, B=HairCLIPv2, C=VividHair, D=SHS, E=Ours

<img src="../outputs/0824/user_study/gt/grid/braid_3276.png" alt="6. GT - braid_3276 - braid" width="480">

#### 7. COLOR · unbraid · CM_1133
- 정답 키: A=SHS, B=VividHair, C=Sketch-only, D=Ours, E=HairCLIPv2

<img src="../outputs/0824/user_study/color/grid/CM_1133.png" alt="7. COLOR - CM_1133 - unbraid" width="480">

#### 8. GT · braid · CM_1067_12
- 정답 키: A=Ours, B=HairCLIPv2, C=SHS, D=VividHair, E=Sketch-only

<img src="../outputs/0824/user_study/gt/grid/CM_1067_12.png" alt="8. GT - CM_1067_12 - braid" width="480">

#### 9. COLOR · braid · braid_4276
- 정답 키: A=VividHair, B=HairCLIPv2, C=Ours, D=SHS, E=Sketch-only

<img src="../outputs/0824/user_study/color/grid/braid_4276.png" alt="9. COLOR - braid_4276 - braid" width="480">

#### 10. COLOR · braid · braid_4212
- 정답 키: A=VividHair, B=HairCLIPv2, C=Sketch-only, D=SHS, E=Ours

<img src="../outputs/0824/user_study/color/grid/braid_4212.png" alt="10. COLOR - braid_4212 - braid" width="480">

#### 11. COLOR · unbraid · CM_1215
- 정답 키: A=SHS, B=HairCLIPv2, C=VividHair, D=Sketch-only, E=Ours

<img src="../outputs/0824/user_study/color/grid/CM_1215.png" alt="11. COLOR - CM_1215 - unbraid" width="480">

#### 12. GT · unbraid · CM_1027
- 정답 키: A=HairCLIPv2, B=VividHair, C=Ours, D=Sketch-only, E=SHS

<img src="../outputs/0824/user_study/gt/grid/CM_1027.png" alt="12. GT - CM_1027 - unbraid" width="480">

#### 13. GT · unbraid · CM_1151
- 정답 키: A=Ours, B=HairCLIPv2, C=SHS, D=VividHair, E=Sketch-only

<img src="../outputs/0824/user_study/gt/grid/CM_1151.png" alt="13. GT - CM_1151 - unbraid" width="480">

#### 14. COLOR · unbraid · CM_1139
- 정답 키: A=VividHair, B=Ours, C=Sketch-only, D=HairCLIPv2, E=SHS

<img src="../outputs/0824/user_study/color/grid/CM_1139.png" alt="14. COLOR - CM_1139 - unbraid" width="480">

#### 15. GT · braid · wavy_753
- 정답 키: A=Sketch-only, B=HairCLIPv2, C=Ours, D=SHS, E=VividHair

<img src="../outputs/0824/user_study/gt/grid/wavy_753.png" alt="15. GT - wavy_753 - braid" width="480">

#### 16. GT · unbraid · CM1033
- 정답 키: A=VividHair, B=HairCLIPv2, C=SHS, D=Ours, E=Sketch-only

<img src="../outputs/0824/user_study/gt/grid/CM_1033.png" alt="16. GT - CM1033 - unbraid" width="480">

#### 17. COLOR · braid · braid_4156
- 정답 키: A=Ours, B=Sketch-only, C=VividHair, D=SHS, E=HairCLIPv2

<img src="../outputs/0824/user_study/color/grid/braid_4156.png" alt="17. COLOR - braid_4156 - braid" width="480">

#### 18. GT · unbraid · CM_1009
- 정답 키: A=Ours, B=HairCLIPv2, C=VividHair, D=SHS, E=Sketch-only

<img src="../outputs/0824/user_study/gt/grid/CM_1009.png" alt="18. GT - CM_1009 - unbraid" width="480">

#### 19. COLOR · unbraid · CM_1007
- 정답 키: A=Ours, B=VividHair, C=SHS, D=Sketch-only, E=HairCLIPv2

<img src="../outputs/0824/user_study/color/grid/CM_1007.png" alt="19. COLOR - CM_1007 - unbraid" width="480">

#### 20. GT · braid · wavy_749
- 정답 키: A=Ours, B=HairCLIPv2, C=Sketch-only, D=VividHair, E=SHS

<img src="../outputs/0824/user_study/gt/grid/wavy_749.png" alt="20. GT - wavy_749 - braid" width="480">
