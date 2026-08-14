# [0814] run8 soft gate — 코드 수정 사양서

> **[구현 완료 2026-08-14]** §3~§5 전부 `main`에 적용됨. §6 검증 V1~V6 통과(결과는 §6에 인라인).
> 남은 것은 §7 서버 확인 → 학습 착수 → §8 오프라인 스윕.
>
> 대상: `planning/[0814]run8_soft_gate_plan.md`의 "코드 변경" 절을 실제 코드에 맞춰 확정한 문서.
> 계획서가 **무엇을/왜**라면, 이 문서는 **어디를/정확히 어떻게**다. 구현할 때는 이 문서만 보고
> 아래 §2 화이트리스트 밖의 파일·라인은 한 줄도 건드리지 않는다.
>
> **기준 브랜치: `main` (HEAD `675aad9` "EMA를 학습 파이프라인에서 완전히 제거", 2026-08-14)**
> `scripts/infer_custom.py`의 feathering 수정분(미커밋 `M`)이 워킹트리에 있는 상태를 전제한다.
> 라인 번호는 이 상태 기준이며, 앵커는 라인 번호가 아니라 **인용된 문자열**로 잡는다.

---

## 0. 확정된 결정

| # | 항목 | 결정 |
|---|---|---|
| D1 | gate off 추론 수단 | `scripts/infer_custom.py`에 `--gate_alpha` CLI 인자 추가 (default None = config 값 사용) |
| D2 | 오프라인 스윕 CRG | **전부 CRG 1.5로 통일** (last_test.md 최신 기준). 계획서의 "CRG 2.0"은 폐기 |
| D3 | 중간평가 | `_validate` / `_perceptual_validate` 둘 다 off (계획서 §중간평가 그대로) |
| D4 | `a` 난수원 | 계획서의 `random.random()` 대신 **`torch.rand`** (§1-A1) |
| D5 | BLD | **전 스텝 블렌딩** — `--bld_soft_steps` **미지정**(= 20 step 전부 블렌딩). run7의 `18`은 승계하지 않음 |
| D6 | 학습 시드 | **미고정 유지**(run4~run7 관행 그대로). 전역 `seed` config 키는 추가하지 않음 |
| D7 | gate 난수원 | **전용 `torch.Generator`**(`self._gate_rng`). 전역 RNG를 소비하면 `DataLoader(shuffle=True)`의 다음 epoch base seed까지 밀려 **데이터 순서가 run7과 달라진다** — gate 외 변수가 하나 더 생기므로 분리한다 (§0-C) |

---

## 0-B. 🔴 브랜치 재검증 (2026-08-14, `run5-ablation-split` → `main` 전환 후)

이 사양서의 **코드 앵커 9개는 main에서도 문자열이 전부 일치**한다(라인 번호만 trainer.py에서
13줄씩 당겨짐 — 아래 표에 main 기준으로 갱신 반영). 다만 **main은 run7이 실제로 학습된
코드(`run5-ablation-split`)와 다르다**. 확인된 차이 6건:

| # | 차이 | 학습 거동 영향 | 조치 |
|---|---|---|---|
| B1 | `HairLoss`에서 `lpips_gate` / `lpips_warmup_frac` 인자 **삭제**, noise gate가 하드코딩됨 | **없음** — run7은 `lpips_gate: noise`로 돌았고 main의 하드코딩이 정확히 그 경로다 | config의 `lpips_gate: noise` 키는 main에서 **조용히 무시**된다. 키는 남기되 주석으로 표시 (§5) |
| B2 | `self.torch_seed = torch.initial_seed()` 기록 + `run_meta.jsonl` **삭제** | 없음(기록만) | main에는 **시드 기록이 아예 없다**. §3-5 주석 문구를 이에 맞게 수정했고, §9-3에 리포트 caveat로 남김 |
| B3 | `grad_norm` / `grad_clipped` 로깅 **삭제** (`clip_grad_norm_` 호출 자체는 동일) | 없음(기록만) | run7에 있던 진단 로그가 run8엔 없다. 복구는 이번 범위 밖 |
| B4 | `configs/run5_1_noisegate_phase1.yaml`, `run5_2_*`, `run6_*` 가 main에 **없음** | — | §6-V2 하위호환 테스트 대상에서 제외 |
| B5 | `configs/run7_phase2_rawstart.yaml` / `_resume.yaml` 이 main에 **있음** | — | **run8_phase2의 템플릿은 `run7_phase2.yaml`이 아니라 `run7_phase2_rawstart.yaml`이다**(전자는 EMA 시작 버그로 실패한 1차 시도). §5-2 전면 반영 |
| B6 | `configs/run7_phase1.yaml` | main·branch 동일 | 그대로 템플릿 사용 |

**결론**: 학습 수식·데이터·게이트 경로는 main == run7 실행 코드다(B1이 유일한 loss 관련 차이인데
동작이 같다). 잃은 것은 **진단 로그 2종(seed 기록, grad_norm)** 뿐이다. → 이 사양서는 main에서
**유효하다**. 단 §5-2(phase2 config)는 rawstart 기준으로 다시 썼으니 갱신본을 쓸 것.

### B7 🔴 추가 발견 — `early_stopping` 기본값은 `True`다
`trainer.py:181` `config["training"].get("early_stopping", True)`. run7_phase2 1차 시도가 실제로
epoch15에서 조기종료됐고, 그래서 `run7_phase2_rawstart.yaml`에는
`early_stopping: false  # [0813] 기본값 True라 명시 필수`가 들어 있다.
run8은 `midtrain_eval: false`라 조기종료 블록 자체가 실행되지 않지만, **양 phase config에
`early_stopping: false`를 명시**한다(초판 사양서의 phase2 config에서 누락돼 있던 항목).

---

## 0-C. run7 대비 실제로 바뀌는 것 — 전량

"gate dropout 말고는 아무것도 안 바뀌나?"에 대한 정확한 답. **학습 조건(loss·데이터·
하이퍼파라미터·시작 가중치)은 gate 하나만 다르다.** 그 밖에 4가지가 더 다르다.

| 축 | run7 | run8 | 학습 수식 영향 |
|---|---|---|---|
| **gate** | 고정 `a=1.0` | `a ~ Bernoulli(0.5)`, iteration당 1회 | **의도된 변경(유일)** |
| loss / 데이터 / LR / batch / epoch / 시작 가중치 | — | 전부 동일 | 없음 |
| 중간평가 | `_validate` + `_perceptual_validate` 실행 | 둘 다 off | **없음** (아래 ※) |
| 코드 브랜치 | `run5-ablation-split` | `main` | 없음 — 진단 로그 2종만 손실 (§0-B) |
| 평가 조건 | CRG 2.0 + `bld_soft_steps 18` | CRG 1.5 + 전 스텝 | 학습 무관. run7 표와 직접 비교 불가 (§8-2) |
| 학습 시드 | 미고정 | 미고정 (D6) | n=1이라 gate/시드 기여 분리 불가 |

