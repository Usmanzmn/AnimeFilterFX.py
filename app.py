import streamlit as st
import os
import tempfile
from moviepy.editor import (
    VideoFileClip, concatenate_videoclips, CompositeVideoClip,
    ColorClip
)
from moviepy.video.fx.all import resize
from PIL import Image
import numpy as np

# ========== Dummy Style Functions (you can update with real models later) ==========
def pastel_style(image):
    return image  # Placeholder – Replace with actual style transformation

def cinematic_warm(image):
    return image  # Placeholder – Replace with actual filter

def get_transform_function(style):
    if style == "🌸 Soft Pastel Anime-Like Style":
        return pastel_style
    elif style == "🎞️ Cinematic Warm Filter":
        return cinematic_warm
    return lambda x: x

# ========== Streamlit UI ==========
st.set_page_config(page_title="Video Filter App", layout="wide")
st.title("🎬 AI Cartoon & Filter Video App")

# ---------- Feature 1: Cartoon Style ----------
st.markdown("---")
st.header("🎨 Apply Cartoon or Filter Style to a Single Video")

uploaded_video = st.file_uploader("📤 Upload Video", type=["mp4"], key="single_video")
style = st.selectbox("🎨 Choose a Style", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
])

if uploaded_video:
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        with open(input_path, "wb") as out:
            out.write(uploaded_video.read())

        try:
            transform_func = get_transform_function(style) if style != "None" else lambda x: x
            clip = VideoFileClip(input_path).fl_image(transform_func)
            output_path = os.path.join(tmpdir, "styled_output.mp4")
            clip.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            st.video(output_path)
            with open(output_path, "rb") as f:
                st.download_button("💾 Download Styled Video", f.read(), file_name="styled_video.mp4", mime="video/mp4")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ---------- Feature 2: Side-by-Side Comparison ----------
st.markdown("---")
st.header("🆚 Compare Two Videos Side-by-Side")

uploaded_duo = st.file_uploader("📤 Upload 2 Videos", type=["mp4"], accept_multiple_files=True, key="duo")
style_duo = st.selectbox("🎨 Apply Style to Comparison", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
], key="style_duo")

if uploaded_duo and len(uploaded_duo) == 2:
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for i, f in enumerate(uploaded_duo):
            path = os.path.join(tmpdir, f"video{i}.mp4")
            with open(path, "wb") as out:
                out.write(f.read())
            paths.append(path)

        try:
            transform_func = get_transform_function(style_duo) if style_duo != "None" else lambda x: x
            clips = [VideoFileClip(p).fl_image(transform_func).resize(height=540) for p in paths]
            min_duration = min([clip.duration for clip in clips])
            clips = [clip.subclip(0, min_duration) for clip in clips]

            side_by_side = CompositeVideoClip([
                clips[0].set_position(("left", "center")),
                clips[1].set_position(("right", "center"))
            ], size=(clips[0].w + clips[1].w, clips[0].h))

            output_path = os.path.join(tmpdir, "comparison.mp4")
            watermark = "drawtext=text='@USMIKASHMIRI':x=w-mod(t*240\\,w+tw):y=h-160:fontsize=40:fontcolor=white@0.6:shadowcolor=black:shadowx=2:shadowy=2"
            raw_path = os.path.join(tmpdir, "raw.mp4")

            side_by_side.write_videofile(raw_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

            final_path = os.path.join(tmpdir, "comparison_watermarked.mp4")
            cmd = f'ffmpeg -y -i "{raw_path}" -vf "{watermark}" -c:v libx264 -preset fast -crf 22 -pix_fmt yuv420p "{final_path}"'
            os.system(cmd)

            st.video(final_path)
            with open(final_path, "rb") as f:
                st.download_button("💾 Download Side-by-Side Video", f.read(), file_name="side_by_side.mp4", mime="video/mp4")

        except Exception as e:
            st.error(f"❌ Error: {e}")
elif uploaded_duo and len(uploaded_duo) != 2:
    st.warning("⚠️ Please upload exactly 2 videos.")

# ---------- Feature 3: Sequential Playback ----------
st.markdown("---")
st.header("🕒 Play 3 Videos Sequentially with Watermark and Slight Fade")

uploaded_seq = st.file_uploader("📤 Upload 3 Videos (for sequential playback)", type=["mp4"], accept_multiple_files=True, key="sequential")
style_seq = st.selectbox("🎨 Apply Style to Sequential Video", [
    "None",
    "🌸 Soft Pastel Anime-Like Style",
    "🎞️ Cinematic Warm Filter"
], key="style_sequential")

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
            clips = []

            # Load and apply style
            video_clips = [VideoFileClip(p).fl_image(transform_func).resize(height=1080) for p in paths]
            max_duration = max([clip.duration for clip in video_clips])

            # All visible for 1s at full opacity
            start_clips = []
            for i in range(3):
                pos_x = i * 640
                start_clips.append(video_clips[i].subclip(0, 1).set_position((pos_x, 0)))
            full_start = CompositeVideoClip(start_clips, size=(1920, 1080)).set_duration(1)
            clips.append(full_start)

            # Play each sequentially, others faded
            for i in range(3):
                dur = video_clips[i].duration
                side_clips = []
                for j in range(3):
                    clip = video_clips[j].resize(height=1080).set_position((j * 640, 0)).set_duration(dur)
                    if j != i:
                        clip = clip.set_opacity(0.4)
                    side_clips.append(clip)
                bg = ColorClip((1920, 1080), color=(0, 0, 0)).set_duration(dur)
                combined = CompositeVideoClip([bg] + side_clips).set_duration(dur)
                clips.append(combined)

            final = concatenate_videoclips(clips)
            raw_output = os.path.join(tmpdir, "sequential_raw.mp4")
            final.write_videofile(raw_output, codec="libx264", audio_codec="aac", verbose=False, logger=None)

            # Watermark scrolls across bottom
            watermark = "drawtext=text='@USMIKASHMIRI':x=w-mod(t*240\\,w+tw):y=h-160:fontsize=40:fontcolor=white@0.6:shadowcolor=black:shadowx=2:shadowy=2"
            final_output = os.path.join(tmpdir, "sequential_final.mp4")
            cmd = f'ffmpeg -y -i "{raw_output}" -vf "{watermark}" -c:v libx264 -preset fast -crf 22 -pix_fmt yuv420p "{final_output}"'
            os.system(cmd)

            st.video(final_output)
            with open(final_output, "rb") as f:
                st.download_button("💾 Download Final Sequential Video", f.read(), file_name="sequential_output.mp4", mime="video/mp4")

        except Exception as e:
            st.error(f"❌ Error: {e}")
elif uploaded_seq and len(uploaded_seq) != 3:
    st.warning("⚠️ Please upload exactly 3 videos.")
