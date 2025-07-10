import streamlit as st
import cv2
import numpy as np
import tempfile
import time
import os
from moviepy.editor import (
    VideoFileClip,
    CompositeVideoClip,
    ColorClip,
    concatenate_videoclips,
    ImageClip
)

# ---------------------- Streamlit UI Setup ----------------------
st.set_page_config(page_title="Anime + Cinematic Video Filters", page_icon="🎨")
st.title("🎨 Anime & Cinematic Style Video Transformation")

# ---------------------- Filter Functions ----------------------
def transform_soft_pastel_anime(frame):
    blur = cv2.bilateralFilter(frame, 9, 75, 75)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)
    s *= 0.6
    v *= 1.2
    pastel = cv2.merge([h, np.clip(s, 0, 255), np.clip(v, 0, 255)])
    pastel = cv2.cvtColor(pastel.astype(np.uint8), cv2.COLOR_HSV2BGR)
    return pastel

def transform_cinematic_warm(frame):
    lut = np.array([min(255, int(i * 1.1 + 10)) for i in range(256)]).astype("uint8")
    warm = cv2.LUT(frame, lut)
    hsv = cv2.cvtColor(warm, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)
    h = (h + 10) % 180
    s *= 1.1
    v *= 1.05
    final = cv2.merge([h, np.clip(s, 0, 255), np.clip(v, 0, 255)])
    return cv2.cvtColor(final.astype(np.uint8), cv2.COLOR_HSV2BGR)

def get_transform_function(option):
    return {
        "🌸 Soft Pastel Anime-Like Style": transform_soft_pastel_anime,
        "🎞️ Cinematic Warm Filter": transform_cinematic_warm,
    }.get(option, lambda x: x)

# ---------------------- Feature 1: Single Video Style Filter ----------------------
st.header("🎨 Apply Style Filter to a Single Video")

uploaded_file = st.file_uploader("📤 Upload a Video", type=["mp4", "mov", "avi"], key="single")
style_option = st.selectbox("🎨 Choose a Style", (
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
), key="style_single")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_input:
        tmp_input.write(uploaded_file.read())
        input_path = tmp_input.name

    try:
        transform_func = get_transform_function(style_option)

        with st.spinner("✨ Applying style transformation... Please wait."):
            clip = VideoFileClip(input_path)
            transformed_clip = clip.fl_image(transform_func)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_output:
                output_path = tmp_output.name
                transformed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🎥 Original Video")
            st.video(input_path)
        with col2:
            st.subheader("🧑‍🎨 Styled Video")
            with open(output_path, "rb") as f:
                st.video(f.read())
                st.download_button("💾 Download Styled Video", f, "styled_video.mp4", mime="video/mp4")

    except Exception as e:
        st.error(f"❌ Error: {e}")

# ---------------------- Feature 2: Merge 3 Vertical Shorts Side-by-Side ----------------------
st.markdown("---")
st.header("🎬 Merge 3 Vertical Shorts Side-by-Side (16:9) + Apply Style")

uploaded_files = st.file_uploader("📤 Upload 3 Vertical Videos", type=["mp4"], accept_multiple_files=True, key="merge")
style_merge = st.selectbox("🎨 Apply Style to Merged Video", (
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
), key="style_merge")

