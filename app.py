import streamlit as st
import os
import tempfile
import subprocess
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image
import numpy as np
import cv2

st.set_page_config(page_title="🎬 AI Video Effects App", layout="centered")
st.title("🎬 AI Video Effects App")

# ---------- Style Filter Functions ----------
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

# ---------- Watermark ----------
def apply_watermark(input_path, output_path, text="@USMIKASHMIRI"):
    watermark_filter = (
        "scale=ceil(iw/2)*2:ceil(ih/2)*2,"
        f"drawtext=fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':"
        f"text='{text}':x=w-mod(t*240\\,w+tw):y=h-160:"
        "fontsize=40:fontcolor=white@0.6:shadowcolor=black:shadowx=2:shadowy=2"
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
        st.error("❌ FFmpeg watermarking failed.")
        st.code(e.stderr.decode(), language="bash")
        raise

import shutil  # Add this at the top

# ========== FEATURE 1 ==========
st.markdown("---")
st.header("🎨 Apply Style to Single Video")

uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4"], key="style_upload")
style = st.selectbox("🎨 Choose a Style", ["None", "🌸 Soft Pastel Anime-Like Style", "🎞️ Cinematic Warm Filter"], key="style_select")

generate = st.button("🚀 Generate Styled Video")
output_dir = "processed_videos"
os.makedirs(output_dir, exist_ok=True)

if uploaded_file and generate:
    start_time = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        clip = VideoFileClip(input_path)
        styled_clip = clip.fl_image(get_transform_function(style))
        styled_temp = os.path.join(tmpdir, "styled.mp4")
        styled_clip.write_videofile(styled_temp, codec="libx264", audio_codec="aac")

        preview_original_temp = os.path.join(tmpdir, "original_preview.mp4")
        preview_styled_temp = os.path.join(tmpdir, "styled_preview.mp4")
        clip.resize(height=360).write_videofile(preview_original_temp, codec="libx264", audio_codec="aac")
        VideoFileClip(styled_temp).resize(height=360).write_videofile(preview_styled_temp, codec="libx264", audio_codec="aac")

        # Copy files to persistent directory
        orig_final = os.path.join(output_dir, "original.mp4")
        styled_final = os.path.join(output_dir, "styled.mp4")
        preview_orig_final = os.path.join(output_dir, "original_preview.mp4")
        preview_styled_final = os.path.join(output_dir, "styled_preview.mp4")

        shutil.copy(input_path, orig_final)
        shutil.copy(styled_temp, styled_final)
        shutil.copy(preview_original_temp, preview_orig_final)
        shutil.copy(preview_styled_temp, preview_styled_final)

        # Save in session
        st.session_state["styled_output_path"] = styled_final
        st.session_state["original_path"] = orig_final
        st.session_state["preview_original"] = preview_orig_final
        st.session_state["preview_styled"] = preview_styled_final
        st.session_state["process_time"] = time.time() - start_time

# Display video + downloads
if "styled_output_path" in st.session_state:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔹 Original")
        st.video(st.session_state["preview_original"])
        with open(st.session_state["original_path"], "rb") as f:
            st.download_button("⬇️ Download Original", f.read(), file_name="original.mp4")

    with col2:
        st.subheader("🔸 Styled")
        st.video(st.session_state["preview_styled"])
        with open(st.session_state["styled_output_path"], "rb") as f:
            st.download_button("⬇️ Download Styled", f.read(), file_name="styled.mp4")

    st.success(f"✅ Done in {st.session_state['process_time']:.2f} sec")

# ========== FEATURE 2 (1280x720, Fit 3 Videos) ==========
st.markdown("---")
st.header("📱 Side-by-Side (1280x720, 3 Videos) with Watermark")

uploaded_files = st.file_uploader("📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sidebyside")
style_sbs = st.selectbox("🎨 Style for Side-by-Side", ["None", "🌸 Soft Pastel Anime-Like Style", "🎞️ Cinematic Warm Filter"], key="style_sbs")

if uploaded_files and len(uploaded_files) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for i, file in enumerate(uploaded_files):
            path = os.path.join(tmpdir, f"video{i}.mp4")
            with open(path, "wb") as f:
                f.write(file.read())
            paths.append(path)

        transform_func = get_transform_function(style_sbs)
        
        # Resize to fit 3 in 1280x720: width=426, height=720
        target_width = 426
        target_height = 720

        clips = [VideoFileClip(p).fl_image(transform_func).resize((target_width, target_height)) for p in paths]
        duration = min(c.duration for c in clips)
        clips = [c.subclip(0, duration) for c in clips]

        # Composite into one 1280x720 video
        side_by_side = CompositeVideoClip([
            clips[0].set_position((0, 0)),
            clips[1].set_position((426, 0)),
            clips[2].set_position((852, 0))
        ], size=(1280, 720)).set_duration(duration)

        raw_output = os.path.join(tmpdir, "sbs_raw.mp4")
        side_by_side.write_videofile(raw_output, codec="libx264", audio_codec="aac")

        final_output = os.path.join(tmpdir, "sbs_final.mp4")
        apply_watermark(raw_output, final_output)

        st.video(final_output)
        with open(final_output, "rb") as f:
            st.download_button("💾 Download Side-by-Side", f.read(), file_name="side_by_side_1280x720.mp4")

    st.success("✅ 3 videos combined into 1280x720 perfectly!")

# ========== FEATURE 3 ==========
st.markdown("---")
st.header("🕒 Play 3 Videos Sequentially with Fade & Watermark")
uploaded_seq = st.file_uploader("📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sequential")
style_seq = st.selectbox("🎨 Style for Sequential Video", ["None", "🌸 Soft Pastel Anime-Like Style", "🎞️ Cinematic Warm Filter"], key="style_seq")

if uploaded_seq and len(uploaded_seq) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for i, f in enumerate(uploaded_seq):
            p = os.path.join(tmpdir, f"seq{i}.mp4")
            with open(p, "wb") as out:
                out.write(f.read())
            paths.append(p)

        transform = get_transform_function(style_seq)
        video_clips = [VideoFileClip(p).fl_image(transform).resize(height=720) for p in paths]

        clips = []
        for i in range(3):
            dur = video_clips[i].duration
            main = video_clips[i]
            others = []
            for j in range(3):
                if j == i:
                    clip = main.set_position((j * 640, 0))
                else:
                    still = video_clips[j].to_ImageClip(t=1).set_duration(dur).set_position((j * 640, 0)).set_opacity(0.4)
                    clip = still
                others.append(clip)
            composite = CompositeVideoClip(others, size=(1920, 720)).set_duration(dur)
            clips.append(composite)

        final = concatenate_videoclips(clips)
        raw = os.path.join(tmpdir, "seq_raw.mp4")
        final.write_videofile(raw, codec="libx264", audio_codec="aac")

        final_output = os.path.join(tmpdir, "seq_final.mp4")
        apply_watermark(raw, final_output)

        st.video(final_output)
        with open(final_output, "rb") as f:
            st.download_button("💾 Download Sequential", f.read(), file_name="sequential_output.mp4")
    st.success("✅ Sequential video done!")

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
