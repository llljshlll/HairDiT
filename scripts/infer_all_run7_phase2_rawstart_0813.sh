#!/bin/bash
# run7_phase2_rawstart: 학습 종료를 기다렸다가 정성(11장) + 정량(50장) inference를 병렬로 일괄 실행.
#
# 학습과 GPU를 나눠 쓰면 총 소요시간이 같으면서 학습만 느려지므로(실측 3.02 -> 4.4 s/it),
# 학습이 끝나 GPU를 단독으로 쓸 수 있을 때 N_PARALLEL개씩 병렬로 몰아서 돌린다.
#
# [정성] dataset/test 11장 — face 합성 + BLD + pixel_blend + cfg_scale 2.0
#   color : dataset/test/sketch 원본
#   gt-A  : sketch_gt에 있는 7장 (sketch_gt 원본, recolor 플래그 없음)
#   gt-B  : sketch_gt에 없는 braid 4장만 --recolor_from_gt
#   → gt 폴더 11장. CM_1082는 img/에 face가 없어 제외.
#
# [정량] _pool50 50장 — face 합성/BLD/pixel_blend/cfg 전부 미사용, --recolor_from_gt
#   run7_phase1 정량지표(reports/[DIGLAB][0812]run7_phase1_result.md)와 조건을 맞춰야
#   비교가 성립하므로 quant50_run7_0812.sh의 인자를 그대로 유지한다.
set -u

RUN=run7_phase2_rawstart
TRAIN_PID=${TRAIN_PID:-183825}
CKPT_DIR=/lambda/nfs/hairDiT/checkpoints/$RUN
CONFIG=/lambda/nfs/hairDiT/configs/run7_phase2_rawstart.yaml

# 정성
OUT_QUAL=/lambda/nfs/hairDiT/outputs/0813/$RUN
STAGE=/lambda/nfs/hairDiT/outputs/0813/_gt_stage
SKETCH_COLOR=/lambda/nfs/hairDiT/dataset/test/sketch
MATTE=/lambda/nfs/hairDiT/dataset/test/matt
FACE=/lambda/nfs/hairDiT/dataset/test/img

# 정량
POOL=/lambda/nfs/hairDiT/outputs/0812/quant50/_pool50
OUT_QUANT=/lambda/nfs/hairDiT/outputs/0813/quant50/$RUN

SEEDS="42 1 2 3"
CFG_SCALE=2.0
N_PARALLEL=${N_PARALLEL:-8}      # 환경변수로 조정 가능. 프로세스당 ~9GB (8개=72GB, 여유 9GB)
LOGD=/lambda/nfs/hairDiT/outputs/0813/_logs_$RUN
mkdir -p "$OUT_QUAL" "$OUT_QUANT" "$LOGD"

N_COLOR=$(ls "$SKETCH_COLOR" | wc -l)
N_GT_A=$(ls "$STAGE/from_sketch_gt" | wc -l)
N_GT_B=$(ls "$STAGE/needs_recolor" | wc -l)
N_GT=$((N_GT_A + N_GT_B))
N_QUANT=50

log() { echo "[all-$RUN] $(date -u +%H:%M:%S) $*"; }

# ---------- 작업 단위 ----------
# 정성 color: 1회 실행으로 완결
job_color() {
    local ckpt="$1" ep="$2" seed="$3"
    local out="$OUT_QUAL/color/$seed/epoch${ep}"
    local lg="$LOGD/qual_${ep}_color_seed${seed}.log"
    [ "$(ls "$out" 2>/dev/null | wc -l)" -ge "$N_COLOR" ] && { log "skip color ep$ep seed$seed (완료됨)"; return 0; }
    log "start color ep$ep seed$seed"
    python3 /lambda/nfs/hairDiT/scripts/infer_custom.py \
        --sketch "$SKETCH_COLOR" --matte "$MATTE" --face "$FACE" \
        --checkpoint "$ckpt" --config "$CONFIG" \
        --num_steps 20 --seed "$seed" \
        --bld_mode full --bld_soft_steps 18 \
        --pixel_blend --pixel_blend_alpha 0.75 \
        --cfg_scale "$CFG_SCALE" \
        --output_dir "$out" >> "$lg" 2>&1
    n=$(ls "$out" 2>/dev/null | wc -l)
    [ "$n" -ge "$N_COLOR" ] && log "done color ep$ep seed$seed ($n/$N_COLOR)" \
                            || log "FAILED color ep$ep seed$seed ($n/$N_COLOR) — $lg"
}

