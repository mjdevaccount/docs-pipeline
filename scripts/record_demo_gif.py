"""
Script to record a demo GIF of the docs-pipeline web interface.
This script uses browser automation to interact with the demo and capture screenshots,
then combines them into an animated GIF.
"""

import time
import os
from pathlib import Path
from PIL import Image
import glob

# Screenshot directory
SCREENSHOT_DIR = Path("demo_screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

def take_screenshot(filename, description=""):
    """Take a screenshot and save it with a description"""
    print(f"📸 Taking screenshot: {description}")
    # This will be called via browser tools
    return f"{SCREENSHOT_DIR}/{filename}"

def wait_for_element(text, timeout=10):
    """Wait for text to appear on page"""
    print(f"⏳ Waiting for: {text}")
    # This will be handled by browser_wait_for tool
    time.sleep(1)  # Small delay between actions

def create_gif_from_screenshots(output_path="demo.gif", duration=1000, loop=0):
    """
    Combine screenshots into an animated GIF.
    
    Args:
        output_path: Path to save the GIF
        duration: Duration of each frame in milliseconds
        loop: Number of loops (0 = infinite)
    """
    print("\nCreating GIF from screenshots...")
    
    # Get all screenshot files sorted by name
    screenshot_files = sorted(glob.glob(str(SCREENSHOT_DIR / "screenshot_*.png")))
    
    if not screenshot_files:
        print("ERROR: No screenshots found!")
        return None
    
    print(f"Found {len(screenshot_files)} screenshots")
    
    # Load all images
    images = []
    for file in screenshot_files:
        try:
            img = Image.open(file)
            # Resize if needed (optional - can adjust for file size)
            # img = img.resize((1200, 800), Image.Resampling.LANCZOS)
            images.append(img.copy())
            print(f"  Loaded: {Path(file).name}")
        except Exception as e:
            print(f"  Error loading {file}: {e}")
    
    if not images:
        print("ERROR: No valid images to create GIF")
        return None
    
    # Save as GIF
    try:
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=loop,
            optimize=True
        )
        print(f"SUCCESS: GIF created successfully: {output_path}")
        print(f"   Size: {len(images)} frames")
        print(f"   Duration per frame: {duration}ms")
        return output_path
    except Exception as e:
        print(f"ERROR: Error creating GIF: {e}")
        return None

def cleanup_screenshots():
    """Remove screenshot directory"""
    import shutil
    if SCREENSHOT_DIR.exists():
        shutil.rmtree(SCREENSHOT_DIR)
        print("🧹 Cleaned up screenshots directory")

if __name__ == "__main__":
    import sys
    import shutil
    
    # Try to find screenshots in temp directory
    temp_base = Path.home() / "AppData" / "Local" / "Temp" / "cursor-browser-extension"
    if temp_base.exists():
        temp_dirs = sorted(temp_base.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        for temp_dir in temp_dirs:
            screenshot_temp = temp_dir / "demo_screenshots"
            if screenshot_temp.exists():
                print(f"Found screenshots in: {screenshot_temp}")
                # Copy to project directory
                SCREENSHOT_DIR.mkdir(exist_ok=True)
                for png_file in screenshot_temp.glob("*.png"):
                    shutil.copy2(png_file, SCREENSHOT_DIR / png_file.name)
                    print(f"  Copied: {png_file.name}")
                break
    
    # Create GIF
    if "--create-gif" in sys.argv or len(sys.argv) == 1:
        output = create_gif_from_screenshots("demo.gif", duration=1500, loop=0)
        if output:
            print(f"\nDemo GIF ready: {output}")
    else:
        print("This script combines screenshots into an animated GIF.")
        print("\nUsage: python record_demo_gif.py [--create-gif]")

