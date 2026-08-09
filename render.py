from __future__ import annotations

import base64
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Any, Dict

from playwright.sync_api import sync_playwright

from config import (
    ASSETS,
    FINAL_H,
    FINAL_W,
    TEMPLATES,
)


# =========================================================
# FORMAT
# =========================================================

def _format_value(
    name: str,
    value: Any,
) -> str:

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"

    if name == "JPY/KRW":
        return f"{number:,.4f}"

    return f"{number:,.2f}"


def _format_rate(
    value: Any,
) -> str:

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"

    return f"{number:.2f}%"


def _change_parts(
    value: Any,
) -> tuple[str, str, str]:

    try:
        number = float(value)
    except (TypeError, ValueError):
        return (
            "flat",
            "―",
            "0.00%",
        )

    if number > 0:

        return (
            "up",
            "▲",
            f"+{number:.2f}%",
        )

    if number < 0:

        return (
            "down",
            "▼",
            f"{number:.2f}%",
        )

    return (
        "flat",
        "―",
        "0.00%",
    )


# =========================================================
# SOURCE
# =========================================================

def _source_label(
    data: Dict[str, Any],
) -> str:

    sources = (
        data.get("sources")
        or {}
    )

    values = []

    for key in (
        "FX",
        "LOAN",
        "GLOBAL",
    ):

        value = sources.get(key)

        if (
            value
            and value not in values
        ):
            values.append(value)

    if not values:
        return "SOURCE PENDING"

    return " · ".join(values)


# =========================================================
# ASSET
# =========================================================

def _asset_data_uri(
    stem: str,
) -> str:

    candidates = (
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    )

    for ext in candidates:

        path = (
            ASSETS
            / f"{stem}{ext}"
        )

        if path.exists():

            mime = (
                mimetypes.guess_type(
                    str(path)
                )[0]
                or "application/octet-stream"
            )

            payload = (
                base64.b64encode(
                    path.read_bytes()
                )
                .decode("ascii")
            )

            return (
                f"data:{mime};base64,"
                f"{payload}"
            )

    # fallback dark background

    svg = """
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="1080"
        height="1920"
    >
        <rect
            width="1080"
            height="1920"
            fill="#07121e"
        />
    </svg>
    """

    payload = (
        base64.b64encode(
            svg.encode("utf-8")
        )
        .decode("ascii")
    )

    return (
        "data:image/svg+xml;base64,"
        + payload
    )


def _font_data_uri(
    filename: str,
) -> str:

    path = (
        ASSETS
        / filename
    )

    if not path.exists():

        raise FileNotFoundError(
            f"Font not found: {path}"
        )

    payload = (
        base64.b64encode(
            path.read_bytes()
        )
        .decode("ascii")
    )

    return (
        "data:font/ttf;base64,"
        + payload
    )


def _load_css(
    filename: str,
) -> str:

    path = (
        TEMPLATES
        / filename
    )

    if not path.exists():

        raise FileNotFoundError(
            f"CSS not found: {path}"
        )

    return path.read_text(
        encoding="utf-8"
    )


# =========================================================
# LOAN RATE HELPERS
# =========================================================

def _loan_rate_map(
    data: Dict[str, Any],
) -> Dict[str, Any]:

    loan_data = (
        data.get("loan_rates")
        or {}
    )

    items = (
        loan_data.get("items")
        or []
    )

    result: Dict[str, Any] = {}

    for item in items:

        name = str(
            item.get(
                "name",
                "",
            )
        ).strip()

        value = item.get(
            "value"
        )

        if name:
            result[name] = value

    return result


def _loan_value(
    rates: Dict[str, Any],
    term: str,
) -> str:

    key = (
        f"수은채 유통수익률 {term}"
    )

    return _format_rate(
        rates.get(key)
    )


# =========================================================
# PAGE 1 TOKENS
# =========================================================

