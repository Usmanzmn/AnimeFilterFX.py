import streamlit as st
import os
import tempfile
import subprocess
import time
import shutil
from moviepy.editor import VideoFileClip, CompositeVideoClip
from PIL import Image
import numpy as np
import cv2
from io import BytesIO

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
    subprocess.run(cmd, check=True)

# ---------- Rain Overlay Function ----------
def overlay_rain(input_path, output_path, rain_type="Rain Type 2"):
    rain_url = "https://cdn.pixabay.com/video/2023/07/11/173723-842185319_large.mp4"
    opacity = 0.25 if rain_type == "Rain Type 1" else 0.5

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-i", rain_url,
        "-filter_complex",
        f"[1:v]format=rgba,colorchannelmixer=aa={opacity}[rain];[0:v][rain]overlay=0:0:shortest=1",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)

# ---------- FEATURE 1: Apply Style + Rain + Watermark ----------
st.markdown("---")
st.header("🎨 Apply Style to Single Video")

uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4"], key="style_upload")
style = st.selectbox("🎨 Choose a Style", ["None", "🌸 Soft Pastel Anime-Like Style", "🎞️ Cinematic Warm Filter"], key="style_select")
add_watermark = st.checkbox("✅ Add Watermark (@USMIKASHMIRI)", value=False)
add_rain = st.checkbox("🌧️ Add Rain Overlay", value=False)
rain_type = None
if add_rain:
    rain_type = st.radio("Choose Rain Type", ["Rain Type 1", "Rain Type 2"], horizontal=True)

if uploaded_file and st.button("🚀 Generate Styled Video"):
    start_time = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        clip = VideoFileClip(input_path)
        styled_clip = clip.fl_image(get_transform_function(style))
        styled_temp = os.path.join(tmpdir, "styled.mp4")
        styled_clip.write_videofile(styled_temp, codec="libx264", audio_codec="aac")

        styled_final_path = styled_temp

        if add_watermark:
            watermarked = os.path.join(tmpdir, "styled_watermarked.mp4")
            apply_watermark(styled_final_path, watermarked)
            styled_final_path = watermarked

        if add_rain:
            rained = os.path.join(tmpdir, "styled_rain.mp4")
            overlay_rain(styled_final_path, rained, rain_type=rain_type)
            styled_final_path = rained

        preview = os.path.join(tmpdir, "preview.mp4")
        VideoFileClip(styled_final_path).resize(height=360).write_videofile(preview, codec="libx264", audio_codec="aac")

        st.session_state["styled_output_path"] = styled_final_path
        st.session_state["preview_styled"] = preview
        st.session_state["process_time"] = time.time() - start_time

if "styled_output_path" in st.session_state:
    st.video(st.session_state["preview_styled"])
    with open(st.session_state["styled_output_path"], "rb") as f:
        st.download_button("⬇️ Download Styled Video", f.read(), file_name="styled_final.mp4")
    st.success(f"✅ Done in {st.session_state['process_time']:.2f} sec")


# ========== FEATURE 2 (Side-by-Side: Raw Unstyled & Final Styled+Watermarked) ==========
st.markdown("---")
st.header("📱 Side-by-Side (1280x720, 3 Videos) with Watermark")

# Initialize session state
if "sbs_raw_output" not in st.session_state:
    st.session_state["sbs_raw_output"] = None
if "sbs_final_output" not in st.session_state:
    st.session_state["sbs_final_output"] = None

uploaded_files = st.file_uploader(
    "📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sidebyside"
)

style_sbs = st.selectbox(
    "🎨 Style for Final Video",
    ["None", "🌸 Soft Pastel Anime-Like Style", "🎞️ Cinematic Warm Filter"],
    key="style_sbs"
)