if uploaded_files and len(uploaded_files) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        file_paths = []
        for i, file in enumerate(uploaded_files):
            path = os.path.join(tmpdir, f"input{i}.mp4")
            with open(path, "wb") as f:
                f.write(file.read())
            file_paths.append(path)

        merged_path = os.path.join(tmpdir, "merged.mp4")

        command = f"""
        ffmpeg -y -i {file_paths[0]} -i {file_paths[1]} -i {file_paths[2]} -filter_complex "
        [0:v]scale=640:1080[v0];
        [1:v]scale=640:1080[v1];
        [2:v]scale=640:1080[v2];
        [v0][v1][v2]hstack=inputs=3[stacked];
        [stacked]drawtext=text='@USMIKASHMIRI':x='w-(t*100)%w':y='h-150':fontsize=40:fontcolor=white@0.3:shadowcolor=black:shadowx=2:shadowy=2[outv]
        " -map "[outv]" -c:v libx264 -preset fast -crf 22 -pix_fmt yuv420p {merged_path}
        """
        result = os.system(command)

        if result == 0:
            st.success("✅ Merged video created!")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🎥 Before Style")
                st.video(merged_path)

            try:
                transform_func = get_transform_function(style_merge)
                clip = VideoFileClip(merged_path)
                styled_clip = clip.fl_image(transform_func)

                styled_path = os.path.join(tmpdir, "styled_merged.mp4")
                styled_clip.write_videofile(styled_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

                with col2:
                    st.subheader("🧑‍🎨 After Style")
                    with open(styled_path, "rb") as f:
                        st.video(f.read())
                        st.download_button("💾 Download Styled Video", f, "styled_merged.mp4", mime="video/mp4")

            except Exception as e:
                st.error(f"❌ Error applying style: {e}")
        else:
            st.error("❌ FFmpeg merge failed.")
elif uploaded_files and len(uploaded_files) != 3:
    st.warning("⚠️ Please upload exactly 3 vertical videos.")

# ---------------------- Feature 3: Sequential Video Playback ----------------------
st.markdown("---")
st.header("🕒 Play 3 Videos Sequentially in One Landscape Frame (Side-by-Side Order with Faded Neighbors)")

uploaded_seq = st.file_uploader("📤 Upload 3 Videos (for sequential playback)", type=["mp4"], accept_multiple_files=True, key="sequential")
style_seq = st.selectbox("🎨 Apply Style to Sequential Video", (
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
), key="style_sequential")

if uploaded_seq and len(uploaded_seq) == 3:
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for i, f in enumerate(uploaded_seq):
            p = os.path.join(tmpdir, f"seq{i}.mp4")
            with open(p, "wb") as out:
                out.write(f.read())
            paths.append(p)

        try:
            transform_func = get_transform_function(style_seq) if style_seq != "None" else lambda x: x

            # Load all clips
            clips_raw = [VideoFileClip(p).resize(height=1080) for p in paths]
            clips_transformed = [clip.fl_image(transform_func) for clip in clips_raw]

            # Create 2-second intro where all 3 videos are fully visible side-by-side
            intro_clips = [clip.resize(width=640) for clip in clips_transformed]
            intro_stacked = CompositeVideoClip([
                intro_clips[0].set_position((0, 0)),
                intro_clips[1].set_position((640, 0)),
                intro_clips[2].set_position((1280, 0)),
            ], size=(1920, 1080)).subclip(0, 2)

            # Sequential playback
            sequences = []
            for i in range(3):
                main_clip = clips_transformed[i]
                dur = main_clip.duration

                side_1 = ImageClip(transform_func(clips_raw[0].get_frame(0))).resize(height=1080).set_duration(dur).set_position((0, 0)).set_opacity(0.6 if i != 0 else 1)
                side_2 = ImageClip(transform_func(clips_raw[1].get_frame(0))).resize(height=1080).set_duration(dur).set_position((640, 0)).set_opacity(0.6 if i != 1 else 1)
                side_3 = ImageClip(transform_func(clips_raw[2].get_frame(0))).resize(height=1080).set_duration(dur).set_position((1280, 0)).set_opacity(0.6 if i != 2 else 1)

                bg = ColorClip((1920, 1080), color=(0, 0, 0)).set_duration(dur)
                main_clip_positioned = main_clip.resize(width=640).set_position((640 * i, 0))

                overlay = CompositeVideoClip([
                    bg,
                    side_1 if i != 0 else main_clip_positioned,
                    side_2 if i != 1 else main_clip_positioned,
                    side_3 if i != 2 else main_clip_positioned
                ], size=(1920, 1080)).set_duration(dur)

                sequences.append(overlay)

            final = concatenate_videoclips([intro_stacked] + sequences)
            out_path = os.path.join(tmpdir, "sequential_output.mp4")
            final.write_videofile(out_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

            st.video(out_path)
            with open(out_path, "rb") as f:
                st.download_button("💾 Download Sequential Side-by-Side Video", f.read(), file_name="sequential_visible.mp4", mime="video/mp4")

        except Exception as e:
            st.error(f"❌ Error: {e}")
elif uploaded_seq and len(uploaded_seq) != 3:
    st.warning("⚠️ Please upload exactly 3 videos.")