def _replace_market_tokens(
    template: str,
    data: Dict[str, Any],
) -> str:

    result = template

    # -----------------------------------------
    # CSS
    # -----------------------------------------

    page1_css = _load_css(
        "page_1.css"
    )

    result = result.replace(
        "{{PAGE1_CSS}}",
        page1_css,
    )

    # -----------------------------------------
    # FONT
    # -----------------------------------------

    result = result.replace(
        "{{PRETENDARD_FONT}}",
        _font_data_uri(
            "PretendardVariable.ttf"
        ),
    )

    # -----------------------------------------
    # BASIC
    # -----------------------------------------

    result = result.replace(
        "{{AS_OF}}",
        str(
            data.get(
                "as_of",
                "",
            )
        ),
    )

    result = result.replace(
        "{{SOURCE}}",
        _source_label(data),
    )

    result = result.replace(
        "{{PAGE1_BG}}",
        _asset_data_uri(
            "page1_bg"
        ),
    )

    # -----------------------------------------
    # FX
    # -----------------------------------------

    items = (
        data.get("items")
        or {}
    )

    for name in (
        "USD/KRW",
        "JPY/KRW",
        "EUR/KRW",
    ):

        item = (
            items.get(name)
            or {}
        )

        token = (
            name
            .replace("/", "_")
        )

        result = result.replace(
            f"{{{{{token}_VALUE}}}}",
            _format_value(
                name,
                item.get("value"),
            ),
        )

        (
            css_class,
            arrow,
            change,
        ) = _change_parts(
            item.get(
                "change_pct"
            )
        )

        result = result.replace(
            f"{{{{{token}_CLASS}}}}",
            css_class,
        )

        result = result.replace(
            f"{{{{{token}_ARROW}}}}",
            arrow,
        )

        result = result.replace(
            f"{{{{{token}_CHANGE}}}}",
            change,
        )

    # -----------------------------------------
    # FX DATE
    # -----------------------------------------

    fx_date = "—"

    usd = (
        items.get("USD/KRW")
        or {}
    )

    if usd.get("source_date"):

        fx_date = str(
            usd["source_date"]
        )

    result = result.replace(
        "{{FX_DATE}}",
        fx_date,
    )

    # -----------------------------------------
    # LOAN RATE
    # -----------------------------------------

    loan_rates = (
        _loan_rate_map(data)
    )

    result = result.replace(
        "{{LOAN_1M_VALUE}}",
        _loan_value(
            loan_rates,
            "1개월",
        ),
    )

    result = result.replace(
        "{{LOAN_1Y_VALUE}}",
        _loan_value(
            loan_rates,
            "1년",
        ),
    )

    result = result.replace(
        "{{LOAN_3Y_VALUE}}",
        _loan_value(
            loan_rates,
            "3년",
        ),
    )

    result = result.replace(
        "{{LOAN_5Y_VALUE}}",
        _loan_value(
            loan_rates,
            "5년",
        ),
    )

    result = result.replace(
        "{{LOAN_10Y_VALUE}}",
        _loan_value(
            loan_rates,
            "10년",
        ),
    )

    # -----------------------------------------
    # LOAN DATE
    # -----------------------------------------

    loan_data = (
        data.get("loan_rates")
        or {}
    )

    loan_date = str(
        loan_data.get(
            "source_date",
            "—",
        )
    )

    result = result.replace(
        "{{LOAN_DATE}}",
        loan_date,
    )

    return result


# =========================================================
# PAGE 2 TOKENS
# =========================================================

def _replace_ending_tokens(
    template: str,
) -> str:

    result = template

    page2_css = _load_css(
        "page_2.css"
    )

    result = result.replace(
        "{{PAGE2_CSS}}",
        page2_css,
    )

    result = result.replace(
        "{{PRETENDARD_FONT}}",
        _font_data_uri(
            "PretendardVariable.ttf"
        ),
    )

    result = result.replace(
        "{{PAGE2_BG}}",
        _asset_data_uri(
            "page2_bg"
        ),
    )

    result = result.replace(
        "{{PAGE2_CTA_BG}}",
        _asset_data_uri(
            "page2_cta_bg"
        ),
    )

    return result


# =========================================================
# BROWSER
# =========================================================

def _browser_executable() -> str | None:

    configured = (
        os.getenv(
            "CHROME_PATH",
            "",
        )
        .strip()
        .strip('"')
    )

    if (
        configured
        and Path(
            configured
        ).exists()
    ):
        return configured

    candidates = [
        shutil.which(
            "chrome"
        ),
        shutil.which(
            "google-chrome"
        ),
        shutil.which(
            "chromium"
        ),
        shutil.which(
            "msedge"
        ),
    ]

    for candidate in candidates:

        if candidate:
            return candidate

    return None


# =========================================================
# SCREENSHOT
# =========================================================

def _screenshot_html(
    html_text: str,
    output_path: Path,
) -> None:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    executable = (
        _browser_executable()
    )

    with sync_playwright() as p:

        launch_kwargs = {
            "headless": True,
        }

        if executable:

            launch_kwargs[
                "executable_path"
            ] = executable

        browser = (
            p.chromium.launch(
                **launch_kwargs
            )
        )

        page = browser.new_page(
            viewport={
                "width": FINAL_W,
                "height": FINAL_H,
            },
            device_scale_factor=1,
        )

        page.set_content(
            html_text,
            wait_until="load",
        )

        # Pretendard 로딩 완료까지 대기
        page.wait_for_function(
            "document.fonts.status === 'loaded'"
        )

        page.screenshot(
            path=str(
                output_path
            ),
            full_page=False,
        )

        browser.close()


# =========================================================
# RENDER
# =========================================================

def render_pages(
    data: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Path]:

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    page1_template = (
        TEMPLATES
        / "page_1.html"
    ).read_text(
        encoding="utf-8"
    )

    page2_template = (
        TEMPLATES
        / "page_2.html"
    ).read_text(
        encoding="utf-8"
    )

    page1_html = (
        _replace_market_tokens(
            page1_template,
            data,
        )
    )

    page2_html = (
        _replace_ending_tokens(
            page2_template,
        )
    )

    page1_html_path = (
        output_dir
        / "page_1.html"
    )

    page2_html_path = (
        output_dir
        / "page_2.html"
    )

    page1_png_path = (
        output_dir
        / "page_1.png"
    )

    page2_png_path = (
        output_dir
        / "page_2.png"
    )

    page1_html_path.write_text(
        page1_html,
        encoding="utf-8",
    )

    page2_html_path.write_text(
        page2_html,
        encoding="utf-8",
    )

    _screenshot_html(
        page1_html,
        page1_png_path,
    )

    _screenshot_html(
        page2_html,
        page2_png_path,
    )

    return (
        page1_png_path,
        page2_png_path,
    )