if uploaded_files and len(uploaded_files) == 3:
    if st.button("🚀 Generate Side-by-Side Video"):
        with st.spinner("Processing..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                paths = []
                for i, file in enumerate(uploaded_files):
                    path = os.path.join(tmpdir, f"video{i}.mp4")
                    with open(path, "wb") as f:
                        f.write(file.read())
                    paths.append(path)

                target_size = (426, 720)
                transform_func = get_transform_function(style_sbs)

                # Load raw unstyled clips
                raw_clips = []
                styled_clips = []
                min_duration = None

                for path in paths:
                    clip_raw = VideoFileClip(path).resize(target_size)
                    clip_styled = clip_raw.fl_image(transform_func)

                    duration = clip_raw.duration
                    if min_duration is None or duration < min_duration:
                        min_duration = duration

                    raw_clips.append(clip_raw)
                    styled_clips.append(clip_styled)

                # Trim both sets to shortest clip duration
                raw_clips = [c.subclip(0, min_duration) for c in raw_clips]
                styled_clips = [c.subclip(0, min_duration) for c in styled_clips]

                # Create raw (unstyled) side-by-side
                raw_combined = CompositeVideoClip([
                    raw_clips[0].set_position((0, 0)),
                    raw_clips[1].set_position((426, 0)),
                    raw_clips[2].set_position((852, 0))
                ], size=(1280, 720)).set_duration(min_duration)

                raw_output = os.path.join(tmpdir, "sbs_raw.mp4")
                raw_combined.write_videofile(raw_output, codec="libx264", audio_codec="aac")

                # Create styled + watermark version
                styled_combined = CompositeVideoClip([
                    styled_clips[0].set_position((0, 0)),
                    styled_clips[1].set_position((426, 0)),
                    styled_clips[2].set_position((852, 0))
                ], size=(1280, 720)).set_duration(min_duration)

                styled_temp = os.path.join(tmpdir, "styled_temp.mp4")
                styled_combined.write_videofile(styled_temp, codec="libx264", audio_codec="aac")

                final_output = os.path.join(tmpdir, "sbs_final.mp4")
                apply_watermark(styled_temp, final_output)

                # Save to session state
                with open(raw_output, "rb") as f:
                    st.session_state["sbs_raw_output"] = f.read()
                with open(final_output, "rb") as f:
                    st.session_state["sbs_final_output"] = f.read()

            st.success("✅ Raw and Final videos generated successfully!")

# Show raw and final output
if st.session_state["sbs_raw_output"]:
    st.subheader("🎬 Raw Video (No Style, No Watermark)")
    st.video(st.session_state["sbs_raw_output"])
    st.download_button("⬇️ Download Raw", st.session_state["sbs_raw_output"], file_name="raw_unstyled.mp4")

if st.session_state["sbs_final_output"]:
    st.subheader("🌟 Final Video (Styled + Watermark)")
    st.video(st.session_state["sbs_final_output"])
    st.download_button("⬇️ Download Final", st.session_state["sbs_final_output"], file_name="styled_watermarked.mp4")

# ========== FEATURE 3 (Sequential Playback with 1-Second Triple Intro) ==========
st.markdown("---")
st.header("🕒 Play 3 Videos Sequentially with 1s Intro & Watermark")

# Initialize session state
st.session_state.setdefault("seq_raw_output", None)
st.session_state.setdefault("seq_final_output", None)

uploaded_seq = st.file_uploader(
    "📤 Upload 3 Videos", type=["mp4"], accept_multiple_files=True, key="sequential"
)

style_seq = st.selectbox(
    "🎨 Style for Final Video",
    ["None", "🌸 Soft Pastel Anime-Like Style", "🎞️ Cinematic Warm Filter"],
    key="style_seq"
)

if uploaded_seq and len(uploaded_seq) == 3:
    if st.button("🚀 Generate Sequential Video"):
        with st.spinner("Processing..."):
            import os, tempfile
            from moviepy.editor import VideoFileClip, CompositeVideoClip, concatenate_videoclips

            with tempfile.TemporaryDirectory() as tmpdir:
                # Save uploaded videos
                paths = []
                for i, file in enumerate(uploaded_seq):
                    file_path = os.path.join(tmpdir, f"seq{i}.mp4")
                    with open(file_path, "wb") as out:
                        out.write(file.read())
                    paths.append(file_path)

                # Prepare transform and video clips
                transform = get_transform_function(style_seq)
                width, height = int(1280 / 3), 720

                video_raw = [VideoFileClip(p).resize((width, height)) for p in paths]
                video_styled = [VideoFileClip(p).fl_image(transform).resize((width, height)) for p in paths]

                raw_clips, styled_clips = [], []

                # ========== SEGMENT 0: Intro - 1 second, all 3 play normally ==========
                intro_duration = 1
                raw_intro = CompositeVideoClip([
                    video_raw[0].subclip(0, intro_duration).set_position((0, 0)),
                    video_raw[1].subclip(0, intro_duration).set_position((width, 0)),
                    video_raw[2].subclip(0, intro_duration).set_position((2 * width, 0))
                ], size=(1280, height))

                styled_intro = CompositeVideoClip([
                    video_styled[0].subclip(0, intro_duration).set_position((0, 0)),
                    video_styled[1].subclip(0, intro_duration).set_position((width, 0)),
                    video_styled[2].subclip(0, intro_duration).set_position((2 * width, 0))
                ], size=(1280, height))

                raw_clips.append(raw_intro)
                styled_clips.append(styled_intro)

                # ========== SEGMENTS 1-3: One plays, others frozen & faded ==========
                for i in range(3):
                    # Full duration of the current main video
                    dur = video_raw[i].duration

                    # Raw parts
                    raw_parts = []
                    styled_parts = []

                    for j in range(3):
                        if j == i:
                            # Play full
                            raw_clip = video_raw[j]
                            styled_clip = video_styled[j]
                        else:
                            # Frozen + faded image
                            raw_clip = video_raw[j].to_ImageClip(t=1).set_duration(dur).set_opacity(0.4)
                            styled_clip = video_styled[j].to_ImageClip(t=1).set_duration(dur).set_opacity(0.4)

                        raw_parts.append(raw_clip.set_position((j * width, 0)))
                        styled_parts.append(styled_clip.set_position((j * width, 0)))

                    raw_clips.append(CompositeVideoClip(raw_parts, size=(1280, height)).set_duration(dur))
                    styled_clips.append(CompositeVideoClip(styled_parts, size=(1280, height)).set_duration(dur))

                # ========== CONCATENATE ==========
                raw_sequence = concatenate_videoclips(raw_clips)
                styled_sequence = concatenate_videoclips(styled_clips)

                # ========== EXPORT RAW ==========
                raw_output_path = os.path.join(tmpdir, "seq_raw.mp4")
                raw_sequence.write_videofile(raw_output_path, codec="libx264", audio_codec="aac")

                # ========== EXPORT STYLED + WATERMARK ==========
                styled_temp_path = os.path.join(tmpdir, "seq_styled_temp.mp4")
                styled_sequence.write_videofile(styled_temp_path, codec="libx264", audio_codec="aac")

                final_output_path = os.path.join(tmpdir, "seq_final.mp4")
                apply_watermark(styled_temp_path, final_output_path)

                # ========== SAVE TO SESSION ==========
                with open(raw_output_path, "rb") as f:
                    st.session_state["seq_raw_output"] = f.read()
                with open(final_output_path, "rb") as f:
                    st.session_state["seq_final_output"] = f.read()

        st.success("✅ Sequential videos generated with 1-second intro + full playback + watermark!")

# ========== DISPLAY ==========
if st.session_state["seq_raw_output"]:
    st.subheader("🎬 Raw Sequential Video (No Style, No Watermark)")
    st.video(st.session_state["seq_raw_output"])
    st.download_button("⬇️ Download Raw", st.session_state["seq_raw_output"], file_name="sequential_raw.mp4")

if st.session_state["seq_final_output"]:
    st.subheader("🌟 Final Sequential Video (Styled + Watermark)")
    st.video(st.session_state["seq_final_output"])
    st.download_button("⬇️ Download Final", st.session_state["seq_final_output"], file_name="sequential_styled.mp4")


from io import BytesIO  # ✅ Add this import at the top of your file

# ========== FEATURE 4 ==========
st.markdown("---")
st.header("🖼️ Combine Thumbnails from 3 Videos (1280x720)")

uploaded_thumb_files = st.file_uploader(
    "📤 Upload 3 Videos", 
    type=["mp4"], 
    accept_multiple_files=True, 
    key="thumbnails"
)

if uploaded_thumb_files and len(uploaded_thumb_files) == 3:
    st.subheader("⏱️ Select timestamps (in seconds) for each video")
    timestamps = [
        st.number_input(
            f"Timestamp for video {i+1}",
            min_value=0.0,
            value=1.0,
            step=0.5,
            key=f"ts_{i}"
        )
        for i in range(3)
    ]

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
            buffer.seek(0)  # ✅ Make sure the buffer is at the start

            st.image(buffer.getvalue(), caption="Combined Thumbnail (1280x720)", use_container_width=True)
            st.download_button(
                "💾 Download Thumbnail", 
                buffer.getvalue(), 
                file_name="combined_thumbnail.jpg", 
                mime="image/jpeg"
            )
