
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from pathlib import Path
import re
import os

# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="Signature Studio",
    page_icon="🤣",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================================
# 2. PROFESSIONAL UI
# ==================================================
st.markdown("""
<style>
    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 28px;
        border-radius: 18px;
        background: linear-gradient(120deg, #172554, #4338ca, #7c3aed);
        color: white;
        text-align: center;
        margin-bottom: 24px;
    }

    .hero h1 {
        color: white;
        font-size: 42px;
        margin-bottom: 8px;
    }

    .hero p {
        color: #e0e7ff;
        font-size: 17px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 700;
        margin-top: 15px;
    }

    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        min-height: 44px;
    }

    div.stDownloadButton > button {
        border-radius: 10px;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>✍️ Signature Studio</h1>
    <p>Create, preview and download your personal signature designs.</p>
</div>
""", unsafe_allow_html=True)

# ==================================================
# 3. FONT DISCOVERY
# ==================================================
def find_font_files():
    """Find available TrueType and OpenType fonts."""

    folders = [
        Path("C:/Windows/Fonts"),
        Path("/usr/share/fonts/truetype"),
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        Path.home() / ".fonts",
    ]

    fonts = []

    for folder in folders:
        if folder.exists():
            try:
                for path in folder.rglob("*"):
                    if path.suffix.lower() in [".ttf", ".otf"]:
                        fonts.append(path)
            except (OSError, PermissionError):
                pass

    return fonts


AVAILABLE_FONTS = find_font_files()


def find_matching_font(keywords):
    """Find a font file whose filename matches style keywords."""

    for keyword in keywords:
        for path in AVAILABLE_FONTS:
            if keyword.lower() in path.stem.lower():
                try:
                    return str(path)
                except OSError:
                    continue

    return None


STYLE_CONFIG = {
    "Classic": {
        "keywords": ["liberationserif-regular", "times", "dejavuserif"],
        "color": "#172554",
        "description": "Traditional and professional"
    },
    "Modern": {
        "keywords": ["arial", "liberationsans-regular", "dejavusans"],
        "color": "#0f766e",
        "description": "Clean and minimal"
    },
    "Elegant": {
        "keywords": ["chancery", "script", "gabriola", "italic"],
        "color": "#7e22ce",
        "description": "Refined and graceful"
    },
    "Handwritten": {
        "keywords": ["comic", "hand", "script", "chancery"],
        "color": "#1d4ed8",
        "description": "Casual handwritten appearance"
    },
    "Bold": {
        "keywords": ["liberationsans-bold", "arialbd", "dejavusans-bold"],
        "color": "#9f1239",
        "description": "Strong and prominent"
    }
}


def load_font(style, size, uploaded_font=None):
    """Load a suitable font, falling back safely if unavailable."""

    if uploaded_font is not None:
        try:
            uploaded_font.seek(0)
            return ImageFont.truetype(uploaded_font, size)
        except (OSError, ValueError):
            pass

    config = STYLE_CONFIG[style]
    font_path = find_matching_font(config["keywords"])

    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            pass

    # Built-in fallbacks; availability varies by Pillow version.
    fallback_names = {
        "Classic": "DejaVuSerif.ttf",
        "Modern": "DejaVuSans.ttf",
        "Elegant": "DejaVuSerif-Italic.ttf",
        "Handwritten": "DejaVuSans-Oblique.ttf",
        "Bold": "DejaVuSans-Bold.ttf"
    }

    try:
        return ImageFont.truetype(fallback_names[style], size)
    except OSError:
        return ImageFont.load_default()


# ==================================================
# 4. SIGNATURE IMAGE GENERATION
# ==================================================
def create_signature(name, style, purpose, color, transparent,
                     uploaded_font=None, add_underline=True):

    width = 1400
    height = 350

    # Transparent background or white background.
    if transparent:
        image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    else:
        image = Image.new("RGB", (width, height), "white")

    draw = ImageDraw.Draw(image)

    font_size = 100
    font = load_font(style, font_size, uploaded_font)

    # Reduce font size for longer names.
    while font_size > 28:
        font = load_font(style, font_size, uploaded_font)
        bbox = draw.textbbox((0, 0), name, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= width - 160:
            break

        font_size -= 5

    bbox = draw.textbbox((0, 0), name, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) // 2
    y = (height - text_height) // 2 - bbox[1] - 10

    draw.text((x, y), name, fill=color, font=font)

    if add_underline and style in ["Elegant", "Handwritten", "Bold"]:
        line_y = min(y + text_height + 28, height - 35)

        draw.line(
            (x, line_y, x + text_width, line_y),
            fill=color,
            width=3
        )

    # For professional purposes, add a subtle baseline.
    if purpose == "Professional" and style == "Modern":
        draw.line(
            (x, min(y + text_height + 18, height - 30),
             x + text_width, min(y + text_height + 18, height - 30)),
            fill=color,
            width=2
        )

    # Create downloadable PNG bytes.
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)

    # Create a white preview so transparent designs are visible.
    preview = Image.new("RGB", image.size, "white")
    if image.mode == "RGBA":
        preview.paste(image, mask=image.getchannel("A"))
    else:
        preview.paste(image)

    return preview, output.getvalue()


