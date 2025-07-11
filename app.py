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

# ---------- Feature 1 ----------
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
        st.video(output_path)

    end_time = time.time()
    st.success(f"✅ Completed in {end_time - start_time:.2f} seconds")
    progress.empty()
    status.empty()

# ---------- Feature 2 ----------
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

            # Watermark with FFmpeg
            status.text("💧 Adding watermark...")
            output_final = os.path.join(tmpdir, "sbs_final.mp4")
            watermark = "drawtext=text='@USMIKASHMIRI':x=w-mod(t*240\\,w+tw):y=h-160:fontsize=40:fontcolor=white@0.6:shadowcolor=black:shadowx=2:shadowy=2"
            cmd = f'ffmpeg -y -i "{output_raw}" -vf "{watermark}" -c:v libx264 -preset fast -crf 22 -pix_fmt yuv420p "{output_final}"'
            os.system(cmd)

            st.video(output_final)
            with open(output_final, "rb") as f:
                st.download_button("💾 Download Side-by-Side", f.read(), file_name="side_by_side.mp4", mime="video/mp4")

            end_time = time.time()
            st.success(f"✅ Completed in {end_time - start_time:.2f} seconds")
            progress.progress(100)

        except Exception as e:
            st.error(f"❌ FFmpeg merge failed.\n\n{e}")

    progress.empty()
    status.empty()

# ---------- Feature 3 ----------
st.markdown("---")
st.header("🕒 Play 3 Videos Sequentially with Watermark and Slight Fade")

uploaded_seq = st.file_uploader("📤 Upload 3 Videos (for sequential playback)", type=["mp4"], accept_multiple_files=True, key="sequential")
style_seq = st.selectbox("🎨 Apply Style to Sequential Video", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
], key="style_sequential")

if uploaded_seq and len(uploaded_seq) == 3:
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

            st.video(final_output)
            with open(final_output, "rb") as f:
                st.download_button("💾 Download Sequential Video", f.read(), file_name="sequential_output.mp4", mime="video/mp4")

            end_time = time.time()
            st.success(f"✅ Completed in {end_time - start_time:.2f} seconds")
            progress.progress(100)

        except Exception as e:
            st.error(f"❌ Error: {e}")

    progress.empty()
    status.empty()
elif uploaded_seq and len(uploaded_seq) != 3:
    st.warning("⚠️ Please upload exactly 3 videos.")

# ---------- Feature 4 ---------- 
st.markdown("---") 
st.header("🖼️ Final Goal Summary: Extract Thumbnails from 3 Videos")

uploaded_thumb_files = st.file_uploader(
    "📤 Upload 3 Videos (Cartoonified, Original, No-Audio)",
    type=["mp4"],
    accept_multiple_files=True,
    key="thumbnail_uploads"
)

if uploaded_thumb_files and len(uploaded_thumb_files) == 3:
    st.write("⏱️ Enter timestamp (in seconds) for each video below:")
    col1, col2, col3 = st.columns(3)

    with col1:
        time1 = st.number_input("Timestamp for Cartoonified Video", min_value=0.0, step=0.1, key="t1")
    with col2:
        time2 = st.number_input("Timestamp for Original Video", min_value=0.0, step=0.1, key="t2")
    with col3:
        time3 = st.number_input("Timestamp for No-Audio Video", min_value=0.0, step=0.1, key="t3")

    if st.button("📸 Generate All Thumbnails"):
        with tempfile.TemporaryDirectory() as tmpdir:
            thumb_paths = []
            times = [time1, time2, time3]

            for i, uploaded in enumerate(uploaded_thumb_files):
                input_path = os.path.join(tmpdir, f"thumb{i}.mp4")
                with open(input_path, "wb") as f:
                    f.write(uploaded.read())

                clip = VideoFileClip(input_path)
                timestamp = times[i]
                if timestamp > clip.duration:
                    st.warning(f"⚠️ Timestamp {timestamp}s exceeds duration of video {i+1}. Using middle frame instead.")
                    timestamp = clip.duration / 2

                frame = clip.get_frame(timestamp)
                img = Image.fromarray(frame.astype(np.uint8))
                img_path = os.path.join(tmpdir, f"thumbnail{i+1}.png")
                img.save(img_path)
                thumb_paths.append(img_path)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.image(thumb_paths[0], caption="📸 Cartoonified Thumbnail")
                with open(thumb_paths[0], "rb") as f:
                    st.download_button("Download 1️⃣", f.read(), "cartoon_thumbnail.png", "image/png")
            with col2:
                st.image(thumb_paths[1], caption="📸 Original Thumbnail")
                with open(thumb_paths[1], "rb") as f:
                    st.download_button("Download 2️⃣", f.read(), "original_thumbnail.png", "image/png")
            with col3:
                st.image(thumb_paths[2], caption="📸 No-Audio Thumbnail")
                with open(thumb_paths[2], "rb") as f:
                    st.download_button("Download 3️⃣", f.read(), "noaudio_thumbnail.png", "image/png")

elif uploaded_thumb_files and len(uploaded_thumb_files) != 3:
    st.warning("⚠️ Please upload exactly 3 videos to generate thumbnails.")
