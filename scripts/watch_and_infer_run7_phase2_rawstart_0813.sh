#!/bin/bash
# run7_phase2_rawstart 체크포인트가 생길 때마다 자동으로 inference.
#
# 조합: 시드 42/1/2/3 × {color, gt} — gt는 두 번 나눠 돌려 한 폴더에 합친다.
#   color : dataset/test/sketch (11장) 원본 그대로
#   gt-A  : sketch_gt에 있는 7장은 sketch_gt 원본 사용 (recolor 플래그 없음)
#   gt-B  : sketch_gt에 없는 braid 4장만 --recolor_from_gt
#   → gt 폴더 최종 11장 (color와 장수 일치). CM_1082는 img/ 에 face가 없어 제외.
#
# 학습과 GPU를 공유한다. 실측상 학습 프로세스의 예약 메모리는 12.2GB 여유에서 고정이고
# (캐싱 할당자가 perceptual val peak까지 이미 확보 후 재사용) inference는 약 8.6GB를 쓴다.
# 그래도 안전을 위해 매 실행 전 여유 메모리를 확인하고, 부족하면 대기한다.
set -u

RUN=run7_phase2_rawstart
CKPT_DIR=/lambda/nfs/hairDiT/checkpoints/$RUN
CONFIG=/lambda/nfs/hairDiT/configs/run7_phase2_rawstart.yaml
OUT_ROOT=/lambda/nfs/hairDiT/outputs/0813/$RUN
STAGE=/lambda/nfs/hairDiT/outputs/0813/_gt_stage
MATTE=/lambda/nfs/hairDiT/dataset/test/matt
FACE=/lambda/nfs/hairDiT/dataset/test/img
SKETCH_COLOR=/lambda/nfs/hairDiT/dataset/test/sketch

SEEDS="42 1 2 3"
CFG_SCALE=2.0
FREE_MB_THRESHOLD=10000      # inference 소요 ~8600MB + 마진
PROCESSED=/lambda/nfs/hairDiT/outputs/0813/_processed_${RUN}.txt

N_COLOR=$(ls "$SKETCH_COLOR" | wc -l)          # 11
N_GT_A=$(ls "$STAGE/from_sketch_gt" | wc -l)   # 7
N_GT_B=$(ls "$STAGE/needs_recolor" | wc -l)    # 4
N_GT=$((N_GT_A + N_GT_B))                      # 11

mkdir -p "$OUT_ROOT"
touch "$PROCESSED"

log() { echo "[infer-$RUN] $(date -u +%H:%M:%S) $*"; }

wait_for_gpu() {
    while true; do
        free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null || echo 0)
        [ "$free" -ge "$FREE_MB_THRESHOLD" ] && return 0
        sleep 20
    done
}

# $1=ckpt  $2=sketch_dir  $3=out_dir  $4=logfile  $5=seed  $6=extra_args
run_infer() {
    wait_for_gpu
    python3 /lambda/nfs/hairDiT/scripts/infer_custom.py \
        --sketch "$2" --matte "$MATTE" --face "$FACE" \
        --checkpoint "$1" --config "$CONFIG" \
        --num_steps 20 --seed "$5" \
        --bld_mode full --bld_soft_steps 18 \
        --pixel_blend --pixel_blend_alpha 0.75 \
        --cfg_scale "$CFG_SCALE" \
        $6 \
        --output_dir "$3" \
        >> "$4" 2>&1
}

process_epoch() {
    local ckpt="$1" ep="$2"
    for seed in $SEEDS; do
        # ---------- color ----------
        key="${ep}_color_seed${seed}"
        if ! grep -qx "$key" "$PROCESSED"; then
            out="$OUT_ROOT/color/$seed/epoch${ep}"
            lg="$OUT_ROOT/${ep}_color_seed${seed}.log"
            log "epoch$ep color seed$seed -> $out"
            run_infer "$ckpt" "$SKETCH_COLOR" "$out" "$lg" "$seed" ""
            n=$(ls "$out" 2>/dev/null | wc -l)
            if [ "$n" -ge "$N_COLOR" ]; then
                echo "$key" >> "$PROCESSED"; log "  done color seed$seed ($n/$N_COLOR)"
            else
                log "  FAILED color seed$seed ($n/$N_COLOR) — 다음 패스에서 재시도 (로그: $lg)"
            fi
        fi

        # ---------- gt (A: sketch_gt 원본 + B: recolor) ----------
        key="${ep}_gt_seed${seed}"
        if ! grep -qx "$key" "$PROCESSED"; then
            out="$OUT_ROOT/gt/$seed/epoch${ep}"
            lg="$OUT_ROOT/${ep}_gt_seed${seed}.log"
            log "epoch$ep gt seed$seed (A:sketch_gt ${N_GT_A}장) -> $out"
            run_infer "$ckpt" "$STAGE/from_sketch_gt" "$out" "$lg" "$seed" ""
            log "epoch$ep gt seed$seed (B:recolor ${N_GT_B}장) -> $out"
            run_infer "$ckpt" "$STAGE/needs_recolor" "$out" "$lg" "$seed" "--recolor_from_gt"
            n=$(ls "$out" 2>/dev/null | wc -l)
            if [ "$n" -ge "$N_GT" ]; then
                echo "$key" >> "$PROCESSED"; log "  done gt seed$seed ($n/$N_GT)"
            else
                log "  FAILED gt seed$seed ($n/$N_GT) — 다음 패스에서 재시도 (로그: $lg)"
            fi
        fi
    done
}

log "시작 — watching $CKPT_DIR (color ${N_COLOR}장 / gt ${N_GT_A}+${N_GT_B}=${N_GT}장)"
while true; do
    for ckpt in $(ls "$CKPT_DIR"/epoch_*.pth "$CKPT_DIR"/final.pth 2>/dev/null \
                  | grep -v '_infer\.pth$' | sort -V); do
        [ -e "$ckpt" ] || continue
        base=$(basename "$ckpt" .pth)
        ep=${base#epoch_}                       # final.pth면 "final"
        # _infer.pth 가 있고 크기가 안정된 것만 (저장 중 파일 회피)
        inf="${ckpt%.pth}_infer.pth"
        [ -f "$inf" ] || continue
        s1=$(stat -c%s "$inf" 2>/dev/null || echo 0); sleep 5
        s2=$(stat -c%s "$inf" 2>/dev/null || echo 0)
        [ "$s1" = "$s2" ] && [ "$s1" != "0" ] || continue

        process_epoch "$ckpt" "$ep"
    done

    # 학습이 끝났고 final.pth 조합까지 전부 처리됐으면 종료
    if [ -f "$CKPT_DIR/final.pth" ]; then
        remaining=0
        for seed in $SEEDS; do
            grep -qx "final_color_seed${seed}" "$PROCESSED" || remaining=1
            grep -qx "final_gt_seed${seed}"    "$PROCESSED" || remaining=1
        done
        if [ "$remaining" -eq 0 ]; then
            log "모든 체크포인트 처리 완료 — 종료"
            break
        fi
    fi
    sleep 30
done
