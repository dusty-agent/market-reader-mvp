from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
TEMPLATES = ROOT / "templates"
OUTPUT = ROOT / "output"

# =========================================================
# VIDEO
# =========================================================

FINAL_W = 1080
FINAL_H = 1920

FPS = 30

FX_SECONDS = 7
KEXIM_SECONDS = 7
ENDING_SECONDS = 6

VIDEO_SECONDS = (
    FX_SECONDS
    + KEXIM_SECONDS
    + ENDING_SECONDS
)