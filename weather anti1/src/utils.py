"""
WeatherGPT Utility Functions
============================
Helper utilities for UI rendering:
- Converts markdown formatting (bold, bullets, code) to clean HTML
- Renders two-sided chat bubbles (User on right, WeatherGPT on left)
"""

import re
from datetime import datetime


def markdown_to_html(text: str) -> str:
    """
    Converts basic markdown formatting into clean HTML:
    - **bold text** -> <strong>bold text</strong>
    - *italic text* -> <em>italic text</em>
    - `inline code` -> <code>inline code</code>
    - Bullet lists (•, -, *) -> <ul><li>...</li></ul>
    - Headings (##, ###) -> styled div headings
    """
    lines = text.strip().split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        line_s = line.strip()

        # Handle empty lines (spacing)
        if not line_s:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<div style='height: 6px;'></div>")
            continue

        # Format markdown syntax: bold, italic, code
        line_formatted = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line_s)
        line_formatted = re.sub(r"\*(.*?)\*", r"<em>\1</em>", line_formatted)
        line_formatted = re.sub(
            r"`(.*?)`",
            r"<code style='background:#f1f5f9; padding:2px 5px; border-radius:4px; font-size:0.9em; color:#0f172a;'>\1</code>",
            line_formatted
        )

        # Bullet list items
        if line_s.startswith("• ") or line_s.startswith("- ") or line_s.startswith("* "):
            if not in_list:
                html_lines.append("<ul style='margin: 4px 0 8px 1.2rem; padding: 0; list-style-type: disc;'>")
                in_list = True
            bullet_content = line_formatted[2:].strip()
            html_lines.append(f"<li style='margin-bottom: 3px; color: #1e293b;'>{bullet_content}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False

            # Section headings
            if line_s.startswith("### "):
                html_lines.append(f"<div style='font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-bottom: 6px;'>{line_formatted[4:]}</div>")
            elif line_s.startswith("## "):
                html_lines.append(f"<div style='font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-bottom: 8px;'>{line_formatted[3:]}</div>")
            else:
                html_lines.append(f"<div style='margin-bottom: 4px;'>{line_formatted}</div>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def render_chat_bubble_html(role: str, content: str, tag: str = "Forecast", timestamp: str = "") -> str:
    """
    Renders styled chat cards for the conversation interface:
    - User message: aligned to the RIGHT in a light green bubble
    - WeatherGPT message: aligned to the LEFT in a clean white card with an 'Offline ML' badge
    """
    if not timestamp:
        timestamp = datetime.now().strftime("%H:%M")

    body_html = markdown_to_html(content)

    if role == "user":
        # User message: aligned to the right
        return f"""
        <div style="display: flex; justify-content: flex-end; width: 100%; margin: 8px 0 14px 0;">
            <div style="background-color: #dcfce7; color: #111827; padding: 12px 18px; border-radius: 14px; max-width: 75%; min-width: 220px; box-shadow: 0 2px 6px rgba(0,0,0,0.18); border: 1px solid #bbf7d0;">
                <div style="font-size: 0.8rem; font-weight: 600; color: #15803d; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    <span>👤 You</span>
                    <span style="font-weight: 400; color: #4b5563; font-size: 0.75rem;">({timestamp})</span>
                </div>
                <div style="font-size: 0.98rem; font-weight: 500; color: #0f172a; line-height: 1.45;">
                    {body_html}
                </div>
            </div>
        </div>
        """
    else:
        # WeatherGPT assistant message: aligned to the left
        return f"""
        <div style="display: flex; justify-content: flex-start; width: 100%; margin: 8px 0 18px 0;">
            <div style="background-color: #ffffff; color: #1e293b; padding: 14px 20px; border-radius: 14px; max-width: 85%; min-width: 300px; width: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.22); border: 1px solid #e2e8f0;">
                <div style="font-size: 0.84rem; font-weight: 600; color: #475569; margin-bottom: 8px; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span>☁️ WeatherGPT</span>
                        <span style="color: #64748b; font-weight: 400;">— {tag} ({timestamp})</span>
                    </div>
                    <span style="font-size: 0.72rem; background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; padding: 2px 8px; border-radius: 9999px; font-weight: 600;">Offline ML</span>
                </div>
                <div style="font-size: 0.95rem; line-height: 1.6; color: #1e293b;">
                    {body_html}
                </div>
            </div>
        </div>
        """
