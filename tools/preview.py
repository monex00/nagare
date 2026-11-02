"""Render frames of an animated SVG with Chromium and optionally encode a video.

python tools/preview.py koi-pond.svg out/ --times 0 3 6      -> PNG stills
python tools/preview.py koi-pond.svg out/ --video 12          -> out/preview-<scheme>.mp4
"""
import argparse
import pathlib
import subprocess

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("svg")
ap.add_argument("out")
ap.add_argument("--times", type=float, nargs="*", default=[0.0])
ap.add_argument("--video", type=float, default=0, help="seconds of video to encode")
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--scheme", choices=["light", "dark", "both"], default="both")
ap.add_argument("--scale", type=float, default=2)
a = ap.parse_args()

out = pathlib.Path(a.out)
out.mkdir(parents=True, exist_ok=True)
svg = pathlib.Path(a.svg).resolve()
schemes = ["light", "dark"] if a.scheme == "both" else [a.scheme]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for scheme in schemes:
        page = browser.new_page(viewport={"width": 900, "height": 360},
                                device_scale_factor=a.scale, color_scheme=scheme)
        page.goto(svg.as_uri())
        page.evaluate("document.documentElement.pauseAnimations()")

        def shot(t, path):
            page.evaluate(f"document.documentElement.setCurrentTime({t})")
            page.wait_for_timeout(15)
            page.screenshot(path=str(path))

        for t in a.times:
            shot(t, out / f"{scheme}-{t:05.1f}.png")
        if a.video:
            fdir = out / f"frames-{scheme}"
            fdir.mkdir(exist_ok=True)
            n = int(a.video * a.fps)
            for i in range(n):
                shot(i / a.fps, fdir / f"{i:05d}.png")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps),
                            "-i", str(fdir / "%05d.png"), "-c:v", "libx264", "-preset", "veryfast",
                            "-pix_fmt", "yuv420p", "-crf", "20", str(out / f"preview-{scheme}.mp4")],
                           check=True)
        page.close()
    browser.close()