**※ 중간평가 제거와 난수열** — 여기가 미묘하다. `_validate()`는 val_loader 전체에 대해
`_sample_sigmas()`(CUDA `torch.normal`)와 `torch.randn_like()`를 돌려 **전역 CUDA RNG를 소비한다**.
이걸 빼면 그 이후 학습 step이 받는 난수가 달라진다(phase1은 epoch 10/20/30/40의 4개 지점,
phase2는 8개 지점부터). 학습 수식은 그대로지만 궤적은 갈린다.
`_perceptual_validate()`와 `select_fixed_indices()`는 **로컬 `torch.Generator`만** 쓰므로 전역
RNG를 건드리지 않는다(코드 확인 완료) — 난수열에 영향 없다.
→ 어차피 학습 시드가 미고정(D6)이라 run7과 run8은 처음부터 다른 난수열이다. 실질 영향은 없다.

**gate 추첨을 전역 RNG에서 뽑지 않는 이유(D7)** — 만약 `torch.rand(())`를 전역에서 뽑으면
`DataLoader(shuffle=True)`가 매 epoch iterator 생성 시 쓰는 base seed(`torch.empty(...).random_()`,
generator=None → 전역 CPU 생성기)까지 밀려서 **epoch 2부터 데이터 순서가 달라진다**. 이건 시드
고정 여부와 무관하게 발생하는, gate와 무관한 두 번째 변수다. 전용 Generator로 분리하면 전역
RNG 소비가 0이 되어 이 오염이 사라진다(§6-V4b에서 실측 확인).

**엄밀한 단일변수 비교를 원한다면** 전역 시드를 고정하고 `gate_mode: fixed` / `soft` 두 팔을
같은 시드로 돌리면 된다 — D7 덕분에 두 팔의 노이즈·sigma·데이터 순서가 bit-identical해진다.
이번에는 시드 미고정(D6)이라 그 비교는 하지 않는다. 리포트에 caveat로 남긴다(§9-3).

---

## 1. 원 계획서 검증 결과 — 그대로 구현하면 깨지는 것 8건

계획서의 방향(gate dropout, 중간평가 제거, EMA 현상 유지)은 현재 코드와 **타당하다**. 다만
아래는 그대로 옮기면 실패하거나 목적을 달성하지 못한다.

### A1. `random`이 import되어 있지 않다 → `NameError`
계획서 §코드변경 2는 `random.random()`을 쓴다. `src/training/trainer.py`의 import 블록
(`trainer.py:32-53`)에 `random`이 없다 → 첫 step에서 즉사.

**단순 import 추가로 고치지 않는다.** 이 파이프라인의 난수는 전부 torch 스트림이다(노이즈,
sigma, DataLoader shuffle). `torch.rand`를 쓰면 `torch.manual_seed` 하나로 gate 시퀀스까지 함께
재현되지만, `random` 모듈은 그 시드가 지배하지 않는 **별도 스트림**이라 gate 시퀀스만 영원히
복원 불가가 된다. → D4. (main에는 시드 기록조차 없다 — §0-B B2)

### A2. `midtrain_eval`을 읽는 위치가 어긋나면 `AttributeError`
`_setup_perceptual_eval()`은 `__init__` **130행**에서 호출된다. 반면 비슷한 성격의 플래그인
`self.early_stopping`은 **181행**(호출보다 뒤)에서 읽힌다. 여기를 따라 `midtrain_eval`을 181행
근처에 두면 130행의 `if self.midtrain_eval:`이 미정의 속성을 참조해 즉시 죽는다.
→ 반드시 **104-111행 블록**(`self.gate_alpha` 바로 아래)에 둔다.

### A3. `log_dict["gate_a"] = a`를 게이트 호출부에 쓰면 `NameError`
`log_dict`는 `self.loss_fn(...)`이 **반환**하는 값이라 `trainer.py:648` 이전에는 존재하지 않는다.
게이트 샘플링은 624행 이전이어야 하므로, `a`는 지역변수로 들고 있다가 **함수 말미
(`densify_t` 로깅 옆, 727행)** 에서 `log_dict`에 넣는다.

### A4. `_perceptual_validate` 호출부는 2곳 — 하나만 놓쳐도 1 epoch 뒤에 죽는다
`_setup_perceptual_eval()`을 스킵하면 `self._pval_unbraid` / `self._pval_braid` 자체가 없다.
호출부는 ① `train()` 시작부 epoch-0 baseline(480행) ② `perceptual_every` 블록(534행) 두 곳인데,
②는 **epoch 1이 끝난 뒤**(phase1 기준 수십 분~1시간 뒤) 처음 터지므로 스모크 테스트로 안 잡힌다.
→ 호출부 2곳을 막는 것에 더해 `_perceptual_validate` **자체에 조기 return 가드**를 넣는다(이중 방어).

### A5. `--gate_alpha` CLI가 없어서 run8의 목적 자체를 실행할 수 없다
`scripts/infer_custom.py:608`은 `gate_alpha`를 **YAML에서만** 읽는다. 즉 현재 코드로는
"gate on/off 추론 비교"(last_test.md 훈련 방침의 합격 조건)를 config 파일을 갈아끼우지 않고는
할 수 없다. → D1. 참고로 `gate_alpha=0.0`이면 게이트는
`gate = 0·m̃ + 1 = 1`이 되어 `schedule="none"`과 **수치적으로 완전히 동일**하다(bf16에서 ×1.0은
정확 연산). 인자 하나로 on/off/중간값이 전부 커버된다.

### A6. 오프라인 스윕 조건이 문서마다 불일치
- 계획서: "CRG 2.0 + BLD"
- run7 실제 선정 표(`reports/[DIGLAB][0812][장서현]run7_phase1_result.md` §정량지표):
  `--crg_scale 2.0 --bld_mode full --bld_soft_steps 18 --recolor_from_gt`
- last_test.md(최신): "CRG **1.5** + BLD full(step 20) + **Pixel Matte-Blend** + Feathering **0**"

계획서는 `--bld_soft_steps` / `--recolor_from_gt` / `--pixel_blend`를 아예 누락했다.
→ D2(CRG 1.5) + D5(soft_steps 미지정)로 확정. 커맨드 전문은 §8.
**부작용**: 조건이 run7 표(CRG 2.0 / soft_steps 18)와 두 군데 달라졌으므로, run7과 숫자를
나란히 놓으려면 **run7 채택 체크포인트도 동일 조건으로 재측정**해야 한다(§8-2).

