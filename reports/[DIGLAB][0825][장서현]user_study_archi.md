user_study에 들어갈 사진을 정하기 위한 리포트

user_study에서는 각 이미지마다 Ours(mcs2)와 4개 baseline(Sketch-only/SHS/HairCLIPv2/VividHair)의 **1:1 비교**로 들어갈 것임
- 총 8개 이미지(braid/unbraid × GT/COLOR = 4조건 × 2세트) 선정 → 이미지 8장 × baseline 4개 = **32세트**
- 문항은 이번엔 4개(Hair Realism / Structure Fidelity / Color Fidelity / **Face Identity** 추가)로 진행 예정

## 숫자 설명
아래 각 이미지 옆 표의 득표수는 `[DIGLAB][0824][장서현]user_study.md`(33명 응답, 문항 3개) 설문에서 **Ours(mcs2)가 받은 득표수**임(분모는 항상 33). 이 득표수가 높은 이미지 위주로 이번 8장 후보를 골랐음.

---

## 1. COLOR · braid

| 이미지 | Hair Realism | Structure Fidelity | Color Fidelity |
|---|---:|---:|---:|
| braid_2562_1_2 | 16/33 | 20/33 | 15/33 |
| braid_4156 | 21/33 | 12/33 | 10/33 |

| 이미지 | sketch | image | Ours(mcs2) | Sketch-only(mcs3) | SHS | HairCLIPv2 | VividHair |
|---|---|---|---|---|---|---|---|
| **braid_2562_1_2** | <img src="../outputs/0825/color/sketch/braid_2562_1_2.png" width="130"> | <img src="../outputs/0825/color/image/braid_2562_1_2.png" width="130"> | <img src="../outputs/0825/color/mcs2/braid_2562_1_2.png" width="130"> | <img src="../outputs/0825/color/mcs3/braid_2562_1_2.png" width="130"> | <img src="../outputs/0825/color/SHS/braid_2562_1_2.png" width="130"> | <img src="../outputs/0825/color/HairCLIPv2/braid_2562_1_2.png" width="130"> | <img src="../outputs/0825/color/VividHair/braid_2562_1_2.png" width="130"> |
| **braid_4156** | <img src="../outputs/0825/color/sketch/braid_4156.png" width="130"> | <img src="../outputs/0825/color/image/braid_4156.png" width="130"> | <img src="../outputs/0825/color/mcs2/braid_4156.png" width="130"> | <img src="../outputs/0825/color/mcs3/braid_4156.png" width="130"> | <img src="../outputs/0825/color/SHS/braid_4156.png" width="130"> | <img src="../outputs/0825/color/HairCLIPv2/braid_4156.png" width="130"> | <img src="../outputs/0825/color/VividHair/braid_4156.png" width="130"> |

## 2. COLOR · unbraid

| 이미지 | Hair Realism | Structure Fidelity | Color Fidelity |
|---|---:|---:|---:|
| CM_1215 | 20/33 | 16/33 | 12/33 |
| CM_1007 | 22/33 | 23/33 | 18/33 |

| 이미지 | sketch | image | Ours(mcs2) | Sketch-only(mcs3) | SHS | HairCLIPv2 | VividHair |
|---|---|---|---|---|---|---|---|
| **CM_1215** | <img src="../outputs/0825/color/sketch/CM_1215.png" width="130"> | <img src="../outputs/0825/color/image/CM_1215.png" width="130"> | <img src="../outputs/0825/color/mcs2/CM_1215.png" width="130"> | <img src="../outputs/0825/color/mcs3/CM_1215.png" width="130"> | <img src="../outputs/0825/color/SHS/CM_1215.png" width="130"> | <img src="../outputs/0825/color/HairCLIPv2/CM_1215.png" width="130"> | <img src="../outputs/0825/color/VividHair/CM_1215.png" width="130"> |
| **CM_1007** | <img src="../outputs/0825/color/sketch/CM_1007.png" width="130"> | <img src="../outputs/0825/color/image/CM_1007.png" width="130"> | <img src="../outputs/0825/color/mcs2/CM_1007.png" width="130"> | <img src="../outputs/0825/color/mcs3/CM_1007.png" width="130"> | <img src="../outputs/0825/color/SHS/CM_1007.png" width="130"> | <img src="../outputs/0825/color/HairCLIPv2/CM_1007.png" width="130"> | <img src="../outputs/0825/color/VividHair/CM_1007.png" width="130"> |

## 3. GT · braid

**braid_2548으로 확정.** GT 조건은 이전 투표에서 Ours가 전반적으로 낮게 나와서(아래 4번 참고), 이전에 썼던 이미지를 그대로 재사용하기보다 **새 후보(braid_4276)를 하나 더 추가로 제시** 

| 이미지 | 상태 | Hair Realism | Structure Fidelity | Color Fidelity |
|---|---|---:|---:|---:|
| braid_2548 | 확정 | 18/33 | 18/33 | 14/33 |
| braid_4276 | 신규 후보 (GT로는 미평가, COLOR로는 24/25/17) | — | — | — |

