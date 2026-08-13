#!/bin/bash
# infer_all_run7_phase2_rawstart_0813.sh(정성+정량 inference → 정량지표 계산)가 끝나면
# 리포트를 생성하고 이미지와 함께 커밋·push 한다.
#
# outputs/ 와 dataset/ 은 .gitignore 대상이라 phase1 리포트 때와 동일하게 `git add -f`로
# 리포트가 참조하는 파일만 강제 추가한다(전체 outputs를 넣지 않는다).
set -u

CHAIN_PID=${CHAIN_PID:?CHAIN_PID 필요}
RUN=run7_phase2_rawstart
ROOT=/lambda/nfs/hairDiT
REPORT="reports/[DIGLAB][0812][장서현]run7_phase2_result.md"
SEED=42
LOG=$ROOT/outputs/0813/_finalize_$RUN.log

cd "$ROOT"
exec >> "$LOG" 2>&1

log() { echo "[finalize] $(date -u +%H:%M:%S) $*"; }

log "inference 체인(PID $CHAIN_PID) 종료 대기..."
while kill -0 "$CHAIN_PID" 2>/dev/null; do sleep 60; done
log "체인 종료 확인"

# ---------- 1) 리포트 생성 ----------
log "리포트 생성"
python3 scripts/make_report_run7_phase2_0813.py || { log "리포트 생성 실패 — 중단"; exit 1; }

# ---------- 2) 리포트가 참조하는 이미지만 강제 추가 ----------
log "이미지 스테이징"
# 정성 결과 (seed42만 — 리포트가 참조하는 범위)
for kind in color gt; do
    d="outputs/0813/$RUN/$kind/$SEED"
    [ -d "$d" ] && git add -f --sparse "$d" 2>&1 || log "  add 실패: $d"
done
# 리포트가 참조하는 입력 이미지
for d in dataset/test/img dataset/test/sketch dataset/test/sketch_gt; do
    [ -d "$d" ] && git add -f --sparse "$d" 2>&1 || log "  add 실패: $d"
done
# 리포트 · 스크립트 · 설정 (gitignore 대상 아님)
git add "$REPORT" \
        scripts/make_report_run7_phase2_0813.py \
        scripts/infer_all_run7_phase2_rawstart_0813.sh \
        scripts/finalize_and_push_run7_phase2_0813.sh \
        scripts/watch_and_infer_run7_phase2_rawstart_0813.sh \
        scripts/eval/quant50_run7_phase2.py \
        configs/run7_phase2_rawstart.yaml \
        configs/run7_phase2_rawstart_resume.yaml 2>/dev/null

n_files=$(git diff --cached --name-only | wc -l)
log "스테이징된 파일 수: $n_files"
if [ "$n_files" -eq 0 ]; then
    log "커밋할 변경 없음 — 종료"
    exit 0
fi

# ---------- 3) 커밋 ----------
git commit -q -F - <<'MSG'
0813 리포트: run7_phase2 재학습(rawstart) 결과 — EMA 시작 버그 수정 후 정성·정량 평가

1차 run7_phase2는 phase2 epoch5부터 color sketch의 색 조건화가 붕괴했다. 원인은 LR이 아니라
resume_from의 EMA shadow 덮어쓰기였다(controlnet_blocks의 ||ema||/||raw|| = 0.396x — 조건 신호
주입 경로만 40% 세기로 시작). LR은 2e-5 그대로 두고 EMA 수정 단일 변수만 바꿔 재학습한 결과
epoch5에서 색이 복원되어 인과가 분리 확인됐다.

- reports/[DIGLAB][0812][장서현]run7_phase2_result.md 신규 (phase1 리포트와 동일 구조:
  정량지표 n=50 표 + 정성 gt/Colorful sketch 이미지 표, seed42)
- 정성 inference 결과 이미지(seed42) 및 리포트 참조 입력 이미지 추가
- scripts: 병렬 inference 체인, 정량지표(quant50_run7_phase2.py), 리포트 생성기

⚠️ 채택 epoch은 미확정 — 정량·정성 함께 검토 후 확정 필요.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
log "커밋 완료: $(git log -1 --pretty='%h %s')"

# ---------- 4) push ----------
log "push 시도"
if git push origin main; then
    log "push 성공"
else
    log "push 실패 — 원격 변경 확인 후 수동 처리 필요"
    git status --short | head -20
    exit 1
fi
log "ALL DONE"