### A7. 계획서의 사실관계 오류 — run7은 이미 오프라인으로 epoch을 골랐다
계획서는 "run7까지는 in-loop perceptual_validate 로그로 phase 이관 epoch을 사후 선정했다"고
적었다. 실제로는 run7_phase1 리포트의 선정 표가 **n=50 · seed 4개 · CRG+BLD 오프라인 스윕**
결과이고, 선정 기준인 방향 지표(GT 오차·coherence·seed 불일치)는 `_perceptual_validate`가
**계산하지도 않는 지표**다(그 함수는 dE/lpips/edge_iou만 낸다).
→ 결론(중간평가 제거)은 오히려 더 강해진다. 다만 run8은 "새 방법론"이 아니라 **run7이 이미
쓰던 방식의 명시화**라고 리포트에 적어야 한다.

### A8. 스윕에 필요한 스크립트가 계획서에 하나 빠졌다
계획서 §실행순서 4는 "`infer_custom.py` + `eval_metrics.py`"라고만 쓰는데, 선정 기준 1순위인
방향 지표는 `scripts/eval_metrics.py`에 **없다**(`ALL_METRICS` 확인). `scripts/eval/orientation_metric.py`가
따로 필요하고, 이 파일은 `RUNS` dict에 경로가 하드코딩돼 있어(`orientation_metric.py:29-33`)
run8 엔트리 추가가 필요하다. §8-3 O2.

### 부수 확인 (문제 없음, 기록용)
- `gate_block_samples`는 `gate_alpha`를 스칼라로 받고 `[0,1]` 범위검사를 한다
  (`controlnet_sd35.py:437`) → **per-batch 스칼라만 지원**. 계획서의 "iteration당 1회(샘플 단위
  아님)"는 코드와 일치하며, per-sample로 바꾸려면 `controlnet_sd35.py`를 고쳐야 하므로 하지 않는다.
- `gradient_accumulation_steps`는 `configs/base.yaml:7`에서 **1** → optimizer step 1회당 `a` 1회.
- EMA는 main의 trainer.py에서 완전히 제거됐고, `resume_from` 자리에 **재발 방지 주석**이
  들어가 있다(`trainer.py:278-294`). 계획서 §EMA "별도 변경 불필요"는 사실이다.
  ⚠️ 그 주석 블록은 삭제·요약 금지 — 같은 버그가 두 번 재발한 이력이 있다.
- `_perceptual_validate`는 `scripts.infer_custom`을 import하는데, 이 모듈은 최근 최상단에
  `import kornia.filters as KF`가 추가됐다(feathering 수정, 미커밋). 학습 env에 kornia가 없으면
  **run7에는 없던 새 크래시 경로**가 생긴다. `midtrain_eval: false`면 이 import 자체가 실행되지
  않으므로 이번 변경으로 위험이 사라진다(부수 이득).

---

## 2. 변경 범위 — 화이트리스트

**수정해도 되는 파일 (이 3개뿐)**
1. `src/training/trainer.py` — hunk 7개, 아래 §3
2. `scripts/infer_custom.py` — hunk 2개, 아래 §4
3. `configs/run8_phase1.yaml`, `configs/run8_phase2.yaml` — **신규 생성**

**절대 건드리지 말 것 (명시적 금지)**
- `src/models/controlnet_sd35.py` — `gate_block_samples`는 이미 `a ∈ [0,1]` 스칼라를 받게 설계돼
  있어 수정 불필요. 손대면 run1~7 전체가 재현 불가가 된다.
- `src/training/losses.py`, `src/data/**` — soft gate는 loss·데이터와 무관하다.
  특히 main에서 이미 제거된 `lpips_gate` 토글을 "config에 있으니 되살리자"고 **복구하지 말 것**
  (§0-B B1 — 동작은 이미 동일하다).
- `src/training/trainer.py:278-294`의 EMA 재발 방지 주석 블록 — 건드리지 않는다.
- `configs/run7_*.yaml`, `configs/mcs*.yaml`, `configs/base.yaml` 등 기존 config 전부 —
  run8은 **신규 파일만** 만든다. 기존 config 수정 = 과거 run 재현성 파괴.
- `scripts/infer_custom.py`의 `run_sampling` / `run_sampling_batched` **함수 본문** —
  이미 `gate_alpha` 파라미터를 받고 있다. §4의 hunk 2개(인자 추가 + main()의 값 결정)만 건드린다.
- `scripts/train.py` — 신규 키는 전부 YAML `training:` 블록이라 entry point 변경 불필요.
- `reports/**` — 이 작업에서는 수정하지 않는다.

**작업 완료 시 `git status --porcelain`에 **새로** 나타나야 하는 항목**
```
M  src/training/trainer.py
?? configs/run8_phase1.yaml
?? configs/run8_phase2.yaml
```
(`M scripts/infer_custom.py`는 feathering 수정분으로 **이미** M 상태다 — 새로 늘지 않는다.
이 3줄 외의 tracked 파일이 M/D로 늘었다면 잘못 건드린 것.)

---

## 3. `src/training/trainer.py` — hunk 8개 (라인 번호는 적용 전 main 기준)

### 3-1. hunk 1 — `__init__` 설정 읽기 (106-108행)

**앵커(현재)**
```python
        self.schedule     = config["training"].get("schedule", "none")
        self.gate_alpha   = config["training"].get("gate_alpha", 1.0)   # PDF alpha gate (Eq. 9)
        self.w_cycle      = config["training"]["loss_weights"].get("cycle", 0.0)
```

**변경 후**
```python
        self.schedule     = config["training"].get("schedule", "none")
        self.gate_alpha   = config["training"].get("gate_alpha", 1.0)   # PDF alpha gate (Eq. 9)
        # run8 soft gate (planning/[0814]run8_soft_gate_plan.md).
        #   "fixed" — 기존 동작. 항상 self.gate_alpha를 쓴다.
        #   "soft"  — iteration마다 a ∈ {0,1}을 Bernoulli(gate_dropout_p)로 뽑는다(gate dropout).
        # 키가 없으면 "fixed"이므로 run1~run7 config는 거동이 100% 동일하다(회귀 없음).
        self.gate_mode      = config["training"].get("gate_mode", "fixed")
        assert self.gate_mode in ("fixed", "soft"), f"Unknown gate_mode: {self.gate_mode}"
        self.gate_dropout_p = float(config["training"].get("gate_dropout_p", 0.5))
        # gate 추첨은 전역 RNG가 아니라 전용 Generator에서 뽑는다. 전역 CPU RNG를 소비하면
        # DataLoader(shuffle=True)가 매 epoch iterator를 만들 때 쓰는 base seed까지 밀려서
        # 데이터 순서가 run7과 달라진다 — gate 말고 변수가 하나 더 생기는 셈이다.
        # 학습 시드 미고정 관행(run4~run7)은 그대로 유지하되(torch.initial_seed()에서 파생),
        # 값을 config에 되써서 TensorBoard hparam·checkpoint에 남긴다 → gate 시퀀스만은 사후 재현 가능.
        # soft일 때만 만든다 — fixed(기존 config)에서는 config를 건드리지 않아, 저장되는
        # checkpoint config가 run7까지와 바이트 단위로 같은 키 집합을 유지한다.
        self.gate_seed: Optional[int] = None
        self._gate_rng: Optional[torch.Generator] = None
        if self.gate_mode == "soft":
            _gs = config["training"].get("gate_seed")
            self.gate_seed = int(_gs) if _gs is not None else int(torch.initial_seed() % (2 ** 31))
            config["training"]["gate_seed"] = self.gate_seed
            self._gate_rng = torch.Generator().manual_seed(self.gate_seed)
        # run8: 학습 루프 내 중간평가(_validate / _perceptual_validate)를 전부 끄고 오프라인
        # 스윕으로 대체한다. 기본 True = 기존 동작.
        # ⚠️ 이 줄은 반드시 _setup_perceptual_eval() 호출(아래)보다 위에 있어야 한다.
        self.midtrain_eval  = config["training"].get("midtrain_eval", True)
        self.w_cycle      = config["training"]["loss_weights"].get("cycle", 0.0)
```