| 이미지 | sketch | image | Ours(mcs2) | Sketch-only(mcs3) | SHS | HairCLIPv2 | VividHair |
|---|---|---|---|---|---|---|---|
| **braid_2548** | <img src="../outputs/0825/gt/sketch/braid_2548.png" width="130"> | <img src="../outputs/0825/gt/image/braid_2548.png" width="130"> | <img src="../outputs/0825/gt/mcs2/braid_2548.png" width="130"> | <img src="../outputs/0825/gt/mcs3/braid_2548.png" width="130"> | <img src="../outputs/0825/gt/SHS/braid_2548.png" width="130"> | <img src="../outputs/0825/gt/HairCLIPv2/braid_2548.png" width="130"> | <img src="../outputs/0825/gt/VividHair/braid_2548.png" width="130"> |
| **braid_4276** | <img src="../outputs/0825/gt/sketch/braid_4276.png" width="130"> | <img src="../outputs/0825/gt/image/braid_4276.png" width="130"> | <img src="../outputs/0825/gt/mcs2/braid_4276.png" width="130"> | <img src="../outputs/0825/gt/mcs3/braid_4276.png" width="130"> | <img src="../outputs/0825/gt/SHS/braid_4276.png" width="130"> | <img src="../outputs/0825/gt/HairCLIPv2/braid_4276.png" width="130"> | <img src="../outputs/0825/gt/VividHair/braid_4276.png" width="130"> |

## 4. GT · unbraid

GT·unbraid는 이전 투표에서 **Ours가 4조건 중 가장 약했던 조합**(unbraid(GT) 요약 참고: Hair Realism 3위/16.2%, SHS·HairCLIPv2보다는 위지만 Sketch-only·VividHair보다 낮음). 그래서 **아직 평가된 적 없는 신규 후보 3장**을 추가로 제시 — 이 중에서 더 나은 걸 고를지, CM_1067_12를 그대로 쓸지 결정해야함

| 이미지 | 상태 | Hair Realism | Structure Fidelity | Color Fidelity |
|---|---|---:|---:|---:|
| CM_1067_12 | GT·unbraid 중 Ours 최고 득표 | 9/33 | 14/33 | 10/33 |
| CM_1172 | 신규 후보 (미평가) | — | — | — |
| CM_1133 | 신규 후보 (GT로는 미평가, COLOR로는 17/16/10) | — | — | — |
| CM_1077 | 신규 후보 (미평가) | — | — | — |

| 이미지 | sketch | image | Ours(mcs2) | Sketch-only(mcs3) | SHS | HairCLIPv2 | VividHair |
|---|---|---|---|---|---|---|---|
| **CM_1067_12** | <img src="../outputs/0825/gt/sketch/CM_1067_12.png" width="130"> | <img src="../outputs/0825/gt/image/CM_1067_12.png" width="130"> | <img src="../outputs/0825/gt/mcs2/CM_1067_12.png" width="130"> | <img src="../outputs/0825/gt/mcs3/CM_1067_12.png" width="130"> | <img src="../outputs/0825/gt/SHS/CM_1067_12.png" width="130"> | <img src="../outputs/0825/gt/HairCLIPv2/CM_1067_12.png" width="130"> | <img src="../outputs/0825/gt/VividHair/CM_1067_12.png" width="130"> |
| **CM_1172** | <img src="../outputs/0825/gt/sketch/CM_1172.png" width="130"> | <img src="../outputs/0825/gt/image/CM_1172.png" width="130"> | <img src="../outputs/0825/gt/mcs2/CM_1172.png" width="130"> | <img src="../outputs/0825/gt/mcs3/CM_1172.png" width="130"> | <img src="../outputs/0825/gt/SHS/CM_1172.png" width="130"> | <img src="../outputs/0825/gt/HairCLIPv2/CM_1172.png" width="130"> | <img src="../outputs/0825/gt/VividHair/CM_1172.png" width="130"> |
| **CM_1133** | <img src="../outputs/0825/gt/sketch/CM_1133.png" width="130"> | <img src="../outputs/0825/gt/image/CM_1133.png" width="130"> | <img src="../outputs/0825/gt/mcs2/CM_1133.png" width="130"> | <img src="../outputs/0825/gt/mcs3/CM_1133.png" width="130"> | <img src="../outputs/0825/gt/SHS/CM_1133.png" width="130"> | <img src="../outputs/0825/gt/HairCLIPv2/CM_1133.png" width="130"> | <img src="../outputs/0825/gt/VividHair/CM_1133.png" width="130"> |
| **CM_1077** | <img src="../outputs/0825/gt/sketch/CM_1077.png" width="130"> | <img src="../outputs/0825/gt/image/CM_1077.png" width="130"> | <img src="../outputs/0825/gt/mcs2/CM_1077.png" width="130"> | <img src="../outputs/0825/gt/mcs3/CM_1077.png" width="130"> | <img src="../outputs/0825/gt/SHS/CM_1077.png" width="130"> | <img src="../outputs/0825/gt/HairCLIPv2/CM_1077.png" width="130"> | <img src="../outputs/0825/gt/VividHair/CM_1077.png" width="130"> |
