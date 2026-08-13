#!/bin/bash
# run7_phase2_rawstart braid 50장 정량 inference (병렬) + 지표 계산.
#
# unbraid 정량(infer_all_run7_phase2_rawstart_0813.sh)과 **완전히 같은 조건**으로 돌린다:
#   face 합성/BLD/pixel_blend/cfg 전부 미사용, --recolor_from_gt, num_steps 20
# 다른 것은 입력 pool(braid test 50장)과 출력 경로뿐이다.
#
# phase2는 replay(unbraid+braid) 학습이고 목적이 braid 습득이므로, unbraid 유지력만 재는
# 기존 지표로는 채택 근거가 절반이다. edge_iou_braid(스케치 대비 구조 충실도)가 핵심.
set -u

RUN=run7_phase2_rawstart
CKPT_DIR=/lambda/nfs/hairDiT/checkpoints/$RUN
CONFIG=/lambda/nfs/hairDiT/configs/run7_phase2_rawstart.yaml
POOL=/lambda/nfs/hairDiT/outputs/0813/quant50/_pool50_braid
OUT=/lambda/nfs/hairDiT/outputs/0813/quant50_braid/$RUN
LOGD=/lambda/nfs/hairDiT/outputs/0813/_logs_${RUN}_braid

SEEDS="42 1 2 3"
N_PARALLEL=${N_PARALLEL:-8}
N_EXPECT=50
mkdir -p "$OUT" "$LOGD"

# [0813] 스레드 과다구독 방지.
# 미설정이면 프로세스당 104 스레드가 뜨고, 8 프로세스면 코어 26개에 832 스레드가 몰려
# load average가 166까지 치솟는다(실측). 특히 braid는 스케치 고유 색상이 61개(unbraid는 11개)라
# recolor_from_gt의 "색상별 512x512 마스크 루프"가 CPU 병목이 되는데, 거기에 스레드까지
# 과다구독되면 GPU가 0%로 놀고 처리량이 34.6장/분 → 19장/분으로 떨어진다.
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-3}
export MKL_NUM_THREADS=${MKL_NUM_THREADS:-3}
export OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-3}
export NUMEXPR_NUM_THREADS=${NUMEXPR_NUM_THREADS:-3}

log() { echo "[braid-quant] $(date -u +%H:%M:%S) $*"; }

job() {
    local ckpt="$1" ep="$2" seed="$3"
    local out="$OUT/$seed/epoch${ep}"
    local lg="$LOGD/braid_quant50_${ep}_seed${seed}.log"
    [ "$(ls "$out" 2>/dev/null | wc -l)" -ge "$N_EXPECT" ] && { log "skip ep$ep seed$seed"; return 0; }
    log "start ep$ep seed$seed"
    python3 /lambda/nfs/hairDiT/scripts/infer_custom.py \
        --sketch "$POOL/sketch" --matte "$POOL/matte" --recolor_face "$POOL/img" \
        --recolor_from_gt \
        --checkpoint "$ckpt" --config "$CONFIG" \
        --num_steps 20 --seed "$seed" \
        --output_dir "$out" >> "$lg" 2>&1
    n=$(ls "$out" 2>/dev/null | wc -l)
    [ "$n" -ge "$N_EXPECT" ] && log "done ep$ep seed$seed ($n/$N_EXPECT)" \
                             || log "FAILED ep$ep seed$seed ($n/$N_EXPECT) — $lg"
}

throttle() { while [ "$(jobs -rp | wc -l)" -ge "$N_PARALLEL" ]; do sleep 5; done; }

EPOCHS=${EPOCHS:-$(ls "$CKPT_DIR"/epoch_*_infer.pth 2>/dev/null \
         | sed -e 's|.*/epoch_||' -e 's|_infer\.pth$||' | sort -V)}
log "대상 epoch: $(echo $EPOCHS | tr '\n' ' ') (N_PARALLEL=$N_PARALLEL)"

for ep in $EPOCHS; do
    ckpt="$CKPT_DIR/epoch_${ep}.pth"
    [ -f "${ckpt%.pth}_infer.pth" ] || { log "건너뜀: epoch$ep infer 체크포인트 없음"; continue; }
    for seed in $SEEDS; do
        throttle; job "$ckpt" "$ep" "$seed" &
    done
done
wait
log "braid inference 완료"

log "지표 계산 시작"
cd /lambda/nfs/hairDiT
python3 scripts/eval/quant50_braid_run7_phase2.py --epochs $EPOCHS \
    > "$LOGD/quant50_braid_metrics.txt" 2>&1
log "지표 완료 -> $LOGD/quant50_braid_metrics.txt"
grep -v "^  \[skip\]" "$LOGD/quant50_braid_metrics.txt" | tail -20
log "ALL DONE braid"