> `Optional`은 이미 import돼 있다(`trainer.py:36`). 신규 import는 없다 —
> **`import random`을 추가하지 말 것**(D4).

### 3-2. hunk 2 — `__init__` setup 호출 스킵 (128-132행)

**앵커**
```python
        self._setup_models()
        self._setup_data()
        self._setup_perceptual_eval()
        self._setup_optimizer()
```
**변경 후**
```python
        self._setup_models()
        self._setup_data()
        if self.midtrain_eval:
            self._setup_perceptual_eval()   # held-out 32장 준비도 불필요해진다
        self._setup_optimizer()
```

### 3-3a. hunk 3a — `train()` 시작 로그에 gate 상태 1줄 (471-474행 바로 뒤)

**앵커**
```python
            + (f" (resuming from epoch {self.start_epoch})" if self.start_epoch else "")
        )
```
**변경 후**
```python
            + (f" (resuming from epoch {self.start_epoch})" if self.start_epoch else "")
        )
        if self.gate_mode == "soft":
            self.accelerator.print(
                f"[gate] soft gate ON — a ~ Bernoulli({self.gate_dropout_p}), "
                f"gate_seed={self.gate_seed} (전용 Generator, 전역 RNG 미소비)"
            )
```
> gate_seed는 `_flatten_config`를 타고 TensorBoard hparam·checkpoint config에도 들어가지만,
> 착수 직후 터미널에서 바로 확인할 수 있게 stdout에도 남긴다.

### 3-3. hunk 3 — `train()` epoch-0 baseline 스킵 (480-482행)

**앵커**
```python
        pval0 = self._perceptual_validate()
        self._best_unbraid = min(self._best_unbraid, pval0["dE_unbraid"])
        self.accelerator.log({f"{k}/ep0": v for k, v in pval0.items()}, step=self.global_step)
```
**변경 후** (바로 위 4줄짜리 주석 블록은 그대로 두고, 이 3줄만 감싼다)
```python
        if self.midtrain_eval:
            pval0 = self._perceptual_validate()
            self._best_unbraid = min(self._best_unbraid, pval0["dE_unbraid"])
            self.accelerator.log({f"{k}/ep0": v for k, v in pval0.items()}, step=self.global_step)
```

### 3-4. hunk 4 — epoch 루프의 두 평가 블록 스킵 (523행, 533행)

블록 **본문은 손대지 않는다**. 조건만 `and`로 확장한다(재들여쓰기 금지 — 들여쓰기를 바꾸면
early-stopping·로깅 로직까지 diff에 섞여 검토가 불가능해진다).

**앵커 1 (523행)**
```python
            if (epoch + 1) % eval_every == 0:
```
**변경 후**
```python
            if self.midtrain_eval and (epoch + 1) % eval_every == 0:
```

**앵커 2 (533행)**
```python
            if (epoch + 1) % perceptual_every == 0:
```
**변경 후**
```python
            if self.midtrain_eval and (epoch + 1) % perceptual_every == 0:
```

> `save_every` 블록(559-560행)은 **건드리지 않는다** — epoch_N.pth 저장은 오프라인 스윕의
> 입력이므로 run8에서 유일한 산출 경로다.

### 3-5. hunk 5 — `_train_step` gate 샘플링 (622-624행)

**앵커**
```python
            block_samples = [s.to(dtype=torch.bfloat16) for s in block_samples]
            if self.schedule != "none":
                block_samples = gate_block_samples(block_samples, matte, self.schedule, gate_alpha=self.gate_alpha)
```
**변경 후**
```python
            block_samples = [s.to(dtype=torch.bfloat16) for s in block_samples]
            # run8 soft gate: iteration당 1회, 배치 전체가 같은 a를 쓴다(샘플 단위 아님 —
            # gate_block_samples가 스칼라만 받는다, controlnet_sd35.py:437).
            # torch.rand를 쓰는 이유: 이 파이프라인의 난수는 전부 torch 스트림(노이즈/sigma/
            # DataLoader shuffle)이라 torch.manual_seed 하나로 gate 시퀀스까지 함께 재현된다.
            # random 모듈은 그 시드가 지배하지 않는 별도 스트림이라 gate만 복원 불가가 된다.
            # gate_mode="fixed"(기본)에서는 난수를 아예 뽑지 않으므로 기존 run과 난수열 동일.
            if self.gate_mode == "soft":
                gate_a = float(torch.rand((), generator=self._gate_rng).item() < self.gate_dropout_p)
            else:
                gate_a = self.gate_alpha
            if self.schedule != "none":
                block_samples = gate_block_samples(block_samples, matte, self.schedule, gate_alpha=gate_a)
```

> `generator=self._gate_rng`가 핵심이다(D7). 전역 `torch.rand(())`를 쓰면 전역 CPU RNG가
> 소비되어 `DataLoader(shuffle=True)`의 다음 epoch base seed가 밀리고, 그러면 데이터 순서가
> run7과 갈려 gate 외 변수가 하나 더 생긴다 — §0-C 참고.
> `self.gate_alpha`는 그대로 남겨둔다 — `_validate`/`_perceptual_validate`와 추론 config가 쓴다.

### 3-6. hunk 6 — `gate_a` 로깅 (`_train_step` 말미, 727-730행)

