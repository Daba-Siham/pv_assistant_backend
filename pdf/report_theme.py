from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
FRONTEND_ROOT = PROJECT_ROOT / "final_PFA_frontend"
THEME_OVERRIDE_PATH = BACKEND_ROOT / "app" / "core" / "report_theme.json"


@dataclass(frozen=True)
class ReportTheme:
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text: str
    muted: str
    success: str
    warning: str
    danger: str
    border: str

    def color(self, name: str):
        return colors.HexColor(getattr(self, name))


# Tokens extracted from the frontend CSS design system:
# final_PFA_frontend/src/pages/home/HomePage.css
#   --blue-dark: #163b67
#   --yellow-accent: #f5a623
#   --yellow-hover: #e49b18
#   --bg-beige: #e9e6df
#   --text-brown: #6d6258
#   --white: #ffffff
# final_PFA_frontend/src/index.css provides dark-mode neutral tokens.
FRONTEND_THEME = ReportTheme(
    primary="#163b67",
    secondary="#0e2744",
    accent="#f5a623",
    background="#e9e6df",
    surface="#ffffff",
    text="#163b67",
    muted="#6d6258",
    success="#16a34a",
    warning="#f5a623",
    danger="#dc2626",
    border="#d1d5db",
)


def _load_override() -> dict[str, str]:
    if not THEME_OVERRIDE_PATH.exists():
        return {}

    try:
        payload = json.loads(THEME_OVERRIDE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    allowed = set(ReportTheme.__dataclass_fields__)
    return {key: value for key, value in payload.items() if key in allowed and value}


def get_theme_from_frontend() -> ReportTheme:
    values = FRONTEND_THEME.__dict__ | _load_override()
    return ReportTheme(**values)


def register_report_fonts() -> dict[str, str]:
    fonts_dir = Path("C:/Windows/Fonts")
    regular = fonts_dir / "arial.ttf"
    bold = fonts_dir / "arialbd.ttf"
    italic = fonts_dir / "ariali.ttf"

    if regular.exists():
        pdfmetrics.registerFont(TTFont("SolarAI-Regular", str(regular)))
    if bold.exists():
        pdfmetrics.registerFont(TTFont("SolarAI-Bold", str(bold)))
    if italic.exists():
        pdfmetrics.registerFont(TTFont("SolarAI-Italic", str(italic)))

    return {
        "regular": "SolarAI-Regular" if regular.exists() else "Helvetica",
        "bold": "SolarAI-Bold" if bold.exists() else "Helvetica-Bold",
        "italic": "SolarAI-Italic" if italic.exists() else "Helvetica-Oblique",
    }


THEME = get_theme_from_frontend()
REPORT_FONTS = register_report_fonts()

PRIMARY_COLOR = THEME.color("primary")
SECONDARY_COLOR = THEME.color("secondary")
ACCENT_COLOR = THEME.color("accent")
LIGHT_BG_COLOR = THEME.color("background")
SURFACE_COLOR = THEME.color("surface")
TEXT_COLOR = THEME.color("text")
MUTED_COLOR = THEME.color("muted")
SUCCESS_COLOR = THEME.color("success")
WARNING_COLOR = THEME.color("warning")
DANGER_COLOR = THEME.color("danger")
BORDER_COLOR = THEME.color("border")