# ==================================================
# 5. SIDEBAR SETTINGS
# ==================================================
with st.sidebar:
    st.header("🎨 Design Settings")

    signature_type = st.selectbox(
        "Signature type",
        ["Both", "Simple", "Stylish"]
    )

    purpose = st.selectbox(
        "Purpose",
        ["Both", "Personal", "Professional"]
    )

    background_type = st.radio(
        "Download background",
        ["Transparent", "White"]
    )

    transparent = background_type == "Transparent"

    st.divider()

    selected_color = st.selectbox(
        "Signature color",
        [
            "Navy Blue",
            "Black",
            "Royal Blue",
            "Purple",
            "Teal",
            "Dark Red"
        ]
    )

    color_map = {
        "Navy Blue": "#172554",
        "Black": "#111111",
        "Royal Blue": "#1d4ed8",
        "Purple": "#7e22ce",
        "Teal": "#0f766e",
        "Dark Red": "#9f1239"
    }

    color = color_map[selected_color]

    uploaded_font = st.file_uploader(
        "Optional: upload a TTF/OTF font",
        type=["ttf", "otf"],
        help="Upload a font file you have permission to use."
    )

    add_underline = st.checkbox(
        "Add decorative underline",
        value=True
    )

    st.caption(
        "Font appearance depends on the font files available "
        "on your computer or the font you upload."
    )

# ==================================================
# 6. MAIN FORM
# ==================================================
st.markdown('<div class="section-title">Your Signature</div>',
            unsafe_allow_html=True)

with st.form("signature_form"):
    name_input = st.text_input(
        "Enter your name",
        placeholder="Example: Satyalal",
        max_chars=60
    )

    generate = st.form_submit_button(
        "✨ Generate My Signatures",
        type="primary",
        width="stretch"
    )

if generate:
    clean_name = re.sub(r"\s+", " ", name_input).strip()

    if not clean_name:
        st.warning("Please enter your name first.")
        st.session_state.pop("signature_results", None)

    elif not any(char.isalpha() for char in clean_name):
        st.warning("Please enter a name containing letters.")
        st.session_state.pop("signature_results", None)

    else:
        if signature_type == "Simple":
            styles = ["Classic", "Modern", "Bold"]
        elif signature_type == "Stylish":
            styles = ["Elegant", "Handwritten"]
        else:
            styles = [
                "Classic",
                "Modern",
                "Elegant",
                "Handwritten",
                "Bold"
            ]

        if purpose == "Personal":
            styles = [
                style for style in styles
                if style in ["Classic", "Elegant", "Handwritten"]
            ]
        elif purpose == "Professional":
            styles = [
                style for style in styles
                if style in ["Classic", "Modern", "Bold"]
            ]

        results = []

        for style in styles:
            preview, png_bytes = create_signature(
                clean_name,
                style,
                purpose,
                color,
                transparent,
                uploaded_font,
                add_underline
            )

            results.append({
                "style": style,
                "preview": preview,
                "png": png_bytes
            })

        st.session_state["signature_results"] = results
        st.session_state["signature_name"] = clean_name

# ==================================================
# 7. DISPLAY DESIGNS AND DOWNLOADS
# ==================================================
if "signature_results" in st.session_state:
    st.divider()

    st.markdown(
        '<div class="section-title">✨ Your Generated Designs</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"Signatures generated for **{st.session_state['signature_name']}**."
    )

    results = st.session_state["signature_results"]

    for start in range(0, len(results), 2):
        columns = st.columns(2)

        for offset, column in enumerate(columns):
            index = start + offset

            if index >= len(results):
                continue

            item = results[index]
            style = item["style"]

            with column:
                st.subheader(style)
                st.caption(STYLE_CONFIG[style]["description"])

                st.image(
                    item["preview"],
                    width="stretch"
                )

                safe_name = re.sub(
                    r"[^A-Za-z0-9_-]",
                    "_",
                    st.session_state["signature_name"]
                )

                filename = f"{safe_name}_{style.lower()}_signature.png"

                st.download_button(
                    label=f"⬇️ Download {style} PNG",
                    data=item["png"],
                    file_name=filename,
                    mime="image/png",
                    key=f"download_{index}",
                    width="stretch"
                )

        st.divider()

    st.info(
        "Transparent PNGs have no background pixels. "
        "They can be placed over other backgrounds in compatible apps. "
        "White-background downloads are also available from the settings."
    )

# ==================================================
# 8. FOOTER
# ==================================================
st.divider()

st.markdown(
    """
    <div style="text-align:center;color:gray;">
        Signature Studio · Built with Python, Pillow and Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