**앵커**
```python
        if "densify_t" in batch:
            log_dict["densify_t"] = float(batch["densify_t"][0])

        return total_loss, log_dict
```
**변경 후**
```python
        if "densify_t" in batch:
            log_dict["densify_t"] = float(batch["densify_t"][0])

        # run8 soft gate 실측 검증용 — 이 스칼라의 이동평균이 gate_dropout_p(0.5)로 수렴하는지
        # 확인한다(lpips_active_fraction과 같은 용도). fixed 모드에서는 상수라 무해.
        log_dict["gate_a"] = float(gate_a)

        return total_loss, log_dict
```
> `gate_a`는 `with self.accelerator.accumulate(...)` 안에서 정의되지만 `with`는 스코프를 만들지
> 않으므로 여기서 그대로 보인다.

### 3-7. hunk 7 — `_perceptual_validate` 조기 return 가드 (805행)

**앵커** (docstring 닫는 `"""` 직후, 첫 import 문)
```python
        from scripts.eval_metrics import (
```
**변경 후**
```python
        # midtrain_eval=False면 _setup_perceptual_eval()을 건너뛰어 self._pval_* 자체가 없다.
        # 호출부를 하나라도 놓쳤을 때 학습 중반에 AttributeError로 죽지 않도록 여기서 먼저 막는다
        # (이 함수는 scripts.infer_custom / scripts.eval_metrics를 import하므로, 그 무거운
        #  의존성 로드까지 여기서 차단된다).
        if not self.midtrain_eval:
            return {}

        from scripts.eval_metrics import (
```
> 이 가드는 **이중 방어**다. hunk 3·4로 호출부를 이미 막았으므로 정상 경로에서는 실행되지 않는다.
> (호출부를 막지 않고 이 가드만 넣으면 `pval0["dE_unbraid"]`에서 `KeyError`가 난다 — 둘 다 필요.)

---

## 4. `scripts/infer_custom.py` — hunk 2개 (라인 번호는 워킹트리 기준)

### 4-1. hunk 1 — `--gate_alpha` 인자 추가 (592행 `--device` 바로 앞)

**앵커**
```python
    parser.add_argument("--device",        default=None,
                        help="cuda / cpu (기본: cuda if available)")
```
**변경 후**
```python
    parser.add_argument("--gate_alpha", type=float, default=None,
                        help="matte gate 강도 a ∈ [0,1] (PDF Eq.9, r̂=r⊙[a·m̃+(1-a)]). "
                             "미지정(기본)이면 config의 training.gate_alpha를 그대로 쓴다 — "
                             "즉 기존 동작 불변. 1.0=full gating, 0.0=게이트 없음"
                             "(schedule=none과 수치적으로 동일). run8 soft gate 모델의 "
                             "on/off 검증용 (planning/[0814]run8_code_change_spec.md).")
    parser.add_argument("--device",        default=None,
                        help="cuda / cpu (기본: cuda if available)")
```

### 4-2. hunk 2 — `main()`에서 CLI 우선 적용 (608행)

**앵커**
```python
    gate_alpha       = cfg["training"].get("gate_alpha", 1.0)   # PDF alpha gate (Eq. 9)
```
**변경 후**
```python
    gate_alpha       = cfg["training"].get("gate_alpha", 1.0)   # PDF alpha gate (Eq. 9)
    if args.gate_alpha is not None:
        gate_alpha = args.gate_alpha                            # CLI가 config를 덮어씀
    print(f"[gate] schedule={schedule}, gate_alpha={gate_alpha}"
          f"{' (CLI override)' if args.gate_alpha is not None else ' (config)'}")
```

> - 692행의 `gate_alpha=gate_alpha,` 호출부는 **그대로 둔다**(지역변수를 이미 넘기고 있다).
> - `zero_raw_matte`가 쓰는 `args.X or cfg[...]` 패턴을 따라하지 말 것 — `gate_alpha=0.0`은
>   falsy라 `or`로 쓰면 0.0이 config 값으로 되돌아간다. 반드시 `is not None`으로 판정한다.
> - 범위 검증은 `gate_block_samples`가 첫 step에 `ValueError`로 잡아준다(추가 검증 불필요).
> - `run_sampling_batched`(trainer 전용)는 손대지 않는다.

---

## 5. 신규 config

### 5-1. `configs/run8_phase1.yaml`  (템플릿: `configs/run7_phase1.yaml`)

실질 변경 4개(`gate_mode`, `gate_dropout_p`, `midtrain_eval`, `output_dir`). 그 외 한 글자도
바꾸지 않는다 — run7과의 단일변수 비교가 이 실험의 전부다.

```yaml
# configs/run8_phase1.yaml — run8 phase1: run7과 동일 파이프라인, matte gate만 soft(gate dropout)
#
# 근거: planning/[0814]run8_soft_gate_plan.md, planning/[0814]run8_code_change_spec.md
#   - configs/run7_phase1.yaml에서 gate 결정 방식 + 중간평가 on/off 외에는 전부 동일
#   - 시작점도 run7과 같은 run5_1(epoch15) full checkpoint
base: configs/base.yaml

model:
  zero_matte_cond: false
  zero_matte_feat: false
  zero_raw_matte: false
  num_extra_conditioning_channels: 16
  matte_bias_zero_init: true
  use_matte_scale: true

training:
  phase: pretrain
  dataset: unbraid
  epochs: 40                 # cosine LR T_max가 이 값에 묶여 있음 — 줄이지 말 것
  batch_size: 16             # 누락 금지(기본값 4) — s≈37 전제가 깨짐
  learning_rate: 1.0e-4
  warmup_steps: 500
  mode: forward
  schedule: all
  gate_alpha: 1.0            # soft 모드에서 학습에는 안 쓰이지만, 이 yaml로 infer_custom.py를
                             # 돌릴 때의 기본 게이트 값이다. 반드시 1.0로 유지(§8 스윕 전제).
  gate_mode: soft            # 🆕 iteration마다 a∈{0,1} Bernoulli 샘플
  gate_dropout_p: 0.5        # 🆕
  midtrain_eval: false       # 🆕 in-loop _validate/_perceptual_validate 전면 off → 오프라인 스윕
  resume: checkpoints/run5_1_noisegate/epoch_15.pth   # 🔴 full ckpt 필수 (§7-P1 검증)
  early_stopping: false      # 기본값이 True다 — 명시 필수 (§0-B B7)

  loss_weights:
    flow: 1.0
    lpips: 0.002
    edge: 0.0
    lpips_noise_cutoff: 0.7
    lpips_gate: noise        # ⚠️ main의 HairLoss는 이 키를 읽지 않는다(noise gate 하드코딩).
                             #    run7 config와의 표기 일치를 위해 남길 뿐, 동작은 동일(§0-B B1).
    scale_sync: true
    s_min: 20.0
    s_max: 120.0

  densify:
    enabled: false
    mask_root: data/densify_masks
    thresholds: [null, 21, 15, 12]

checkpointing:
  output_dir: checkpoints/run8_phase1/     # 🔴 run7과 반드시 분리 (덮어쓰기 경고 없음)
  eval_every: 10               # midtrain_eval:false라 무시됨 (run7 대비 diff 표용으로 값 유지)
  perceptual_every: 1          # midtrain_eval:false라 무시됨
  save_every: 5                # epoch 5/10/.../40 → 오프라인 스윕 대상

# 착수 직후 필수 확인:
#   - "Resumed from checkpoints/run5_1_noisegate/epoch_15.pth (epoch 15, step ...)" 출력
#   - "[PerceptualVal] held-out eval set ..." 로그가 **안 찍혀야** 한다 (midtrain_eval:false 확인)
#   - step ~200 시점 gate_a 이동평균 ≈ 0.50 ± 0.05
#   - step ~10:  lpips_active_fraction ≈ 0.40 ± 0.03
#   - 전 구간:   densify_t 로그 키가 없어야 한다
```

