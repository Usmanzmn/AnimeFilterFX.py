import streamlit as st
import tempfile
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, vfx
from moviepy.video.fx.all import fadein, fadeout
import shutil
import uuid
import subprocess

st.set_page_config(page_title="Cartoon Video App", layout="centered")
st.title("🎬 Cartoon Video Converter with Effects")

# Utility
def save_uploaded_file(uploaded_file):
    file_id = str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, f"{file_id}_{uploaded_file.name}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Feature 1: Cartoonify with Frame-by-Frame Filter
def cartoonify_video(input_path, output_path):
    try:
        # Example using FFmpeg with cartoon effect (basic)
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", "tblend=all_mode=average,framestep=2",
            "-c:a", "copy", output_path
        ]
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        st.error(f"❌ Error applying cartoon filter: {e}")
        return False

# Feature 2: Combine 3 Videos Side-by-Side with Watermark
def combine_side_by_side(video_files, output_path):
    try:
        inputs = []
        for path in video_files:
            inputs += ["-i", path]

        watermark = (
            "drawtext=text='@USMIKASHMIRI':"
            "x=w-mod(t*302\\,w+tw):"
            "y=h-160:"
            "fontsize=40:fontcolor=white@0.6:"
            "shadowcolor=black:shadowx=2:shadowy=2"
        )

        cmd = [
            "ffmpeg", "-y", *inputs,
            "-filter_complex",
            f"[0:v]scale=640:360[vid0];"
            f"[1:v]scale=640:360[vid1];"
            f"[2:v]scale=640:360[vid2];"
            f"[vid0][vid1][vid2]hstack=inputs=3,drawtext={watermark}[v]",
            "-map", "[v]",
            "-shortest",
            output_path
        ]
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        st.error(f"❌ FFmpeg merge failed: {e}")
        return False

# Feature 3: Switch Between 3 Videos with Fade and Watermark
def fade_switch_videos(video_paths, output_path):
    try:
        clips = []
        for path in video_paths:
            clip = VideoFileClip(path).resize(height=480)
            clip = clip.fx(fadein, 1).fx(fadeout, 1)
            clips.append(clip)

        final_clip = concatenate_videoclips(clips, method="compose")

        watermark = (
            "drawtext=text='@USMIKASHMIRI':"
            "x=w-mod(t*302\\,w+tw):"
            "y=h-160:"
            "fontsize=40:fontcolor=white@0.6:"
            "shadowcolor=black:shadowx=2:shadowy=2"
        )

        temp_output = output_path.replace(".mp4", "_temp.mp4")
        final_clip.write_videofile(temp_output, codec="libx264", audio_codec="aac")

        cmd = [
            "ffmpeg", "-y", "-i", temp_output,
            "-vf", watermark,
            "-c:a", "copy",
            output_path
        ]
        subprocess.run(cmd, check=True)
        os.remove(temp_output)
        return True
    except Exception as e:
        st.error(f"❌ Error during fade switch: {e}")
        return False

# UI
st.sidebar.header("Select Feature")
feature = st.sidebar.selectbox("Choose an action:", ["Cartoonify Video", "Combine 3 Videos", "Fade Switch Videos"])

if feature == "Cartoonify Video":
    st.subheader("🎨 Feature 1: Cartoonify Video")
    uploaded = st.file_uploader("Upload a video", type=["mp4", "mov"])
    if uploaded and st.button("Convert"):
        input_path = save_uploaded_file(uploaded)
        output_path = os.path.join(tempfile.gettempdir(), "cartoon_output.mp4")
        if cartoonify_video(input_path, output_path):
            st.success("✅ Cartoon effect applied!")
            st.video(output_path)

elif feature == "Combine 3 Videos":
    st.subheader("🧱 Feature 2: Combine 3 Videos Side-by-Side")
    files = st.file_uploader("Upload 3 videos", accept_multiple_files=True, type=["mp4", "mov"])
    if len(files) == 3 and st.button("Combine"):
        paths = [save_uploaded_file(f) for f in files]
        output_path = os.path.join(tempfile.gettempdir(), "combined_output.mp4")
        if combine_side_by_side(paths, output_path):
            st.success("✅ Videos combined side-by-side!")
            st.video(output_path)

elif feature == "Fade Switch Videos":
    st.subheader("🎞 Feature 3: Switch Between Videos with Fade")
    files = st.file_uploader("Upload 3 videos", accept_multiple_files=True, type=["mp4", "mov"])
    if len(files) == 3 and st.button("Create Sequence"):
        paths = [save_uploaded_file(f) for f in files]
        output_path = os.path.join(tempfile.gettempdir(), "fade_switch_output.mp4")
        if fade_switch_videos(paths, output_path):
            st.success("✅ Fade transition applied between videos!")
            st.video(output_path)
