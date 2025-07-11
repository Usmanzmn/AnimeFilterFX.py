import streamlit as st
import os
import tempfile
import time
from moviepy.editor import (
    VideoFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
    ColorClip
)
from PIL import Image
import numpy as np

st.set_page_config(page_title="Video Effects App", layout="wide")
st.title("🎬 AI Video Effects App")

# ---------- Helper: Style Functions ----------
def get_transform_function(style_name):
    if style_name == "🌸 Soft Pastel Anime-Like Style":
        def pastel_style(frame):
            return np.clip(frame * 1.1 + 10, 0, 255).astype(np.uint8)
        return pastel_style
    elif style_name == "🎞️ Cinematic Warm Filter":
        def warm_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.1, 0, 255)
            g = np.clip(g * 1.05, 0, 255)
            return np.stack([r, g, b], axis=2).astype(np.uint8)
        return warm_style
    else:
        return lambda frame: frame

# ========== Feature 1 ==========
st.markdown("---")
st.header("🎨 Apply Style to Single Video")
uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4"], key="style_upload")
style = st.selectbox("🎨 Choose a Style", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
], key="style_select")

if uploaded_file:
    start_time = time.time()
    progress = st.progress(0)
    status = st.empty()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        clip = VideoFileClip(input_path)
        duration = clip.duration
        transform_func = get_transform_function(style)

        def progress_wrapper(get_frame, t):
            percent = int((t / duration) * 100)
            progress.progress(min(percent, 100))
            status.text(f"⏳ Processing frame at {t:.2f}s / {duration:.2f}s")
            return transform_func(get_frame(t))

        styled = clip.fl(progress_wrapper)
        output_path = os.path.join(tmpdir, "styled.mp4")
        styled.write_videofile(output_path, codec="libx264", audio_codec="aac")
        st.video(output_path)  # FIXED

    end_time = time.time()
    st.success(f"✅ Completed in {end_time - start_time:.2f} seconds")
    progress.empty()
    status.empty()

# ========== Feature 2 ==========
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
    progress = st.progress(0)
    status = st.empty()
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for i, file in enumerate(uploaded_files):
            path = os.path.join(tmpdir, f"video{i}.mp4")
            with open(path, "wb") as f:
                f.write(file.read())
            paths.append(path)

        try:
            transform_func = get_transform_function(style_sbs)
            clips = []
            total = 3
            for idx, p in enumerate(paths):
                status.text(f"🎞️ Processing video {idx + 1} / {total}")
                progress.progress(int(((idx + 1) / total) * 30))
                clip = VideoFileClip(p).fl_image(transform_func).resize(height=1080)
                clips.append(clip)

            min_duration = min([c.duration for c in clips])
            clips = [c.subclip(0, min_duration).set_position((i * 640, 0)) for i, c in enumerate(clips)]

            status.text("🧩 Compositing videos...")
            comp = CompositeVideoClip(clips, size=(1920, 1080)).set_duration(min_duration)
            output_raw = os.path.join(tmpdir, "sbs_raw.mp4")
            comp.write_videofile(output_raw, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            progress.progress(70)

            status.text("💧 Adding watermark...")
            output_final = os.path.join(tmpdir, "sbs_final.mp4")
            watermark = "drawtext=text='@USMIKASHMIRI':x=w-mod(t*240\\,w+tw):y=h-160:fontsize=40:fontcolor=white@0.6:shadowcolor=black:shadowx=2:shadowy=2"
            cmd = f'ffmpeg -y -i "{output_raw}" -vf "{watermark}" -c:v libx264 -preset fast -crf 22 -pix_fmt yuv420p "{output_final}"'
            os.system(cmd)

            st.video(output_final)  # FIXED
            with open(output_final, "rb") as f:
                st.download_button("💾 Download Side-by-Side", f.read(), file_name="side_by_side.mp4", mime="video/mp4")

            end_time = time.time()
            st.success(f"✅ Completed in {end_time - start_time:.2f} seconds")
            progress.progress(100)

        except Exception as e:
            st.error(f"❌ FFmpeg merge failed.\n\n{e}")
    progress.empty()
    status.empty()

# ========== Feature 3 ==========
st.markdown("---")
st.header("🪄 Combine Multiple Videos with Style and Watermark")
uploaded_clips = st.file_uploader("📤 Upload Videos to Combine", type=["mp4"], accept_multiple_files=True, key="combine")
style_combine = st.selectbox("🎨 Choose a Style for Combined Video", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
], key="style_combine")

if uploaded_clips and len(uploaded_clips) >= 2:
    start_time = time.time()
    progress = st.progress(0)
    status = st.empty()
    with tempfile.TemporaryDirectory() as tmpdir:
        clip_paths = []
        for i, file in enumerate(uploaded_clips):
            path = os.path.join(tmpdir, f"clip{i}.mp4")
            with open(path, "wb") as f:
                f.write(file.read())
            clip_paths.append(path)

        try:
            status.text("📦 Loading and styling clips...")
            transform_func = get_transform_function(style_combine)
            clips = []
            total_clips = len(clip_paths)

            for i, path in enumerate(clip_paths):
                clip = VideoFileClip(path).fl_image(transform_func)
                clips.append(clip)
                progress.progress(int(((i + 1) / total_clips) * 50))

            final_clip = concatenate_videoclips(clips, method="compose")

            output_path_raw = os.path.join(tmpdir, "combined_raw.mp4")
            status.text("💾 Rendering combined video...")
            final_clip.write_videofile(output_path_raw, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            progress.progress(75)

            # Add watermark using ffmpeg
            status.text("💧 Adding watermark...")
            final_output = os.path.join(tmpdir, "combined_final.mp4")
            watermark = "drawtext=text='@USMIKASHMIRI':x=w-mod(t*200\\,w+tw):y=h-140:fontsize=36:fontcolor=white@0.6:shadowcolor=black:shadowx=2:shadowy=2"
            os.system(f'ffmpeg -y -i "{output_path_raw}" -vf "{watermark}" -c:v libx264 -preset fast -crf 22 -pix_fmt yuv420p "{final_output}"')

            st.video(final_output)  # ✅ FIXED: removed use_container_width
            with open(final_output, "rb") as f:
                st.download_button("💾 Download Combined Video", f.read(), file_name="combined_video.mp4", mime="video/mp4")

            end_time = time.time()
            st.success(f"✅ Completed in {end_time - start_time:.2f} seconds")
            progress.progress(100)

        except Exception as e:
            st.error(f"❌ An error occurred while combining videos.\n\n{e}")

    progress.empty()
    status.empty()


# ========== Feature 4  ==========
st.markdown("---")
st.header("📸 Combine All Thumbnails into One (16:9)")

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
                img = img.resize((640, 360))  # 16:9 thumbnail
                images.append(img)

            combined = Image.new("RGB", (1920, 360))
            for i, img in enumerate(images):
                combined.paste(img, (i * 640, 0))

            st.image(combined, caption="Combined Thumbnail", use_column_width=True)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as out_thumb:
                combined.save(out_thumb.name)
                st.download_button("💾 Download Thumbnail", open(out_thumb.name, "rb").read(), file_name="combined_thumbnail.jpg", mime="image/jpeg")

