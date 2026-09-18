"""
Create visual assets for the application
Generates placeholder images for avatars, icons, and backgrounds
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_serena_avatar():
    """Create Serena's avatar - Pokémon-inspired"""
    size = 128
    img = Image.new('RGB', (size, size), color='#ff80ab')
    draw = ImageDraw.Draw(img)
    
    # Create a playful pink gradient effect
    for i in range(size):
        color_intensity = int(255 * (1 - i/size))
        color = (255, 128, 171, color_intensity)
        draw.line([(0, i), (size, i)], fill=color)
    
    # Add "S" in the center
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    text = "S"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Add Pokémon-style sparkles
    for _ in range(5):
        import random
        x = random.randint(10, size-10)
        y = random.randint(10, size-10)
        draw.ellipse([x, y, x+3, y+3], fill='white')
    
    return img

def create_astrid_avatar():
    """Create Astrid's avatar - Viking/Norse-inspired"""
    size = 128
    img = Image.new('RGB', (size, size), color='#8b9dc3')
    draw = ImageDraw.Draw(img)
    
    # Create a Nordic gradient effect
    for i in range(size):
        color_intensity = int(200 * (1 - i/size))
        color = (139, 157, 195, color_intensity)
        draw.line([(0, i), (size, i)], fill=color)
    
    # Add "A" in the center
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    text = "A"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Add Nordic-style geometric patterns
    draw.rectangle([10, 10, 20, 20], fill='#e8e8e8')
    draw.rectangle([size-20, size-20, size-10, size-10], fill='#e8e8e8')
    
    return img

def create_background_serena():
    """Create Serena-themed background"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='#1e1e1e')
    draw = ImageDraw.Draw(img)
    
    # Add subtle pink gradient
    for y in range(height):
        intensity = int(50 * (y / height))
        color = (30 + intensity, 30 + intensity//2, 30 + intensity//3)
        draw.line([(0, y), (width, y)], fill=color)
    
    # Add decorative circles (Pokémon-style)
    for _ in range(10):
        import random
        x = random.randint(0, width)
        y = random.randint(0, height)
        radius = random.randint(20, 80)
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                    outline='#ff80ab', width=2)
    
    return img

def create_background_astrid():
    """Create Astrid-themed background"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Add subtle Nordic gradient
    for y in range(height):
        intensity = int(40 * (y / height))
        color = (26 + intensity, 26 + intensity//2, 26 + intensity//3)
        draw.line([(0, y), (width, y)], fill=color)
    
    # Add Nordic geometric patterns
    for i in range(0, width, 100):
        draw.line([(i, 0), (i, height)], fill='#8b9dc3', width=1)
    for i in range(0, height, 100):
        draw.line([(0, i), (width, i)], fill='#8b9dc3', width=1)
    
    return img

def create_icon(name, color, symbol):
    """Create UI icons"""
    size = 32
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Convert hex color to RGB
    if color.startswith('#'):
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    else:
        rgb = (100, 100, 100)  # Default gray
    
    # Background circle
    draw.ellipse([2, 2, size-2, size-2], fill=rgb)
    
    # Add symbol
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), symbol, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), symbol, fill='white', font=font)
    
    return img

def main():
    """Create all visual assets"""
    images_dir = Path(__file__).parent / "images"
    avatars_dir = images_dir / "avatars"
    backgrounds_dir = images_dir / "backgrounds"
    icons_dir = images_dir / "icons"
    
    # Create directories
    avatars_dir.mkdir(parents=True, exist_ok=True)
    backgrounds_dir.mkdir(parents=True, exist_ok=True)
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    print("Creating visual assets...")
    
    # Create avatars
    print("Creating avatars...")
    serena_avatar = create_serena_avatar()
    serena_avatar.save(avatars_dir / "serena_avatar.png")
    print("  ✓ Serena avatar created")
    
    astrid_avatar = create_astrid_avatar()
    astrid_avatar.save(avatars_dir / "astrid_avatar.png")
    print("  ✓ Astrid avatar created")
    
    # Create backgrounds
    print("Creating backgrounds...")
    serena_bg = create_background_serena()
    serena_bg.save(backgrounds_dir / "serena_background.png")
    print("  ✓ Serena background created")
    
    astrid_bg = create_background_astrid()
    astrid_bg.save(backgrounds_dir / "astrid_background.png")
    print("  ✓ Astrid background created")
    
    # Create icons
    print("Creating icons...")
    icons = [
        ("agent", "#007acc", "🤖"),
        ("media", "#ff80ab", "🎬"),
        ("server", "#8b9dc3", "🔧"),
        ("photo", "#9caf88", "📸"),
        ("chat", "#4fc3f7", "💬"),
        ("settings", "#ff9800", "⚙️")
    ]
    
    for name, color, symbol in icons:
        icon = create_icon(name, color, symbol)
        icon.save(icons_dir / f"{name}_icon.png")
        print(f"  ✓ {name} icon created")
    
    print("\n✅ All visual assets created successfully!")
    print(f"Assets saved to: {images_dir}")

if __name__ == "__main__":
    main()