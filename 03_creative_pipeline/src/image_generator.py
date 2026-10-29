"""Image banner generation using Pillow local synthesis and Google Imagen 3 API."""

import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from .models import AspectRatio, BrandColors, CreativeBrief, CreativeVariant, GeneratedImage

logger = logging.getLogger(__name__)

# システムフォント候補（macOS, Linux, Docker）
SYSTEM_FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    # Linux / Debian / Alpine
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    # Windows
    "C:\\Windows\\Fonts\\meiryo.ttc",
    "C:\\Windows\\Fonts\\msgothic.ttc",
]


def _get_font(size: int) -> ImageFont.ImageFont:
    """利用可能な日本語/ユニコードフォントをロード。見つからなければデフォルトフォントを返す"""
    for font_path in SYSTEM_FONT_CANDIDATES:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """HEXカラー文字列 ('#2563EB') を (R, G, B) タプルに変換"""
    try:
        hex_code = hex_code.strip().lstrip("#")
        if len(hex_code) == 3:
            hex_code = "".join([c * 2 for c in hex_code])
        if len(hex_code) != 6:
            return (37, 99, 235)  # デフォルトブルー
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (37, 99, 235)


def _draw_gradient_background(draw: ImageDraw.ImageDraw, width: int, height: int, start_color: Tuple[int, int, int], end_color: Tuple[int, int, int]):
    """滑らかな縦方向リニアグラデーション背景を描画"""
    for y in range(height):
        factor = y / float(height)
        r = int(start_color[0] + (end_color[0] - start_color[0]) * factor)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * factor)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def _wrap_text(text: str, max_chars_per_line: int = 14) -> List[str]:
    """指定文字数でテキストを折り返す"""
    lines = []
    current_line = ""
    for char in text:
        if char == "\n":
            lines.append(current_line)
            current_line = ""
            continue
        current_line += char
        if len(current_line) >= max_chars_per_line:
            lines.append(current_line)
            current_line = ""
    if current_line:
        lines.append(current_line)
    return lines


def generate_pillow_banner(
    variant: CreativeVariant,
    brief: CreativeBrief,
    aspect_ratio: AspectRatio,
    output_path: Path
) -> GeneratedImage:
    """Pillow を使用してプロフェッショナルな広告バナー画像を完全ローカル生成"""
    width, height = aspect_ratio.dimensions
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # カラーパレットの取得
    c_primary = _hex_to_rgb(brief.brand_colors.primary)
    c_secondary = _hex_to_rgb(brief.brand_colors.secondary)
    c_accent = _hex_to_rgb(brief.brand_colors.accent)
    c_bg = _hex_to_rgb(brief.brand_colors.background)
    c_white = (255, 255, 255)
    c_dark = (15, 23, 42)

    image = Image.new("RGB", (width, height), c_bg)
    draw = ImageDraw.Draw(image)

    # 1. グラデーション背景（暗めの洗練されたテックトーン）
    _draw_gradient_background(draw, width, height, c_secondary, c_dark)

    # 2. アクセント幾何学装飾（右上に半透明風のアクセントサークル）
    accent_box = [int(width * 0.7), -int(height * 0.2), int(width * 1.3), int(height * 0.4)]
    draw.ellipse(accent_box, outline=c_primary, width=3)
    accent_box_2 = [int(width * 0.75), -int(height * 0.15), int(width * 1.25), int(height * 0.35)]
    draw.ellipse(accent_box_2, outline=(c_accent[0], c_accent[1], c_accent[2]), width=2)

    # 3. コンテナカード描画
    pad_x = int(width * 0.08)
    pad_y = int(height * 0.08)
    card_box = [pad_x, pad_y, width - pad_x, height - pad_y]
    draw.rounded_rectangle(card_box, radius=24, outline=(255, 255, 255, 60), width=2)

    # 4. バッジ（商材名 + 訴求アプローチ）
    font_badge = _get_font(int(min(width, height) * 0.032))
    badge_text = f" {brief.product_name} | {variant.approach_name} "
    badge_x = pad_x + 40
    badge_y = pad_y + 40
    badge_w = int(len(badge_text) * (min(width, height) * 0.026)) + 30
    badge_h = int(min(width, height) * 0.06)
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=12, fill=c_primary)
    draw.text((badge_x + 15, badge_y + 10), badge_text, font=font_badge, fill=c_white)

    # 5. メインキャッチコピー
    catchphrase = variant.image_prompt.banner_catchphrase
    font_catch_size = int(min(width, height) * 0.065)
    font_catch = _get_font(font_catch_size)
    max_chars = 14 if aspect_ratio != AspectRatio.LANDSCAPE_191_1 else 18
    lines = _wrap_text(catchphrase, max_chars_per_line=max_chars)
    
    start_y = badge_y + badge_h + int(height * 0.06)
    for line in lines:
        draw.text((badge_x, start_y), line, font=font_catch, fill=c_white)
        start_y += font_catch_size + 15

    # 6. サブコピー
    if variant.image_prompt.banner_subphrase:
        subphrase = variant.image_prompt.banner_subphrase
        font_sub_size = int(min(width, height) * 0.038)
        font_sub = _get_font(font_sub_size)
        sub_lines = _wrap_text(subphrase, max_chars_per_line=max_chars + 4)
        start_y += 15
        for s_line in sub_lines:
            draw.text((badge_x, start_y), s_line, font=font_sub, fill=(203, 213, 225))
            start_y += font_sub_size + 10

    # 7. CTA ボタン（カード下部）
    cta_text = f"{variant.meta.cta_type} ➔"
    font_cta_size = int(min(width, height) * 0.036)
    font_cta = _get_font(font_cta_size)
    cta_w = int(len(cta_text) * (min(width, height) * 0.03)) + 40
    cta_h = int(min(width, height) * 0.075)
    cta_x = badge_x
    cta_y = height - pad_y - cta_h - 40
    draw.rounded_rectangle([cta_x, cta_y, cta_x + cta_w, cta_y + cta_h], radius=16, fill=c_accent)
    draw.text((cta_x + 25, cta_y + int(cta_h * 0.2)), cta_text, font=font_cta, fill=c_dark)

    # 8. フッター（安心訴求・注記）
    font_note = _get_font(int(min(width, height) * 0.024))
    note_text = "※導入効果および削減率は利用環境により異なります"
    draw.text((cta_x + cta_w + 30, cta_y + int(cta_h * 0.35)), note_text, font=font_note, fill=(148, 163, 184))

    # 画像保存
    image.save(output_path, quality=95)
    logger.info("Pillowバナー生成完了: %s (%dx%d)", output_path, width, height)

    return GeneratedImage(
        aspect_ratio=aspect_ratio.value,
        file_path=str(output_path),
        width=width,
        height=height,
        generator_type="pillow_banner"
    )


