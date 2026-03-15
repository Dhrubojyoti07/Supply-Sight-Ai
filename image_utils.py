import io
from PIL import Image, ImageStat


def load_image_from_bytes(data: bytes) -> Image.Image:
    bio = io.BytesIO(data)
    img = Image.open(bio).convert("RGB")
    return img


def resize_image(image: Image.Image, max_size=(800, 600)) -> Image.Image:
    img = image.copy()
    # Pillow 10 removed Image.ANTIALIAS in favor of Image.Resampling.LANCZOS
    try:
        resample = Image.Resampling.LANCZOS
    except Exception:
        # Fallbacks for older Pillow versions
        resample = getattr(Image, "LANCZOS", getattr(Image, "ANTIALIAS", Image.BILINEAR))

    img.thumbnail(max_size, resample)
    return img


def image_to_bytes(image: Image.Image, fmt="JPEG", quality=85) -> bytes:
    bio = io.BytesIO()
    image.save(bio, format=fmt, quality=quality)
    return bio.getvalue()


def simple_describe(image: Image.Image) -> str:
    stat = ImageStat.Stat(image)
    r, g, b = [int(x) for x in stat.mean]
    w, h = image.size
    brightness = int(sum(stat.mean) / 3)
    try:
        colors = image.getcolors(maxcolors=1000000)
        color_count = len(colors) if colors else 0
    except Exception:
        color_count = 0

    parts = [
        f"Size: {w}x{h}",
        f"Mode: {image.mode}",
        f"Approx. average color RGB({r},{g},{b})",
        f"Approx. brightness: {brightness}",
        f"Distinct colors (est): {color_count}",
    ]
    return ", ".join(parts)


def load_image_from_path(path: str) -> Image.Image:
    from PIL import Image as PILImage

    img = PILImage.open(path).convert("RGB")
    return img


def image_feature(image: Image.Image) -> dict:
    """Compute simple features for image similarity: average RGB and size."""
    stat = ImageStat.Stat(image)
    avg = tuple(int(x) for x in stat.mean)
    w, h = image.size
    return {"avg": avg, "size": (w, h)}
