import streamlit as st
import os
import shutil
import subprocess
import tempfile
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image
import numpy as np

st.set_page_config(page_title="Video Effects App", layout="wide")
st.title("\U0001F3AC AI Video Effects App")

# ---------- Helper: Style Functions ----------
def get_transform_function(style_name):
    if style_name == "\U0001F338 Soft Pastel Anime-Like Style":
        def pastel_style(frame):
            # Apply a simple pastel filter effect
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

# ---------- Feature 1 ----------
st.markdown("---")
st.header("\U0001F3A8 Apply Style to Single Video")

uploaded_file = st.file_uploader("\U0001F4E4 Upload a Video", type=["mp4"], key="style_upload")
style = st.selectbox("\U0001F3A8 Choose a Style", [
    "None",
    "\U0001F338 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
], key="style_select")

if uploaded_file:
    start_time = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        clip = VideoFileClip(input_path)
        transform_func = get_transform_function(style)
        styled = clip.fl_image(transform_func)
        output_path = os.path.join(tmpdir, "styled.mp4")
        styled.write_videofile(output_path, codec="libx264", audio_codec="aac")
        st.video(output_path)

    end_time = time.time()
    st.success(f"✅ Completed in {end_time - start_time:.2f} seconds")

# ---------- Feature 2 ----------
st.markdown("---")
st.header("\U0001F4F1 Side by Side (3 Videos) with Watermark")

uploaded_files = st.file_uploader("\U0001F4E4 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sidebyside")
style_sbs = st.selectbox("\U0001F3A8 Apply Style to Side-by-Side", [
    "None",
    "\U0001F338 Soft Pastel Anime-Like Style",
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
        clips = []
        for i, p in enumerate(paths):
            clip = VideoFileClip(p).fl_image(transform_func).resize(height=1080)
            clips.append(clip)

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

# ---------- Feature 3 ----------
st.markdown("---")
st.header("\U0001F551 Play 3 Videos Sequentially with Watermark and Slight Fade")

uploaded_seq = st.file_uploader("\U0001F4E4 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sequential")
style_seq = st.selectbox("\U0001F3A8 Apply Style to Sequential Video", [
    "None",
    "\U0001F338 Soft Pastel Anime-Like Style",
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


from io import BytesIO
# ---------- Feature 4 ----------
st.markdown("---")
st.header("📸 Combine All Thumbnails into One (1280x720)")

uploaded_thumb_files = st.file_uploader(
    "📤 Upload 3 Videos (Cartoonified, Original, Styled)", 
    type=["mp4"], 
    accept_multiple_files=True, 
    key="thumbnails"
)

if uploaded_thumb_files and len(uploaded_thumb_files) == 3:
    st.subheader("🕒 Select timestamps (in seconds) for each video")
    timestamps = []
    for i in range(3):
        ts = st.number_input(
            f"Timestamp for video {i+1} (in seconds)", 
            min_value=0.0, 
            value=1.0, 
            step=0.5, 
            key=f"timestamp_{i}"
        )
        timestamps.append(ts)

    if st.button("🧩 Generate Combined Thumbnail"):
        st.info("📸 Extracting and combining thumbnails...")
        with tempfile.TemporaryDirectory() as tmpdir:
            images = []
            for idx, file in enumerate(uploaded_thumb_files):
                path = os.path.join(tmpdir, f"thumb{idx}.mp4")
                with open(path, "wb") as f:
                    f.write(file.read())

                clip = VideoFileClip(path)
                frame = clip.get_frame(timestamps[idx])
                img = Image.fromarray(frame)
                img = img.resize((426, 720))  # Resize to 1/3 width of 1280, full height
                images.append(img)
                clip.close()

            combined = Image.new("RGB", (1280, 720))
            for i, img in enumerate(images):
                combined.paste(img, (i * 426, 0))

            # Save combined image to bytes
            buffer = BytesIO()
            combined.save(buffer, format="JPEG")
            buffer.seek(0)
            st.session_state.thumbnail_bytes = buffer.read()

if "thumbnail_bytes" in st.session_state:
    st.image(BytesIO(st.session_state.thumbnail_bytes), caption="Combined Thumbnail (1280x720)", use_container_width=True)
    st.download_button(
        "💾 Download Thumbnail", 
        st.session_state.thumbnail_bytes, 
        file_name="combined_thumbnail_1280x720.jpg", 
        mime="image/jpeg"
    )