# 정성 gt: A(sketch_gt 원본) + B(recolor)를 한 폴더에 — 순서 의존이라 한 job으로 묶는다
job_gt() {
    local ckpt="$1" ep="$2" seed="$3"
    local out="$OUT_QUAL/gt/$seed/epoch${ep}"
    local lg="$LOGD/qual_${ep}_gt_seed${seed}.log"
    [ "$(ls "$out" 2>/dev/null | wc -l)" -ge "$N_GT" ] && { log "skip gt ep$ep seed$seed (완료됨)"; return 0; }
    log "start gt ep$ep seed$seed (A ${N_GT_A} + B ${N_GT_B})"
    python3 /lambda/nfs/hairDiT/scripts/infer_custom.py \
        --sketch "$STAGE/from_sketch_gt" --matte "$MATTE" --face "$FACE" \
        --checkpoint "$ckpt" --config "$CONFIG" \
        --num_steps 20 --seed "$seed" \
        --bld_mode full --bld_soft_steps 18 \
        --pixel_blend --pixel_blend_alpha 0.75 \
        --cfg_scale "$CFG_SCALE" \
        --output_dir "$out" >> "$lg" 2>&1
    python3 /lambda/nfs/hairDiT/scripts/infer_custom.py \
        --sketch "$STAGE/needs_recolor" --matte "$MATTE" --face "$FACE" \
        --checkpoint "$ckpt" --config "$CONFIG" \
        --num_steps 20 --seed "$seed" \
        --bld_mode full --bld_soft_steps 18 \
        --pixel_blend --pixel_blend_alpha 0.75 \
        --cfg_scale "$CFG_SCALE" \
        --recolor_from_gt \
        --output_dir "$out" >> "$lg" 2>&1
    n=$(ls "$out" 2>/dev/null | wc -l)
    [ "$n" -ge "$N_GT" ] && log "done gt ep$ep seed$seed ($n/$N_GT)" \
                         || log "FAILED gt ep$ep seed$seed ($n/$N_GT) — $lg"
}

# 정량 50장 (조건: face/BLD/pixel_blend/cfg 미사용 — phase1 정량과 동일)
job_quant() {
    local ckpt="$1" ep="$2" seed="$3"
    local out="$OUT_QUANT/$seed/epoch${ep}"
    local lg="$LOGD/quant50_${ep}_seed${seed}.log"
    [ "$(ls "$out" 2>/dev/null | wc -l)" -ge "$N_QUANT" ] && { log "skip quant ep$ep seed$seed (완료됨)"; return 0; }
    log "start quant50 ep$ep seed$seed"
    python3 /lambda/nfs/hairDiT/scripts/infer_custom.py \
        --sketch "$POOL/sketch" --matte "$POOL/matte" --recolor_face "$POOL/img" \
        --recolor_from_gt \
        --checkpoint "$ckpt" --config "$CONFIG" \
        --num_steps 20 --seed "$seed" \
        --output_dir "$out" >> "$lg" 2>&1
    n=$(ls "$out" 2>/dev/null | wc -l)
    [ "$n" -ge "$N_QUANT" ] && log "done quant50 ep$ep seed$seed ($n/$N_QUANT)" \
                            || log "FAILED quant50 ep$ep seed$seed ($n/$N_QUANT) — $lg"
}

throttle() {
    while [ "$(jobs -rp | wc -l)" -ge "$N_PARALLEL" ]; do
        sleep 5
    done
}

# ---------- 1) 학습 종료 대기 ----------
log "학습 PID $TRAIN_PID 종료 대기..."
while kill -0 "$TRAIN_PID" 2>/dev/null; do sleep 60; done
log "학습 종료 확인. GPU 해제 대기(60s)..."
sleep 60
nvidia-smi --query-gpu=memory.free --format=csv,noheader

# ---------- 2) 병렬 실행 ----------
# [0813] final.pth는 epoch40 직후 저장된 동일 가중치라 중복 — 제외한다
# (어젯밤 실측에서도 epoch15와 final의 정량 수치가 완전히 일치했다).
# 이미 완료된 5/10/15는 job 내부 장수 체크로 자동 skip된다.
EPOCHS=${EPOCHS:-$(ls "$CKPT_DIR"/epoch_*_infer.pth 2>/dev/null \
         | sed -e 's|.*/epoch_||' -e 's|_infer\.pth$||' | sort -V)}
log "대상 체크포인트: $(echo $EPOCHS | tr "\n" " ")  (N_PARALLEL=$N_PARALLEL)"
log "PARALLEL_START"

for ep in $EPOCHS; do
    if [ "$ep" = "final" ]; then ckpt="$CKPT_DIR/final.pth"; else ckpt="$CKPT_DIR/epoch_${ep}.pth"; fi
    [ -f "${ckpt%.pth}_infer.pth" ] || { log "건너뜀: ${ckpt%.pth}_infer.pth 없음"; continue; }
    for seed in $SEEDS; do
        throttle; job_quant "$ckpt" "$ep" "$seed" &
        # [0813] 정성(color/gt)은 사용자가 별도 환경에서 수행 — 여기서는 정량만 돌린다.
        # job_color / job_gt 는 함수로 남겨둠(필요 시 아래 두 줄 주석 해제).
        # throttle; job_color "$ckpt" "$ep" "$seed" &
        # throttle; job_gt    "$ckpt" "$ep" "$seed" &
    done
done
wait
log "전체 inference 완료"

# ---------- 3) 정량지표 계산 ----------
log "정량지표 계산 시작"
cd /lambda/nfs/hairDiT
python3 scripts/eval/quant50_run7_phase2.py --epochs $EPOCHS \
    > "$LOGD/quant50_metrics.txt" 2>&1
log "정량지표 완료 -> $LOGD/quant50_metrics.txt"
tail -20 "$LOGD/quant50_metrics.txt"
log "ALL DONE"
