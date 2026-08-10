from __future__ import annotations

import argparse
import json

from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from dotenv import load_dotenv

from build_video import build_video
from collectors import fetch_all
from config import OUTPUT, ROOT
from render import render_pages


# =========================================================
# MAIN
# =========================================================

def main():

    # =====================================================
    # ENV
    # =====================================================

    load_dotenv(
        ROOT / ".env"
    )


    # =====================================================
    # DEFAULT BGM
    # =====================================================

    bgm = (
        ROOT
        / "assets"
        / "bgp.mp3"
    )


    # =====================================================
    # ARGUMENTS
    # =====================================================

    p = argparse.ArgumentParser(
        description="MarketReader Shorts generator"
    )


    p.add_argument(
        "--sample",
        action="store_true",
        help="Use sample_data.json instead of APIs",
    )


    p.add_argument(
        "--json",
        type=Path,
        help="Use a prepared market JSON",
    )


    p.add_argument(
        "--bgm",
        type=Path,
        help="Optional BGM file",
    )


    p.add_argument(
        "--frames-only",
        action="store_true",
        help="Render the three PNG pages only",
    )


    args = p.parse_args()


    # =====================================================
    # DATE / OUTPUT
    # =====================================================

    stamp = datetime.now(
        ZoneInfo("Asia/Seoul")
    ).strftime(
        "%Y-%m-%d"
    )


    day_dir = (
        OUTPUT
        / stamp
    )


    day_dir.mkdir(
        parents=True,
        exist_ok=True,
    )


    json_out = (
        day_dir
        / "market.json"
    )


    video_out = (
        day_dir
        / "market_reader.mp4"
    )


    # =====================================================
    # DATA
    # =====================================================

    if args.json:

        data = json.loads(
            args.json.read_text(
                encoding="utf-8",
            )
        )


    elif args.sample:

        data = json.loads(
            (
                ROOT
                / "sample_data.json"
            ).read_text(
                encoding="utf-8",
            )
        )


    else:

        data = fetch_all()


    # =====================================================
    # SAVE JSON
    # =====================================================

    json_out.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


    # =====================================================
    # RENDER
    #
    # FX
    # KEXIM
    # ENDING
    # =====================================================

    (
        fx_page,
        kexim_page,
        ending_page,
    ) = render_pages(
        data,
        day_dir,
    )


    print(
        f"[OK] FX     : {fx_page}"
    )

    print(
        f"[OK] KEXIM  : {kexim_page}"
    )

    print(
        f"[OK] ENDING : {ending_page}"
    )

    print(
        f"[OK] JSON   : {json_out}"
    )


    # =====================================================
    # VIDEO
    # =====================================================

    if not args.frames_only:

        # ---------------------------------------------
        # CLI에서 --bgm을 주면 그 파일 우선
        # ---------------------------------------------

        selected_bgm = (
            args.bgm
            if args.bgm
            else bgm
        )


        # ---------------------------------------------
        # BGM이 없으면 무음 영상
        # ---------------------------------------------

        if (
            selected_bgm is not None
            and not selected_bgm.exists()
        ):

            print(
                f"[WARN] BGM not found: "
                f"{selected_bgm}"
            )

            selected_bgm = None


        # ---------------------------------------------
        # Build 3-page video
        # ---------------------------------------------

        build_video(
            fx_page=fx_page,
            kexim_page=kexim_page,
            ending_page=ending_page,
            output=video_out,
            bgm=selected_bgm,
        )


        print(
            f"[OK] VIDEO  : {video_out}"
        )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()