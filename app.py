import streamlit as st
import os
import tempfile
import subprocess
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image
import numpy as np
from io import BytesIO
import cv2

st.set_page_config(page_title="🎬 AI Video Effects App", layout="wide")
st.title("🎬 AI Video Effects App")

# ---------- Utility: Style Functions ----------
def get_transform_function(style_name):
    if style_name == "🌸 Soft Pastel Anime-Like Style":
        def pastel_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.08 + 20, 0, 255)
            g = np.clip(g * 1.06 + 15, 0, 255)
            b = np.clip(b * 1.15 + 25, 0, 255)
            blurred = (frame.astype(np.float32) * 0.4 +
                       cv2.GaussianBlur(frame, (7, 7), 0).astype(np.float32) * 0.6)
            tint = np.array([10, -5, 15], dtype=np.float32)
            result = np.clip(blurred + tint, 0, 255).astype(np.uint8)
            return result
        return pastel_style

    elif style_name == "🎞️ Cinematic Warm Filter":
        def warm_style(frame):
            r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
            r = np.clip(r * 1.15 + 15, 0, 255)
            g = np.clip(g * 1.08 + 8, 0, 255)
            b = np.clip(b * 0.95, 0, 255)
            rows, cols = r.shape
            Y, X = np.ogrid[:rows, :cols]
            center = (rows / 2, cols / 2)
            vignette = 1 - ((X - center[1])**2 + (Y - center[0])**2) / (1.5 * center[0] * center[1])
            vignette = np.clip(vignette, 0.3, 1)[..., np.newaxis]
            result = np.stack([r, g, b], axis=2).astype(np.float32) * vignette
            grain = np.random.normal(0, 3, frame.shape).astype(np.float32)
            return np.clip(result + grain, 0, 255).astype(np.uint8)
        return warm_style

    return lambda frame: frame

# ---------- Watermark Function (with automatic even-dimension scaling) ----------
def apply_watermark(input_path, output_path, text="@USMIKASHMIRI"):
    # The 'scale' filter ensures the width and height are even
    watermark_filter = (
        "scale=ceil(iw/2)*2:ceil(ih/2)*2,"  # Force dimensions to be even.
        f"drawtext=fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':"
        f"text='{text}':"
        "x=w-mod(t*240\\,w+tw):y=h-160:"
        "fontsize=40:fontcolor=white@0.6:"
        "shadowcolor=black:shadowx=2:shadowy=2"
    )
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", watermark_filter,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        st.error("❌ FFmpeg watermarking failed. Check FFmpeg, font path, or file permissions.")
        st.code(e.stderr.decode(), language="bash")
        raise

# ========== FEATURE 1 ==========
st.markdown("---")
st.header("🎨 Apply Style to Single Video (Before & After)")
uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4"], key="style_upload")
style = st.selectbox("🎨 Choose a Style", ["None", "🌸 Soft Pastel Anime-Like Style", "🎞️ Cinematic Warm Filter"], key="style_select")

if uploaded_file:
    start_time = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        clip = VideoFileClip(input_path)
        styled_clip = clip.fl_image(get_transform_function(style))
        styled_path = os.path.join(tmpdir, "styled.mp4")
        styled_clip.write_videofile(styled_path, codec="libx264", audio_codec="aac")

        clip_resized = clip.resize(height=480)
        styled_resized = VideoFileClip(styled_path).resize(height=480)

        combined = CompositeVideoClip(
            [clip_resized.set_position((0, 0)),
             styled_resized.set_position((clip_resized.w, 0))],
            size=(clip_resized.w + styled_resized.w, clip_resized.h)
        ).set_duration(min(clip_resized.duration, styled_resized.duration))

        final_path = os.path.join(tmpdir, "before_after.mp4")
        combined.write_videofile(final_path, codec="libx264", audio_codec="aac")

        st.video(final_path)
        with open(final_path, "rb") as f:
            st.download_button("💾 Download Before & After", f.read(), file_name="before_after.mp4")
    st.success(f"✅ Completed in {time.time() - start_time:.2f} seconds")

# ========== FEATURE 2 ==========
st.markdown("---")
st.header("📱 Side by Side (3 Videos) with Watermark")
uploaded_files = st.file_uploader("📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sidebyside")
style_sbs = st.selectbox("🎨 Style for Side-by-Side", ["None", "🌸 Soft Pastel Anime-Like Style", "🎞️ Cinematic Warm Filter"], key="style_sbs")

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
        duration = min(c.duration for c in clips)
        clips = [c.subclip(0, duration).set_position((i * 640, 0)) for i, c in enumerate(clips)]

        side_by_side = CompositeVideoClip(clips, size=(1920, 1080)).set_duration(duration)
        raw_output = os.path.join(tmpdir, "sbs_raw.mp4")
        side_by_side.write_videofile(raw_output, codec="libx264", audio_codec="aac")

        final_output = os.path.join(tmpdir, "sbs_final.mp4")
        apply_watermark(raw_output, final_output)

        st.video(final_output)
        with open(final_output, "rb") as f:
            st.download_button("💾 Download Side-by-Side", f.read(), file_name="side_by_side.mp4")
    st.success(f"✅ Completed in {time.time() - start_time:.2f} seconds")

