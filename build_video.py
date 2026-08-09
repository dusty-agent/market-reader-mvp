from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from config import (
    FINAL_H,
    FINAL_W,
    FPS,
    PAGE1_SECONDS,
    PAGE2_SECONDS,
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

    found = shutil.which("ffmpeg")

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
    page1: Path,
    page2: Path,
    output: Path,
    bgm: Path | None = None,
) -> Path:

    ffmpeg = _ffmpeg()

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -----------------------------------------------------
    # Inputs
    # -----------------------------------------------------

    cmd = [
        ffmpeg,
        "-y",

        # Page 1
        "-loop",
        "1",
        "-framerate",
        str(FPS),
        "-t",
        str(PAGE1_SECONDS),
        "-i",
        str(page1),

        # Page 2
        "-loop",
        "1",
        "-framerate",
        str(FPS),
        "-t",
        str(PAGE2_SECONDS),
        "-i",
        str(page2),
    ]

    has_bgm = (
        bgm is not None
        and bgm.exists()
    )

    if has_bgm:

        # 음악이 영상보다 짧아지는 경우에도 대응
        cmd += [
            "-stream_loop",
            "-1",
            "-i",
            str(bgm),
        ]

    # -----------------------------------------------------
    # Video filters
    # -----------------------------------------------------

    filter_parts = [

        (
            f"[0:v]"
            f"scale={FINAL_W}:{FINAL_H},"
            f"setsar=1,"
            f"fps={FPS},"
            f"format=yuv420p"
            f"[v0]"
        ),

        (
            f"[1:v]"
            f"scale={FINAL_W}:{FINAL_H},"
            f"setsar=1,"
            f"fps={FPS},"
            f"format=yuv420p"
            f"[v1]"
        ),

        (
            "[v0][v1]"
            "concat=n=2:v=1:a=0"
            "[v]"
        ),
    ]

    # -----------------------------------------------------
    # Audio
    #
    # 영상 마지막 1초에 fade-out
    # 13초 영상 → 12초부터 fade-out
    # -----------------------------------------------------

    if has_bgm:

        fade_start = max(
            VIDEO_SECONDS - 1,
            0,
        )

        filter_parts.append(
            (
                "[2:a]"
                f"atrim=duration={VIDEO_SECONDS},"
                "asetpts=N/SR/TB,"
                f"afade=t=out:"
                f"st={fade_start}:"
                "d=1"
                "[a]"
            )
        )

    filter_complex = ";".join(
        filter_parts
    )

    cmd += [
        "-filter_complex",
        filter_complex,

        "-map",
        "[v]",
    ]

    # -----------------------------------------------------
    # Audio output
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Final output
    # -----------------------------------------------------

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

    subprocess.run(
        cmd,
        check=True,
    )

    return output