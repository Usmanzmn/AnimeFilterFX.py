import streamlit as st
import os
import tempfile
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
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
import subprocess  # ✅ Make sure this is at the top of your file

st.markdown("---")
st.header("📱 Side by Side (3 Videos) with Watermark")

uploaded_files = st.file_uploader("📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sidebyside")
style_sbs = st.selectbox("🎨 Apply Style to Side-by-Side", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
], key="style_sbs")

if uploaded_files and len(uploaded_files) == 3:
    if "sbs_final_path" not in st.session_state:
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
                watermark = (
                    "drawtext=text='@USMIKASHMIRI':"
                    "x=w-mod(t*240\\,w+tw):y=h-160:"
                    "fontsize=40:fontcolor=white@0.6:"
                    "shadowcolor=black:shadowx=2:shadowy=2"
                )
                cmd = [
                    "ffmpeg", "-y", "-i", output_raw,
                    "-vf", watermark,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
                    output_final
                ]
                subprocess.run(cmd, check=True)

                # Copy output to a persistent location
                final_save_path = os.path.join("outputs", "sbs_final.mp4")
                os.makedirs("outputs", exist_ok=True)
                shutil.copy(output_final, final_save_path)

                st.session_state.sbs_final_path = final_save_path

                end_time = time.time()
                st.success(f"✅ Completed in {end_time - start_time:.2f} seconds")
                progress.progress(100)

            except Exception as e:
                st.error(f"❌ Error occurred:\n\n{e}")

        progress.empty()
        status.empty()

# Safely display video and download button
if "sbs_final_path" in st.session_state and os.path.exists(st.session_state.sbs_final_path):
    st.video(st.session_state.sbs_final_path)
    with open(st.session_state.sbs_final_path, "rb") as f:
        st.download_button("💾 Download Side-by-Side", f.read(), file_name="side_by_side.mp4", mime="video/mp4")
else:
    st.error("⚠️ Final video not available or was not saved.")


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
