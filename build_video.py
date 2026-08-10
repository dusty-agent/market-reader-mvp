from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from config import (
    FINAL_H,
    FINAL_W,
    FPS,
    FX_SECONDS,
    KEXIM_SECONDS,
    ENDING_SECONDS,
    VIDEO_SECONDS,
)


# =========================================================
# FFMPEG
# =========================================================

def _ffmpeg() -> str:

    configured = os.getenv(
        "FFMPEG_PATH",
        "",
    ).strip()

    if configured:
        return configured

    found = shutil.which(
        "ffmpeg"
    )

    if not found:
        raise RuntimeError(
            "ffmpeg not found. "
            "Install ffmpeg or set FFMPEG_PATH in .env"
        )

    return found


# =========================================================
# BUILD VIDEO
# =========================================================

def build_video(
    fx_page: Path,
    kexim_page: Path,
    ending_page: Path,
    output: Path,
    bgm: Path | None = None,
) -> Path:

    ffmpeg = _ffmpeg()

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    # =====================================================
    # Validate
    # =====================================================

    for path in (
        fx_page,
        kexim_page,
        ending_page,
    ):

        if not path.exists():
            raise FileNotFoundError(
                f"Image not found: {path}"
            )


    # =====================================================
    # Inputs
    # =====================================================

    cmd = [
        ffmpeg,
        "-y",

        # -------------------------------------------------
        # FX
        # -------------------------------------------------

        "-loop",
        "1",

        "-framerate",
        str(FPS),

        "-t",
        str(FX_SECONDS),

        "-i",
        str(fx_page),


        # -------------------------------------------------
        # KEXIM
        # -------------------------------------------------

        "-loop",
        "1",

        "-framerate",
        str(FPS),

        "-t",
        str(KEXIM_SECONDS),

        "-i",
        str(kexim_page),


        # -------------------------------------------------
        # ENDING
        # -------------------------------------------------

        "-loop",
        "1",

        "-framerate",
        str(FPS),

        "-t",
        str(ENDING_SECONDS),

        "-i",
        str(ending_page),
    ]


    # =====================================================
    # BGM
    # =====================================================

    has_bgm = (
        bgm is not None
        and bgm.exists()
    )


    if has_bgm:

        # BGM이 20초보다 짧아져도 안전하게 반복.
        # 현재 20초 BGM이라면 사실상 반복되지 않습니다.

        cmd += [
            "-stream_loop",
            "-1",

            "-i",
            str(bgm),
        ]


    # =====================================================
    # VIDEO FILTERS
    # =====================================================

    filter_parts = [

        # -------------------------------------------------
        # FX
        # -------------------------------------------------

        (
            f"[0:v]"
            f"scale={FINAL_W}:{FINAL_H},"
            f"setsar=1,"
            f"fps={FPS},"
            f"format=yuv420p"
            f"[v0]"
        ),


        # -------------------------------------------------
        # KEXIM
        # -------------------------------------------------

        (
            f"[1:v]"
            f"scale={FINAL_W}:{FINAL_H},"
            f"setsar=1,"
            f"fps={FPS},"
            f"format=yuv420p"
            f"[v1]"
        ),


        # -------------------------------------------------
        # ENDING
        # -------------------------------------------------

        (
            f"[2:v]"
            f"scale={FINAL_W}:{FINAL_H},"
            f"setsar=1,"
            f"fps={FPS},"
            f"format=yuv420p"
            f"[v2]"
        ),


        # -------------------------------------------------
        # CONCAT
        # -------------------------------------------------

        (
            "[v0][v1][v2]"
            "concat=n=3:v=1:a=0"
            "[v]"
        ),
    ]


    # =====================================================
    # AUDIO
    # =====================================================

    if has_bgm:

        # 마지막 1초 동안 fade-out
        #
        # 20초 영상이면
        # 19초부터 20초까지 fade-out

        fade_start = max(
            VIDEO_SECONDS - 1,
            0,
        )


        # BGM은 4번째 input이므로 [3:a]

        filter_parts.append(
            (
                "[3:a]"
                f"atrim=duration={VIDEO_SECONDS},"
                "asetpts=N/SR/TB,"
                f"afade=t=out:"
                f"st={fade_start}:"
                "d=1"
                "[a]"
            )
        )


    # =====================================================
    # FILTER COMPLEX
    # =====================================================

    filter_complex = ";".join(
        filter_parts
    )


    cmd += [
        "-filter_complex",
        filter_complex,

        "-map",
        "[v]",
    ]


    # =====================================================
    # AUDIO OUTPUT
    # =====================================================

    if has_bgm:

        cmd += [
            "-map",
            "[a]",

            "-c:a",
            "aac",

            "-b:a",
            "192k",
        ]

    else:

        cmd += [
            "-an",
        ]


    # =====================================================
    # FINAL OUTPUT
    # =====================================================

    cmd += [
        "-t",
        str(VIDEO_SECONDS),

        "-c:v",
        "libx264",

        "-pix_fmt",
        "yuv420p",

        "-r",
        str(FPS),

        "-movflags",
        "+faststart",

        str(output),
    ]


    # =====================================================
    # RUN
    # =====================================================

    print()
    print("====================================")
    print("Building MarketReader Video")
    print("====================================")
    print()
    print(
        f"FX      : {FX_SECONDS}s"
    )
    print(
        f"KEXIM   : {KEXIM_SECONDS}s"
    )
    print(
        f"ENDING  : {ENDING_SECONDS}s"
    )
    print(
        f"TOTAL   : {VIDEO_SECONDS}s"
    )
    print(
        f"BGM     : "
        f"{bgm if has_bgm else 'None'}"
    )
    print()


    subprocess.run(
        cmd,
        check=True,
    )


    print()
    print(
        f"✅ Video complete: {output}"
    )
    print()


    return output