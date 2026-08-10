from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from render import (
    _replace_market_tokens,
    _screenshot_html,
)

from build_video import build_video


# =========================================================
# PATH
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

TEMPLATES = (
    ROOT
    / "templates"
)


# =========================================================
# ENV
# =========================================================

load_dotenv(
    ROOT / ".env"
)


# =========================================================
# MAIN
# =========================================================

def main():

    # =====================================================
    # DATE
    # =====================================================

    date = "2026-08-10"

    day_dir = (
        ROOT
        / "output"
        / date
    )


    # =====================================================
    # EXISTING JSON
    # =====================================================

    json_path = (
        day_dir
        / "market.json"
    )


    if not json_path.exists():

        raise FileNotFoundError(
            f"market.json not found: {json_path}"
        )


    print()
    print("====================================")
    print("MarketReader Video Rebuild")
    print("====================================")
    print()
    print(f"DATE : {date}")
    print(f"JSON : {json_path}")
    print()


    data = json.loads(
        json_path.read_text(
            encoding="utf-8",
        )
    )


    # =====================================================
    # TEMPLATE PATH
    # =====================================================

    fx_template_path = (
        TEMPLATES
        / "page_1_fx.html"
    )


    kexim_template_path = (
        TEMPLATES
        / "page_1_kexim.html"
    )


    if not fx_template_path.exists():

        raise FileNotFoundError(
            f"FX template not found: "
            f"{fx_template_path}"
        )


    if not kexim_template_path.exists():

        raise FileNotFoundError(
            f"KEXIM template not found: "
            f"{kexim_template_path}"
        )


    # =====================================================
    # LOAD TEMPLATE
    # =====================================================

    fx_template = (
        fx_template_path
        .read_text(
            encoding="utf-8",
        )
    )


    kexim_template = (
        kexim_template_path
        .read_text(
            encoding="utf-8",
        )
    )


    # =====================================================
    # REPLACE TOKENS
    #
    # 기존 market.json 그대로 사용
    # =====================================================

    fx_html = (
        _replace_market_tokens(
            fx_template,
            data,
        )
    )


    kexim_html = (
        _replace_market_tokens(
            kexim_template,
            data,
        )
    )


    # =====================================================
    # OUTPUT PATH
    # =====================================================

    fx_html_path = (
        day_dir
        / "fx.html"
    )


    fx_png_path = (
        day_dir
        / "fx.png"
    )


    kexim_html_path = (
        day_dir
        / "kexim.html"
    )


    kexim_png_path = (
        day_dir
        / "kexim.png"
    )


    # =====================================================
    # WRITE HTML
    # =====================================================

    fx_html_path.write_text(
        fx_html,
        encoding="utf-8",
    )


    kexim_html_path.write_text(
        kexim_html,
        encoding="utf-8",
    )


    # =====================================================
    # SCREENSHOT
    # =====================================================

    print("Rendering FX...")


    _screenshot_html(
        fx_html,
        fx_png_path,
    )


    print(
        f"[OK] FX     : {fx_png_path}"
    )


    print("Rendering KEXIM...")


    _screenshot_html(
        kexim_html,
        kexim_png_path,
    )


    print(
        f"[OK] KEXIM  : {kexim_png_path}"
    )


    # =====================================================
    # ENDING
    #
    # 오늘은 기존 page_2.png 재사용
    # =====================================================

    ending_png_path = (
        day_dir
        / "page_2.png"
    )


    if not ending_png_path.exists():

        raise FileNotFoundError(
            "기존 Ending PNG를 찾을 수 없습니다: "
            f"{ending_png_path}"
        )


    print(
        f"[OK] ENDING : {ending_png_path}"
    )


    # =====================================================
    # BGM
    # =====================================================

    bgm_path = (
        ROOT
        / "assets"
        / "bgp.mp3"
    )


    if not bgm_path.exists():

        print()
        print(
            f"[WARN] BGM not found: "
            f"{bgm_path}"
        )

        print(
            "영상은 무음으로 생성합니다."
        )

        bgm_path = None

    else:

        print(
            f"[OK] BGM    : {bgm_path}"
        )


    # =====================================================
    # VIDEO
    # =====================================================

    video_path = (
        day_dir
        / "market_reader.mp4"
    )


    print()
    print("Building video...")
    print()


    build_video(
        fx_page=fx_png_path,
        kexim_page=kexim_png_path,
        ending_page=ending_png_path,
        output=video_path,
        bgm=bgm_path,
    )


    # =====================================================
    # COMPLETE
    # =====================================================

    print()
    print("====================================")
    print("COMPLETE")
    print("====================================")
    print()
    print(
        f"[OK] video : {video_path}"
    )
    print()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()