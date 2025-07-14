import streamlit as st
import os
import shutil
import subprocess
import tempfile
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Video Effects App", layout="wide")
st.title("🎬 AI Video Effects App")

# ---------- Helper: Style Functions ----------
def get_transform_function(style_name):
    if style_name == "🌸 Soft Pastel Anime-Like Style":
        def pastel_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.05 + 15, 0, 255)
            g = np.clip(g * 1.05 + 15, 0, 255)
            b = np.clip(b * 1.1 + 20, 0, 255)
            return np.stack([r, g, b], axis=2).astype(np.uint8)
        return pastel_style

    elif style_name == "🎞️ Cinematic Warm Filter":
        def warm_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.1 + 10, 0, 255)
            g = np.clip(g * 1.05 + 5, 0, 255)
            return np.stack([r, g, b], axis=2).astype(np.uint8)
        return warm_style

    else:
        return lambda frame: frame

# ========== FEATURE 1 ==========
st.markdown("---")
st.header("🎨 Apply Style to Single Video (Before & After)")

uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4"], key="style_upload")
style = st.selectbox("🎨 Choose a Style", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
], key="style_select")

if uploaded_file:
    start_time = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        # Load original video
        clip = VideoFileClip(input_path)
        transform_func = get_transform_function(style)

        # Apply style
        styled = clip.fl_image(transform_func)
        styled_path = os.path.join(tmpdir, "styled.mp4")
        styled.write_videofile(styled_path, codec="libx264", audio_codec="aac")

        # Resize both videos
        clip_resized = clip.resize(height=480)
        styled_resized = VideoFileClip(styled_path).resize(height=480)

        # Combine side-by-side
        combined = CompositeVideoClip(
            [clip_resized.set_position((0, 0)),
             styled_resized.set_position((clip_resized.w, 0))],
            size=(clip_resized.w + styled_resized.w, clip_resized.h)
        ).set_duration(min(clip_resized.duration, styled_resized.duration))

        final_path = os.path.join(tmpdir, "before_after.mp4")
        combined.write_videofile(final_path, codec="libx264", audio_codec="aac")

        # Display side-by-side result
        st.video(final_path)

        # Optional: download button
        with open(final_path, "rb") as f:
            st.download_button("💾 Download Before & After", f.read(), file_name="before_after.mp4", mime="video/mp4")

    st.success(f"✅ Completed in {time.time() - start_time:.2f} seconds")


# ========== FEATURE 2 ==========
st.markdown("---")
st.header("📱 Side by Side (3 Videos) with Watermark")

uploaded_files = st.file_uploader("📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sidebyside")
style_sbs = st.selectbox("🎨 Apply Style to Side-by-Side", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
], key="style_sbs")

if uploaded_files and len(uploaded_files) == 3:
    start_time = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for i, file in enumerate(uploaded_files):
            path = os.path.join(tmpdir, f"video{i}.mp4")
            with open(path, "wb") as f:
                f.write(file.read())
            paths.append(path)

        transform_func = get_transform_function(style_sbs)
        clips = [VideoFileClip(p).fl_image(transform_func).resize(height=1080) for p in paths]

        min_duration = min([c.duration for c in clips])
        clips = [c.subclip(0, min_duration).set_position((i * 640, 0)) for i, c in enumerate(clips)]
        comp = CompositeVideoClip(clips, size=(1920, 1080)).set_duration(min_duration)
        raw_output = os.path.join(tmpdir, "sbs_raw.mp4")
        comp.write_videofile(raw_output, codec="libx264", audio_codec="aac")

        final_output = os.path.join(tmpdir, "sbs_final.mp4")
        watermark = (
            "drawtext=text='@USMIKASHMIRI':"
            "x=w-mod(t*240\\,w+tw):y=h-160:"
            "fontsize=40:fontcolor=white@0.6:"
            "shadowcolor=black:shadowx=2:shadowy=2"
        )
        cmd = [
            "ffmpeg", "-y", "-i", raw_output,
            "-vf", watermark,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
            final_output
        ]
        subprocess.run(cmd, check=True)

        st.video(final_output)
        with open(final_output, "rb") as f:
            st.download_button("💾 Download Side-by-Side", f.read(), file_name="side_by_side.mp4", mime="video/mp4")

