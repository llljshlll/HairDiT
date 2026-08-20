# SD3.5 ControlNet(Canny) + BLD Density Sketch Seed Test


---

## 1. controlNet

- 사용 모델: tensorart/SD3.5M-Controlnet-Canny — HairDiT처럼 자체 데이터로 새로 학습시킨 것이 아니라, sketch 컨트롤 + 텍스트 프롬프트만으로 사실적인 이미지를 생성하도록 이미 학습되어 커뮤니티에 공개돼 있는 off-the-shelf ControlNet
- 목적: 이런 기성 ControlNet에 density sketch를 컨트롤 이미지로, "사실적인 머리" 계열 프롬프트를 태워 넣었을 때 얼마나 그럴듯한 헤어가 나오는지 정성 평가

| 항목 | 값 |
|---|---|
| Base | stabilityai/stable-diffusion-3.5-medium |
| ControlNet | tensorart/SD3.5M-Controlnet-Canny |
| 배경 유지 | BLD — 매 스텝 matte 바깥을 `(1-σ)·x0_bg+σ·noise`로 블렌딩, decode 후 pixel-space 최종 합성 추가(pixel blending) |
| 컨트롤 이미지 | sketch 원본을 canny로 바꾸지 않고 그대로 사용 |
| controlnet_conditioning_scale | 0.8 (tensorart/SD3.5M-Controlnet-Canny 모델 카드 공식 예시값) |
| 해상도 / step | 512×512 / 30 step (tensorart 모델 카드 공식 예시값) |
| guidance_scale | 4.5 (stabilityai/stable-diffusion-3.5-medium, tensorart 두 모델 카드 공식 예시값 모두 동일) |
| 프롬프트 | `"a photo of a woman with long hair, studio lighting, high quality"` |

**공통 인퍼런스 조건**
- bld, pixel blend 둘 다 run7 mcs2 inference 조건과 똑같이 적용
- `--bld_mode full` — 매 denoising 스텝마다 matte 바깥을 배경의 noised latent로 블렌딩
- `--pixel_blend` — decode 후 pixel-space에서 matte 바깥을 원본 픽셀로 한 번 더 덮어씀(경계 feather=2px)
- `--num_inference_steps 30` (기본값, tensorart 모델 카드 공식 예시값)
- `--prompt "a photo of a woman with long hair, studio lighting, high quality"`
- `--negative_prompt "blurry, low quality, distorted, deformed"`


| sketch | Seed 42 | Seed 1 | Seed 2 | Seed 3 |
|---|---|---|---|---|
| <img src="../data/densified_shs_raw/T15/CM_1067.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_42/CM_1067.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_1/CM_1067.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_2/CM_1067.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_3/CM_1067.png" width="180"> |
| <img src="../data/densified_shs_raw/T15/CM_1068.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_42/CM_1068.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_1/CM_1068.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_2/CM_1068.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_3/CM_1068.png" width="180"> |
| <img src="../data/densified_shs_raw/T15/CM_1033.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_42/CM_1033.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_1/CM_1033.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_2/CM_1033.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_3/CM_1033.png" width="180"> |
| <img src="../data/densified_shs_raw/T15/CM_1082.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_42/CM_1082.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_1/CM_1082.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_2/CM_1082.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_3/CM_1082.png" width="180"> |
| <img src="../data/densified_shs_raw/T15/CM_1084.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_42/CM_1084.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_1/CM_1084.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_2/CM_1084.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_3/CM_1084.png" width="180"> |
| <img src="../data/densified_shs_raw/T15/CM_1172.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_42/CM_1172.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_1/CM_1172.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_2/CM_1172.png" width="180"> | <img src="../outputs/0820/3_density_bldfull_3/CM_1172.png" width="180"> |

seed별로 차이 큼


----
## 2. 배경에 따른 mcs1 / mcs2의 결과 변화

**공통 인퍼런스 조건**
- `--bld_mode full` — 매 denoising 스텝마다 matte 바깥을 배경의 noised latent로 블렌딩(latent 단계 배경 합성)
- `--crg_scale 1.5`
- `--pixel_blend` **미사용**(off) — decode 후 pixel-space 최종 matte blending은 적용 안 함, `vae.decode()` 결과를 그대로 저장

### mcs1

| 배경 | Seed 42 | Seed 1 | Seed 2 | Seed 3 |
|---|---|---|---|---|
| ori — <img src="../dataset/test/img/braid_4156.png" width="90"> | <img src="../outputs/0820/red_test/mcs1_ori/42/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs1_ori/1/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs1_ori/2/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs1_ori/3/braid_4156.png" width="180"> |
| block — <img src="../dataset/test/img/block.png" width="90"> | <img src="../outputs/0820/red_test/mcs1_block/42/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs1_block/1/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs1_block/2/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs1_block/3/braid_4156.png" width="180"> |
| river — <img src="../dataset/test/img/river.png" width="90"> | <img src="../outputs/0820/red_test/mcs1_river/42/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs1_river/1/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs1_river/2/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs1_river/3/braid_4156.png" width="180"> |

### mcs2

| 배경 | Seed 42 | Seed 1 | Seed 2 | Seed 3 |
|---|---|---|---|---|
| ori — <img src="../dataset/test/img/braid_4156.png" width="90"> | <img src="../outputs/0820/red_test/mcs2_ori/42/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs2_ori/1/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs2_ori/2/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs2_ori/3/braid_4156.png" width="180"> |
| block — <img src="../dataset/test/img/block.png" width="90"> | <img src="../outputs/0820/red_test/mcs2_block/42/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs2_block/1/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs2_block/2/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs2_block/3/braid_4156.png" width="180"> |
| river — <img src="../dataset/test/img/river.png" width="90"> | <img src="../outputs/0820/red_test/mcs2_river/42/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs2_river/1/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs2_river/2/braid_4156.png" width="180"> | <img src="../outputs/0820/red_test/mcs2_river/3/braid_4156.png" width="180"> |