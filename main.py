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


def main():
    load_dotenv(ROOT / ".env")
    bgm = Path("assets/bgm.mp3")

    p = argparse.ArgumentParser(description="MarketReader Shorts generator")
    p.add_argument("--sample", action="store_true", help="Use sample_data.json instead of APIs")
    p.add_argument("--json", type=Path, help="Use a prepared market JSON")
    p.add_argument("--bgm", type=Path, help="Optional BGM file")
    p.add_argument("--frames-only", action="store_true", help="Render the two PNG pages only")
    args = p.parse_args()

    stamp = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
    day_dir = OUTPUT / stamp
    day_dir.mkdir(parents=True, exist_ok=True)

    json_out = day_dir / "market.json"
    video_out = day_dir / "market_reader.mp4"

    if args.json:
        data = json.loads(args.json.read_text(encoding="utf-8"))
    elif args.sample:
        data = json.loads((ROOT / "sample_data.json").read_text(encoding="utf-8"))
    else:
        data = fetch_all()

    json_out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    page1, page2 = render_pages(data, day_dir)
    print(f"[OK] page 1: {page1}")
    print(f"[OK] page 2: {page2}")
    print(f"[OK] json  : {json_out}")

    if not args.frames_only:
        build_video(page1, page2, video_out, bgm=bgm)
        print(f"[OK] video : {video_out}")


if __name__ == "__main__":
    main()