# ========== FEATURE 3 ==========
st.markdown("---")
st.header("🕐 Play 3 Videos Sequentially with Watermark")

uploaded_seq = st.file_uploader("📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sequential")
style_seq = st.selectbox("🎨 Apply Style to Sequential Video", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
], key="style_sequential")

if uploaded_seq and len(uploaded_seq) == 3:
    start_time = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for i, file in enumerate(uploaded_seq):
            path = os.path.join(tmpdir, f"seq{i}.mp4")
            with open(path, "wb") as f:
                f.write(file.read())
            paths.append(path)

        transform_func = get_transform_function(style_seq)
        clips = [VideoFileClip(p).fl_image(transform_func).resize(height=1080) for p in paths]

        final_clip = concatenate_videoclips(clips, method="compose")
        raw_output = os.path.join(tmpdir, "seq_raw.mp4")
        final_clip.write_videofile(raw_output, codec="libx264", audio_codec="aac")

        final_output = os.path.join(tmpdir, "seq_final.mp4")
        watermark = (
            "drawtext=text='@USMIKASHMIRI':"
            "x=w-mod(t*240\\,w+tw):y=h-160:"
            "fontsize=40:fontcolor=white@0.6:"
            "shadowcolor=black:shadowx=2:shadowy=2"
        )
        cmd = [
            "ffmpeg", "-y", "-i", raw_output,
            "-vf", watermark,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
            final_output
        ]
        subprocess.run(cmd, check=True)

        st.video(final_output)
        with open(final_output, "rb") as f:
            st.download_button("💾 Download Sequential Video", f.read(), file_name="sequential_output.mp4", mime="video/mp4")

# ========== FEATURE 4 ==========
st.markdown("---")
st.header("🖼️ Combine Thumbnails from 3 Videos (1280x720)")

uploaded_thumb_files = st.file_uploader("📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="thumbnails")

if uploaded_thumb_files and len(uploaded_thumb_files) == 3:
    st.subheader("⏱️ Select timestamps (in seconds) for each video")
    timestamps = []
    for i in range(3):
        ts = st.number_input(
            f"Timestamp for video {i+1}", 
            min_value=0.0, 
            value=1.0, 
            step=0.5, 
            key=f"timestamp_{i}"
        )
        timestamps.append(ts)

    if st.button("🧩 Generate Combined Thumbnail"):
        with tempfile.TemporaryDirectory() as tmpdir:
            images = []
            for idx, file in enumerate(uploaded_thumb_files):
                path = os.path.join(tmpdir, f"thumb{idx}.mp4")
                with open(path, "wb") as f:
                    f.write(file.read())

                clip = VideoFileClip(path)
                frame = clip.get_frame(timestamps[idx])
                img = Image.fromarray(frame)
                img = img.resize((426, 720))  # ~1/3 of 1280
                images.append(img)
                clip.close()

            combined = Image.new("RGB", (1280, 720))
            for i, img in enumerate(images):
                combined.paste(img, (i * 426, 0))

            buffer = BytesIO()
            combined.save(buffer, format="JPEG")
            buffer.seek(0)
            st.session_state.thumbnail_bytes = buffer.read()

if "thumbnail_bytes" in st.session_state:
    st.image(BytesIO(st.session_state.thumbnail_bytes), caption="Combined Thumbnail (1280x720)", use_container_width=True)
    st.download_button(
        "💾 Download Thumbnail", 
        st.session_state.thumbnail_bytes, 
        file_name="combined_thumbnail.jpg", 
        mime="image/jpeg"
    )
