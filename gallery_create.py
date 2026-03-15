from PIL import Image, ImageDraw
import os

os.makedirs('gallery', exist_ok=True)

samples = [
    ('001_warehouse.png', (30, 30, 60), 'Warehouse Example'),
    ('002_shelf.png', (60, 30, 30), 'Retail Shelf Example'),
    ('003_packline.png', (30, 60, 30), 'Packaging Line Example'),
]

for name, color, label in samples:
    img = Image.new('RGB', (800, 600), color)
    d = ImageDraw.Draw(img)
    # simple title
    d.text((24, 24), label, fill=(255, 255, 255))
    # draw some shapes to make images distinct
    for i in range(5):
        x = 50 + i * 120
        d.rectangle([x, 150, x + 80, 350], outline=(255, 255, 255))
    path = os.path.join('gallery', name)
    img.save(path)

print('Created sample images in gallery/')