### 5-2. `configs/run8_phase2.yaml`  (템플릿: **`configs/run7_phase2_rawstart.yaml`**)

> 🔴 `configs/run7_phase2.yaml`(EMA 시작 버그로 실패한 1차 시도)을 템플릿으로 쓰지 말 것.
> 실제로 완주해 리포트에 실린 phase2는 **rawstart** 계열이다(§0-B B5).

```yaml
# configs/run8_phase2.yaml — run8 phase2: replay finetune, soft gate 유지
#
# 근거: planning/[0814]run8_soft_gate_plan.md, planning/[0814]run8_code_change_spec.md
#   - 템플릿은 configs/run7_phase2_rawstart.yaml (실제 완주본). run7_phase2.yaml은 EMA 시작
#     버그로 실패한 1차 시도라 승계하지 않는다.
#   - LR 2.0e-5: mcs2(raw 시작, 2e-5)에서 검증된 값이고 run7_phase2_rawstart 실행값이다.
#     (교수님 지시 ③ — 커밋된 run7_phase2.yaml의 5.0e-6은 실행값이 아니다)
base: configs/base.yaml

model:
  zero_matte_cond: false
  zero_matte_feat: false
  zero_raw_matte: false
  num_extra_conditioning_channels: 16
  matte_bias_zero_init: true
  use_matte_scale: true

training:
  phase: finetune              # ⚠️ 필수! edge 활성화
  dataset: replay              # unbraid_train(3000) + braid_train(1000), 8:8 stratified
  sample_seed: 0
  epochs: 40
  batch_size: 16
  learning_rate: 2.0e-5
  warmup_steps: 500
  early_stopping: false        # 기본값이 True다 — run7_phase2 1차가 실제로 epoch15에서
                               # 조기종료됐다. 명시 필수 (§0-B B7)
  mode: forward
  schedule: all
  gate_alpha: 1.0
  gate_mode: soft              # 🆕 phase2도 soft 유지
  gate_dropout_p: 0.5          # 🆕
  midtrain_eval: false         # 🆕
  resume: null                 # ⚠️ phase 전환에 --resume 금지. CosineAnnealingLR은 주기함수라
                               #    phase1 종료 지점 이후로 이어가면 LR이 되레 올라간다
                               #    (run7_phase2 리포트: 의도 대비 누적 LR 3.2배, 실측 확인).
  # 🔴 placeholder — run8_phase1 오프라인 스윕(§8-1) 결과로 확정할 것. 무조건 epoch40 아님.
  #    weights-only 로드다(trainer.py resume_from 분기) — EMA 덮어쓰기는 코드에서 제거됨.
  resume_from: checkpoints/run8_phase1/epoch_40.pth

  loss_weights:
    flow: 1.0
    lpips: 0.002
    edge: 0.05                 # mcs2 parity 유지 (교수님 확정, 올리지 않음)
    lpips_noise_cutoff: 0.7
    lpips_gate: noise          # ⚠️ main에서는 읽히지 않는 키 (§0-B B1)
    scale_sync: true
    s_min: 20.0
    s_max: 120.0

checkpointing:
  output_dir: checkpoints/run8_phase2/
  eval_every: 5                # midtrain_eval:false라 무시됨
  perceptual_every: 1          # midtrain_eval:false라 무시됨
  save_every: 5

# 착수 직후 필수 확인:
#   - "Loaded Phase 1 weights from checkpoints/run8_phase1/epoch_N.pth" 출력
#     (EMA 관련 로그는 코드에서 제거됐으므로 안 뜨는 게 정상 — run7_phase2*.yaml 하단의
#      "Loaded Phase 1 EMA weights" 주석은 stale이니 무시)
#   - "Resumed from ..."은 **안 떠야** 한다 (resume: null 확인)
#   - "[PerceptualVal] ..." 로그가 안 떠야 한다
#   - gate_a 이동평균 ≈ 0.50
```

---

## 6. 검증 절차 — 순서대로 (V1~V6 **통과 완료**, 2026-08-14 로컬 `hair-dit` env)

```
V1 syntax ok
V2 config compat ok
   phase1 diff(run7→run8): output_dir / gate_mode / gate_dropout_p / midtrain_eval — 4개뿐
   phase2 diff(run7_rawstart→run8): 위 4개 + resume_from(run8_phase1로 교체) — 5개뿐
V3 a=0 identity: True   |  a=1 changes: True
V4 Bernoulli mean = 0.5057 (n=20000)  |  동일 seed 재현성: True
V4b 전용 Generator 500회 소비 후 전역 RNG 불변: True     ← D7 전제 실측
V5 --gate_alpha 노출 확인 (--help)
V6 blast radius: M trainer.py(+53/-7), M infer_custom.py(+10), ?? run8_phase{1,2}.yaml
   fixed 모드에서 config에 gate_seed 키 추가되지 않음 확인
```

### 6-V1. 문법 (GPU 불필요, 로컬 `hair-dit` env)
```bash
cd /home/diglab/workspace/projects/hair/HairDiT
python -c "import ast; ast.parse(open('src/training/trainer.py').read()); ast.parse(open('scripts/infer_custom.py').read()); print('syntax ok')"
```

### 6-V2. 기존 config 하위호환 — **가장 중요한 회귀 방지**
```bash
python - <<'PY'
import sys; sys.path.insert(0, '.')
from scripts.train import load_config
# main에 존재하는 config만 대상 (run5_1/run5_2/run6_* 는 main에 없음 — spec §0-B B4)
for p in ["configs/run7_phase1.yaml", "configs/run7_phase2.yaml",
          "configs/run7_phase2_rawstart.yaml", "configs/mcs2_phase1.yaml"]:
    t = load_config(p)["training"]
    assert t.get("gate_mode", "fixed") == "fixed", p
    assert t.get("midtrain_eval", True) is True, p
for p in ["configs/run8_phase1.yaml", "configs/run8_phase2.yaml"]:
    t = load_config(p)["training"]
    assert t["gate_mode"] == "soft" and t["gate_dropout_p"] == 0.5, p
    assert t["midtrain_eval"] is False and t["gate_alpha"] == 1.0, p
    assert t["schedule"] == "all", p
    assert t["early_stopping"] is False, p          # §0-B B7
print("config compat ok")
PY
```
기대: 기존 config는 전부 `fixed`/`midtrain_eval=True` → 코드 경로가 run7과 동일.