def generate_images_with_imagen(
    variant: CreativeVariant,
    aspect_ratio: AspectRatio,
    output_path: Path
) -> Optional[GeneratedImage]:
    """Google GenAI SDK (Imagen 3 API) による画像素材生成（APIキー・アクセス権が必要）"""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
    except ImportError:
        logger.warning("google-genai パッケージがないため Imagen 生成をスキップします。")
        return None

    client = genai.Client(api_key=api_key)
    prompt = variant.image_prompt.prompt_en

    # アスペクト比のマッピング
    ar_map = {
        AspectRatio.SQUARE_1_1: "1:1",
        AspectRatio.LANDSCAPE_191_1: "16:9",  # Imagen 3のサポート形式に近似
        AspectRatio.STORY_9_16: "9:16",
    }
    imagen_ar = ar_map.get(aspect_ratio, "1:1")

    try:
        logger.info("Imagen 3 API で画像を生成中... (prompt: %s)", prompt[:60])
        result = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=prompt,
            config=dict(
                number_of_images=1,
                aspect_ratio=imagen_ar,
                output_mime_type="image/jpeg",
            )
        )
        if result and result.generated_images:
            img_bytes = result.generated_images[0].image.image_bytes
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            
            w, h = aspect_ratio.dimensions
            return GeneratedImage(
                aspect_ratio=aspect_ratio.value,
                file_path=str(output_path),
                width=w,
                height=h,
                generator_type="imagen3"
            )
    except Exception as e:
        logger.warning("Imagen 3 API 呼び出しに失敗しました (%s)。ローカル生成にフォールバックします。", e)

    return None


def generate_creative_images(
    variant: CreativeVariant,
    brief: CreativeBrief,
    output_dir: Path,
    aspect_ratios: Optional[List[AspectRatio]] = None,
    use_api: bool = False
) -> List[GeneratedImage]:
    """指定されたアスペクト比ごとにバナー画像を生成し、リストを返す"""
    if not aspect_ratios:
        aspect_ratios = [AspectRatio.SQUARE_1_1, AspectRatio.LANDSCAPE_191_1]

    output_dir.mkdir(parents=True, exist_ok=True)
    images: List[GeneratedImage] = []

    for ar in aspect_ratios:
        safe_ar_name = ar.value.replace(":", "_")
        filename = f"{variant.variant_id}_{safe_ar_name}.png"
        out_path = output_dir / filename

        generated = None
        if use_api:
            generated = generate_images_with_imagen(variant, ar, out_path)

        if not generated:
            generated = generate_pillow_banner(variant, brief, ar, out_path)

        images.append(generated)

    return images
