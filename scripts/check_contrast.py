"""WCAG 2.1 AA Contrast Ratio Verification Script for MailGuard AI.

Calculates relative luminance and contrast ratio according to the W3C WCAG 2.1 specification:
https://www.w3.org/WAI/GL/wiki/Relative_luminance
https://www.w3.org/WAI/GL/wiki/Contrast_ratio

No external dependencies. Reads static/css/style.css and evaluates foreground/background
pairings across both light and dark themes.
"""

from pathlib import Path
import re
import sys
from typing import Dict, List, NamedTuple, Optional, Tuple


class ContrastResult(NamedTuple):
    theme: str
    element: str
    fg_var: str
    fg_hex: str
    bg_var: str
    bg_hex: str
    ratio: float
    required: float
    passed: bool


def srgb_to_linear(val_255: float) -> float:
    """Convert 8-bit sRGB channel to linear light value."""
    c = val_255 / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Parse #rgb or #rrggbb hex color string to (r, g, b) tuple."""
    h = hex_code.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        raise ValueError(f"Invalid hex color: {hex_code}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def relative_luminance(hex_code: str) -> float:
    """Calculate WCAG relative luminance from hex color string."""
    r, g, b = hex_to_rgb(hex_code)
    r_lin = srgb_to_linear(r)
    g_lin = srgb_to_linear(g)
    b_lin = srgb_to_linear(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculate contrast ratio between two hex colors (always >= 1.0)."""
    l1 = relative_luminance(hex1)
    l2 = relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def parse_css_variables(css_text: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Parse CSS variable mappings from :root (light) and [data-theme="dark"] blocks."""
    # Strip comments first
    cleaned_css = re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)

    light_vars: Dict[str, str] = {}
    dark_vars: Dict[str, str] = {}

    # Extract :root block
    root_match = re.search(r":root\s*\{([^}]+)\}", cleaned_css)
    if root_match:
        for line in root_match.group(1).split(";"):
            line = line.strip()
            if line.startswith("--"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    k = parts[0].strip()
                    v = parts[1].strip()
                    light_vars[k] = v

    # Extract [data-theme="dark"] block
    dark_match = re.search(r'\[data-theme=["\']dark["\']\]\s*\{([^}]+)\}', cleaned_css)
    if dark_match:
        for line in dark_match.group(1).split(";"):
            line = line.strip()
            if line.startswith("--"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    k = parts[0].strip()
                    v = parts[1].strip()
                    dark_vars[k] = v

    # Fallback to light values if dark block does not override
    merged_dark = dict(light_vars)
    merged_dark.update(dark_vars)

    return light_vars, merged_dark


def evaluate_stylesheet(css_path: Path) -> List[ContrastResult]:
    """Evaluate contrast of defined foreground/background pairs in stylesheet."""
    if not css_path.exists():
        raise FileNotFoundError(f"Stylesheet not found: {css_path}")

    css_text = css_path.read_text(encoding="utf-8")
    light_vars, dark_vars = parse_css_variables(css_text)

    # Core UI text pairings to verify: (theme, element_name, fg_var, bg_var, req_ratio)
    rules = [
        # Light Theme Pairs (Normal text >= 4.5:1, UI elements >= 3.0:1)
        ("light", "Body / Primary Text", "--color-text-main", "--color-surface", 4.5),
        ("light", "Canvas Body Text", "--color-text-main", "--color-bg", 4.5),
        ("light", "Muted Helper Text", "--color-text-muted", "--color-surface", 4.5),
        ("light", "Primary Action Button", "--color-text-inverse", "--color-primary", 4.5),
        ("light", "Interactive Links", "--color-primary", "--color-surface", 4.5),
        ("light", "Spam Verdict Text", "--color-spam", "--color-surface", 4.5),
        ("light", "Spam Alert Box Text", "--color-spam", "--color-spam-bg", 4.5),
        ("light", "Legitimate Verdict Text", "--color-ham", "--color-surface", 4.5),
        ("light", "Legitimate Alert Box Text", "--color-ham", "--color-ham-bg", 4.5),
        ("light", "Uncertain / Review Text", "--color-uncertain", "--color-surface", 4.5),
        ("light", "Uncertain Alert Box Text", "--color-uncertain", "--color-uncertain-bg", 4.5),
        # Dark Theme Pairs
        ("dark", "Body / Primary Text", "--color-text-main", "--color-surface", 4.5),
        ("dark", "Canvas Body Text", "--color-text-main", "--color-bg", 4.5),
        ("dark", "Muted Helper Text", "--color-text-muted", "--color-surface", 4.5),
        ("dark", "Primary Action Button", "--color-primary-text", "--color-primary", 4.5),
        ("dark", "Interactive Links", "--color-primary", "--color-surface", 4.5),
        ("dark", "Spam Verdict Text", "--color-spam", "--color-surface", 4.5),
        ("dark", "Spam Alert Box Text", "--color-spam", "--color-spam-bg", 4.5),
        ("dark", "Legitimate Verdict Text", "--color-ham", "--color-surface", 4.5),
        ("dark", "Legitimate Alert Box Text", "--color-ham", "--color-ham-bg", 4.5),
        ("dark", "Uncertain / Review Text", "--color-uncertain", "--color-surface", 4.5),
        ("dark", "Uncertain Alert Box Text", "--color-uncertain", "--color-uncertain-bg", 4.5),
    ]

    results: List[ContrastResult] = []

    for theme, elem, fg_var, bg_var, req in rules:
        vars_map = light_vars if theme == "light" else dark_vars
        fg_hex = vars_map.get(fg_var)
        bg_hex = vars_map.get(bg_var)

        if not fg_hex or not bg_hex:
            # Missing variable
            results.append(
                ContrastResult(
                    theme=theme,
                    element=elem,
                    fg_var=fg_var,
                    fg_hex=str(fg_hex),
                    bg_var=bg_var,
                    bg_hex=str(bg_hex),
                    ratio=0.0,
                    required=req,
                    passed=False,
                )
            )
            continue

        try:
            ratio = contrast_ratio(fg_hex, bg_hex)
            passed = ratio >= req
        except Exception:
            ratio = 0.0
            passed = False

        results.append(
            ContrastResult(
                theme=theme,
                element=elem,
                fg_var=fg_var,
                fg_hex=fg_hex,
                bg_var=bg_var,
                bg_hex=bg_hex,
                ratio=round(ratio, 2),
                required=req,
                passed=passed,
            )
        )

    return results


def print_contrast_report(results: List[ContrastResult]) -> bool:
    """Print an aligned table of contrast verification results."""
    print("=" * 86)
    print("MAILGUARD AI - WCAG 2.1 AA COLOR CONTRAST VERIFICATION REPORT")
    print("=" * 86)
    header = f"{'Theme':<7} | {'Element / Component':<28} | {'FG Hex':<8} | {'BG Hex':<8} | {'Ratio':<7} | {'Req':<5} | {'Status':<6}"
    print(header)
    print("-" * 86)

    all_passed = True
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        if not r.passed:
            all_passed = False
        print(
            f"{r.theme:<7} | {r.element:<28} | {r.fg_hex:<8} | {r.bg_hex:<8} | {r.ratio:>5.2f}:1 | {r.required:>4.1f} | [{status}]"
        )

    print("=" * 86)
    if all_passed:
        print("ALL PAIRS PASS WCAG 2.1 AA REQUIREMENTS (Zero Contrast Failures)")
    else:
        print("ONE OR MORE COLOR PAIRS FAILED WCAG 2.1 AA REQUIREMENTS")
    print("=" * 86)
    return all_passed


def main() -> int:
    css_path = Path(__file__).resolve().parent.parent / "static" / "css" / "style.css"
    results = evaluate_stylesheet(css_path)
    passed = print_contrast_report(results)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