# ---------- Feature 3 ----------
st.markdown("---")
st.header("🕒 Play 3 Videos Sequentially with Watermark and Slight Fade")

uploaded_seq = st.file_uploader(
    "📤 Upload 3 Videos (for sequential playback)", 
    type=["mp4"], 
    accept_multiple_files=True, 
    key="sequential"
)

style_seq = st.selectbox("🎨 Apply Style to Sequential Video", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
], key="style_sequential")

if uploaded_seq and len(uploaded_seq) == 3:
    if "sequential_video" not in st.session_state:
        start_time = time.time()
        progress = st.progress(0)
        status = st.empty()

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = []
            for i, f in enumerate(uploaded_seq):
                p = os.path.join(tmpdir, f"seq{i}.mp4")
                with open(p, "wb") as out:
                    out.write(f.read())
                paths.append(p)

            try:
                transform_func = get_transform_function(style_seq) if style_seq != "None" else lambda x: x
                video_clips = []
                total = 3
                for i, p in enumerate(paths):
                    status.text(f"🖼️ Applying style to video {i+1} / {total}")
                    progress.progress(int(((i + 1) / total) * 30))
                    video_clips.append(VideoFileClip(p).fl_image(transform_func).resize(height=1080))

                clips = []
                intro_clips = [clip.subclip(0, 1).set_position((i * 640, 0)) for i, clip in enumerate(video_clips)]
                intro = CompositeVideoClip(intro_clips, size=(1920, 1080)).set_duration(1)
                clips.append(intro)

                for i in range(3):
                    dur = video_clips[i].duration
                    main = video_clips[i]
                    others = []
                    for j in range(3):
                        if j == i:
                            clip = main.set_position((j * 640, 0))
                        else:
                            paused = video_clips[j].to_ImageClip(t=1).set_duration(dur).set_position((j * 640, 0)).set_opacity(0.4)
                            clip = paused
                        others.append(clip)
                    composite = CompositeVideoClip(others, size=(1920, 1080)).set_duration(dur)
                    clips.append(composite)

                final = concatenate_videoclips(clips)
                raw_output = os.path.join(tmpdir, "sequential_raw.mp4")

                status.text("📽️ Rendering final sequence...")
                final.write_videofile(raw_output, codec="libx264", audio_codec="aac", verbose=False, logger=None)
                progress.progress(80)

                final_output = os.path.join(tmpdir, "sequential_final.mp4")
                status.text("💧 Adding watermark...")
                watermark = "drawtext=text='@USMIKASHMIRI':x=w-mod(t*240\\,w+tw):y=h-160:fontsize=40:fontcolor=white@0.6:shadowcolor=black:shadowx=2:shadowy=2"
                cmd = f'ffmpeg -y -i "{raw_output}" -vf "{watermark}" -c:v libx264 -preset fast -crf 22 -pix_fmt yuv420p "{final_output}"'
                os.system(cmd)

                # Read video bytes into memory and store in session_state
                with open(final_output, "rb") as f:
                    st.session_state.sequential_video = f.read()

                end_time = time.time()
                st.success(f"✅ Completed in {end_time - start_time:.2f} seconds")
                progress.progress(100)

            except Exception as e:
                st.error(f"❌ Error: {e}")

        progress.empty()
        status.empty()

    if "sequential_video" in st.session_state:
        st.video(st.session_state.sequential_video)
        st.download_button(
            "💾 Download Sequential Video", 
            st.session_state.sequential_video, 
            file_name="sequential_output.mp4", 
            mime="video/mp4"
        )

elif uploaded_seq and len(uploaded_seq) != 3:
    st.warning("⚠️ Please upload exactly 3 videos.")

from io import BytesIO

# ========== FEATURE 4 ==========
st.markdown("---")
st.header("🖼️ Combine Thumbnails from 3 Videos (1280x720)")
uploaded_thumb_files = st.file_uploader("📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="thumbnails")

if uploaded_thumb_files and len(uploaded_thumb_files) == 3:
    st.subheader("⏱️ Select timestamps (in seconds) for each video")
    timestamps = [st.number_input(f"Timestamp for video {i+1}", min_value=0.0, value=1.0, step=0.5, key=f"ts_{i}") for i in range(3)]
    if st.button("🧩 Generate Combined Thumbnail"):
        with tempfile.TemporaryDirectory() as tmpdir:
            images = []
            for idx, file in enumerate(uploaded_thumb_files):
                path = os.path.join(tmpdir, f"thumb{idx}.mp4")
                with open(path, "wb") as f:
                    f.write(file.read())
                clip = VideoFileClip(path)
                frame = clip.get_frame(timestamps[idx])
                img = Image.fromarray(frame).resize((426, 720))
                images.append(img)
                clip.close()
            combined = Image.new("RGB", (1280, 720))
            for i, img in enumerate(images):
                combined.paste(img, (i * 426, 0))
            buffer = BytesIO()
            combined.save(buffer, format="JPEG")
            st.image(buffer.getvalue(), caption="Combined Thumbnail (1280x720)", use_container_width=True)
            st.download_button("💾 Download Thumbnail", buffer.getvalue(), file_name="combined_thumbnail.jpg", mime="image/jpeg")
