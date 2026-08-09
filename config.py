from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
TEMPLATES = ROOT / "templates"
OUTPUT = ROOT / "output"

FINAL_W = 1080
FINAL_H = 1920
FPS = 30

# 15-second short: enough time to scan 7 rows + a short closing card.
PAGE1_SECONDS = 10
PAGE2_SECONDS = 3
VIDEO_SECONDS = PAGE1_SECONDS + PAGE2_SECONDS

# Change only these if you want a 10-second version later:
# PAGE1_SECONDS = 7
# PAGE2_SECONDS = 3