### 6-V3. gate_alpha=0.0 ≡ 게이트 없음 (수치 동일성)
```bash
python - <<'PY'
import sys, torch; sys.path.insert(0, '.')
from src.models.controlnet_sd35 import gate_block_samples
bs = [torch.randn(2, 1024 + 154, 64) for _ in range(12)]
m  = torch.rand(2, 1, 512, 512)
a0 = gate_block_samples([b.clone() for b in bs], m, "all", gate_alpha=0.0)
a1 = gate_block_samples([b.clone() for b in bs], m, "all", gate_alpha=1.0)
print("a=0 identity :", all(torch.equal(x, y) for x, y in zip(bs, a0)))
print("a=1 changes  :", any(not torch.equal(x, y) for x, y in zip(bs, a1)))
PY
```
기대: `True` / `True`.

### 6-V4. Bernoulli 실측 + 전용 Generator의 전역 RNG 격리 (D7 전제)
```bash
python - <<'PY'
import torch
g = torch.Generator().manual_seed(12345)
xs = [float(torch.rand((), generator=g).item() < 0.5) for _ in range(20000)]
print("V4 mean =", sum(xs)/len(xs), "(기대 0.50 ± 0.01)")

# 전용 Generator를 아무리 소비해도 전역 RNG는 그대로여야 한다 —
# 이게 깨지면 DataLoader 순서가 밀려 gate 외 변수가 생긴다(§0-C).
torch.manual_seed(7); before = torch.rand(3)
torch.manual_seed(7)
g2 = torch.Generator().manual_seed(999)
_ = [torch.rand((), generator=g2) for _ in range(500)]
print("V4b global RNG 불변 :", torch.equal(before, torch.rand(3)))
PY
```

### 6-V5. `--gate_alpha` 노출 확인
```bash
python scripts/infer_custom.py --help | grep -A3 -- "--gate_alpha"
```

### 6-V6. blast radius 확인
```bash
git status --porcelain | grep -E "^( M|M |D |A )"   # §2의 목록과 대조
git diff --stat src/training/trainer.py
```
기대: trainer.py 대략 `+32 / -6` 수준. 삭제(`-`)가 10줄을 넘으면 실수로 블록을 재들여쓰기했거나
지웠다는 신호다 — 특히 `trainer.py:278-294` EMA 재발 방지 주석이 살아 있는지 확인할 것.

### 6-V7. (학습 서버) 1-epoch 스모크
`epochs: 1`, `save_every: 1`, `output_dir: checkpoints/_smoke_run8/`로 복사한 임시 config로
run8_phase1을 1 epoch만 돌려 ① `[PerceptualVal]` 로그 없음 ② TensorBoard에 `gate_a` 스칼라 존재
③ `epoch_1.pth` / `epoch_1_infer.pth` 생성 — 3가지 확인 후 본 학습 착수.

---

## 7. 착수 전 서버 확인 (P1~P4)

### P1 🔴 `resume` full checkpoint 존재 — 놓치면 조용히 망가진다
`trainer.py`의 resume 분기는 `if resume and Path(resume).exists():`다. **경로가 없으면 경고 없이
통과**하고 가중치 로드도 optimizer 복원도 건너뛴 채 epoch 0부터 학습을 시작한다. 로컬에는
`epoch_15_infer.pth`(weights-only)만 있고 `epoch_15.pth`는 없다.
```bash
python - <<'PY'
import torch
p = "checkpoints/run5_1_noisegate/epoch_15.pth"
c = torch.load(p, map_location="cpu", weights_only=True)
print(sorted(c.keys()))
print("epoch =", c.get("epoch"), "| global_step =", c.get("global_step"))
PY
```
기대: `controlnet` / `optimizer` / `lr_scheduler` / `epoch=15` / `global_step≈2805` 모두 존재.
하나라도 없으면 **착수 금지**(run7과 시작점이 달라져 비교가 무의미해진다).

### P2 디스크
`save_every: 5` → epoch 8회 × (full ~20GB + infer ~6.1GB) ≈ **210GB/phase**, 양 phase 420GB.
`df -h`로 확보 확인. 부족하면 보관 정책을 **사전에** 정할 것(원격 파일 삭제 금지 원칙).

### P3 오프라인 스윕 GPU env
`scripts/infer_custom.py`는 최상단에서 `import kornia.filters as KF`를 한다(feathering 수정분).
```bash
python -c "import kornia, cv2, lpips; print('eval env ok')"
```
학습 GPU env에는 불필요(`midtrain_eval: false`라 import 경로가 실행되지 않음).

### P4 phase2 데이터
`dataset: replay`는 `braid_train` / `braid_test` split을 요구한다. 로컬에는 없다 — phase2 착수
전 서버에 존재 확인.

---

## 8. 오프라인 스윕 (D2: CRG 1.5 / D5: 전 스텝 블렌딩)

### 8-1. 이관 epoch 선정 스윕 (phase1 완주 후)
```bash
for EP in 5 10 15 20 25 30 35 40; do
  for SEED in 42 1 2 3; do
    python scripts/infer_custom.py \
      --sketch dataset/test/sketch \
      --matte  dataset/test/matt \
      --face   dataset/test/img \
      --checkpoint checkpoints/run8_phase1/epoch_${EP}_infer.pth \
      --config     configs/run8_phase1.yaml \
      --num_steps 20 --seed ${SEED} \
      --recolor_from_gt \
      --bld_mode full \
      --pixel_blend --pixel_blend_feather 0 \
      --crg_scale 1.5 \
      --gate_alpha 1.0 \
      --output_dir outputs/0814/run8_phase1/${SEED}/epoch${EP}
  done
done
```
- **`--bld_soft_steps`는 지정하지 않는다**(D5). 20 스텝 전부 블렌딩된다. run7의 `18`과 다르다.
- `--gate_alpha 1.0`은 config 값과 같아 생략해도 되지만, **명시해 두면 커맨드만 보고 게이트
  조건을 알 수 있다.** 스윕 전체에서 이 값을 고정한다.
- `--pixel_blend_feather 0`은 기본값이지만 last_test.md 지시 사항이라 명시한다.
- 선정 기준(교수님 지시 ④, run7과 동일): **방향 지표 1순위**
  (`scripts/eval/orientation_metric.py` — GT 오차 / coherence / seed 불일치),
  색·구조 지표(`scripts/eval_metrics.py` — dE, lpips)는 참고.
