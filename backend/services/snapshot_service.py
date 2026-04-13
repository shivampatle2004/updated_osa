"""
snapshot_service.py
───────────────────
Takes a pixel-perfect screenshot of the dashboard using Playwright's
headless Chromium browser — exactly what the user sees on screen.

Output: A PNG image saved under backend/exports/, served for download
        via GET /api/power-automate/download/{workflow_id}
"""

import asyncio
import os
from pathlib import Path

# Saved screenshots go here
EXPORTS_DIR = Path(__file__).parent.parent / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


async def capture_snapshot_pdf(workflow_id: str, url: str) -> str:
    """
    Navigate to `url` inside a headless browser and take a full-page
    screenshot that looks exactly like the visible screen.

    Args:
        workflow_id: Used to name the output file uniquely.
        url:         The full dashboard URL, e.g.
                     http://localhost:8000/?fileId=abc&fileName=sales.csv

    Returns:
        Absolute path to the saved PNG file.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    # Save as .png  (more "screen-like" than PDF)
    output_path = str(EXPORTS_DIR / f"snapshot_{workflow_id}.png")

    print(f"[SnapshotService] 📸 Opening: {url}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        context = await browser.new_context(
            # Match a standard 1440×900 desktop monitor — the same as the user's screen
            viewport={"width": 1440, "height": 900},
            # Retina-quality pixel ratio for crisp screenshots
            device_scale_factor=1.5,
        )

        page = await context.new_page()

        try:
            # Navigate to the exact URL the user is viewing
            await page.goto(url, wait_until="networkidle", timeout=30_000)

            # Wait for charts and animations to finish rendering
            await asyncio.sleep(3)

            # Take a full-page screenshot (scrolls and stitches the whole page)
            await page.screenshot(
                path=output_path,
                full_page=True,          # Capture everything, not just the viewport
                type="png",
                animations="disabled",   # Freeze animations so nothing is mid-frame
            )

            print(f"[SnapshotService] ✅ Screenshot saved: {output_path}")
            return output_path

        finally:
            await browser.close()