- `--seed` 4개가 필요한 이유: "seed 불일치"는 seed 간 분산 지표라 단일 seed로는 계산 불가.

### 8-2. run8 목적 검증 — gate on/off (phase2 완주 후, last_test.md 합격 조건)
```bash
for GA in 1.0 0.0; do
  python scripts/infer_custom.py \
    --sketch dataset/test/sketch --matte dataset/test/matt --face dataset/test/img \
    --checkpoint checkpoints/run8_phase2/epoch_<채택>_infer.pth \
    --config     configs/run8_phase2.yaml \
    --num_steps 20 --seed 42 \
    --recolor_from_gt \
    --bld_mode full \
    --pixel_blend --pixel_blend_feather 0 \
    --crg_scale 1.5 \
    --gate_alpha ${GA} \
    --output_dir outputs/0814/run8_gate/${GA}
done
```

**대조군 (필수)**: run7의 채택 체크포인트(`checkpoints/run7_phase2_rawstart/epoch_*_infer.pth`)를
**위와 완전히 같은 커맨드**로 다시 돌린다. run7 리포트 표는 CRG 2.0 · `--bld_soft_steps 18`로
측정된 값이라 **지금 조건과 직접 비교할 수 없다**(§1-A6). run7은 `gate_mode: fixed`로 학습됐으므로
`--gate_alpha 0.0`에서 무너지는 것이 예상 거동이며, 그게 soft gate의 효과를 보이는 대조다.

**해석 주의**: `gate_alpha=0.0`은 **residual gate만** 끄는 것이다. matte는 여전히 ControlNet
입력(MatteCNN bias + RawMatteAnchor, 32ch)으로 들어간다. "gate off ≠ matte 정보 제거"이며,
matte를 완전히 빼는 조건은 last_test.md의 별도 ablation(sketch-only, 16ch)이다.

### 8-3. 남은 미결정
- ~~**O1 `--bld_soft_steps`**~~ → **해소**(D5, 2026-08-14 사용자 확인: 전 스텝 블렌딩 20 step).
- **O2 `scripts/eval/orientation_metric.py`**: `RUNS` dict에 경로가 하드코딩돼 있고
  (`orientation_metric.py:29-33`) `IMAGES`가 2장, `GT_DIR`이 `data/test/ori_image`로 고정이다.
  run7 스윕에 쓴 파생본(`scripts/eval/quant50_run7_phase2.py` / `quant50_braid_run7_phase2.py`가
  main에 있음)을 확인해 run8용을 같은 방식으로 파생시킬 것.
  **이 사양서의 코드 변경 범위에는 포함하지 않는다.**
- **O3 last_test.md의 신규 지표는 미구현** (사용자 지시: "일단 좀만 기다리고"):
  ① 경계 밴드가 `dilate(matte>0,k) − erode(matte>0,k)` (8/16px)여야 하는데 현재
  `get_boundary_mask`는 alpha 값 밴드(25≤m≤230)다(`eval_metrics.py:200-201`).
  ② same-identity ArcFace 지표는 `ALL_METRICS`에 없다.
  둘 다 run8 학습과 독립인 별도 작업이므로 여기서 건드리지 않는다.

---

## 9. 리포트에 반드시 남길 것 (last_test.md 명시 지시 — 생략 금지)

run8 결과 리포트에 다음을 **명시적으로** 기록한다("조용한 skip 허용 안 합니다").

1. **EMA 버그**: phase1→phase2 전환을 EMA shadow로 넘겼더니 사실상 처음부터 재학습되는 결과가
   나왔다(산출물 `checkpoints/joint_phase2_EMA_mistake/`, 재발본 `run7_phase2` 1차). 실측 근거는
   `trainer.py:278-294` 주석 그대로 — `controlnet_blocks`(zero-init 조건 주입 경로)의
   ‖ema‖/‖raw‖ = **0.396x**, 일반 레이어는 0.99x. EMAModel에 bias correction이 없어
   decay=0.9999가 수렴하려면 10,000 step이 필요한데 phase1은 7,480 step뿐이었다.
   이후 **weights-only 전환**으로 수정했고(`run7_phase2_rawstart`), 현재 코드에는 EMA가 전부
   제거돼 있다. run8도 이 상태 그대로다.
2. **중간평가 제거**: run8부터 `_validate`/`_perceptual_validate`를 껐고, 대신 `save_every`
   체크포인트를 오프라인 스윕한다. 이는 새 방법론이 아니라 **run7이 이미 실제로 쓰던 방식**의
   명시화다 — run7의 선정 표도 오프라인 스윕 결과였고, 선정 1순위인 방향 지표는
   `_perceptual_validate`가 계산조차 하지 않는다(§1-A7).
3. **파이프라인 차이 caveat (신규, §0-B)**: run7은 `run5-ablation-split` 브랜치 코드로,
   run8은 `main` 코드로 학습된다. 학습 수식·게이트·데이터 경로는 동일하지만(main의
   `lpips_gate` 하드코딩 = run7이 쓴 noise gate), main에는 **시드 기록(`torch.initial_seed()`)과
   `grad_norm` 로깅이 없다**. 즉 run8은 run7이 갖고 있던 진단 로그 2종이 없고, 학습 시드도
   여전히 미고정이다(D6). 셀당 n=1이므로 run7 vs run8 차이가 gate 방식 때문인지 시드 때문인지는
   단정할 수 없다 — §0-C 표를 그대로 옮겨 적을 것.
   덧붙여 gate 추첨은 **전용 Generator**를 써서 전역 RNG를 소비하지 않으므로(D7), 중간평가
   제거를 제외하면 데이터 순서·노이즈 시퀀스가 run7 방식과 동일한 규칙을 따른다. `gate_seed`
   값은 checkpoint config와 TensorBoard hparam에 남아 gate 시퀀스만은 사후 재현 가능하다.
4. **평가 조건 변경**: run7 리포트 표는 CRG 2.0 + `bld_soft_steps 18`, run8은 CRG 1.5 +
   전 스텝 블렌딩이다. 두 표를 그대로 나란히 놓지 말고, run7 채택본을 run8 조건으로
   재측정한 값을 함께 실을 것(§8-2).
5. **run7 대비 config diff 표**(교수님 지시 ⑤ 관행): 실질 변경은
   `gate_mode` / `gate_dropout_p` / `midtrain_eval` / `output_dir` 4개뿐임을 표로 제시.
   phase2는 템플릿이 `run7_phase2_rawstart.yaml`임을 밝힐 것.
6. **`gate_a` 실측 평균**(기대 0.50) — soft gate가 실제로 켜져 돌았다는 유일한 증거.
