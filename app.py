import streamlit as st
import os
import tempfile
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
from moviepy.video.fx.all import crop
import numpy as np
import cv2
import subprocess

# Cartoon effect using OpenCV
def cartoonify(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    gray = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9
    )
    color = cv2.bilateralFilter(image, 9, 300, 300)
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    return cartoon

# Apply filter based on user selection
def get_transform_function(style):
    def transform(frame):
        if style == "Cartoon":
            return cartoonify(frame)
        elif style == "Grayscale":
            return cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        elif style == "Invert":
            return cv2.bitwise_not(frame)
        else:
            return frame
    return transform

# Streamlit UI
st.set_page_config(page_title="Cartoonify Video App", layout="centered")
st.title("🎬 AI Cartoonify Your Video")

option = st.sidebar.selectbox("Choose Feature", [
    "1️⃣ Apply Style to Single Video",
    "2️⃣ Merge 2 Videos with Style",
    "3️⃣ Add Logo to Video"
])

# Feature 1: Apply style to a single video
if option == "1️⃣ Apply Style to Single Video":
    st.subheader("Upload a Video and Apply Cartoon/Other Effects")

    uploaded_file = st.file_uploader("Upload a Video", type=["mp4", "mov", "avi"])
    style = st.selectbox("Select Style", ["Cartoon", "Grayscale", "Invert", "None"])

    if uploaded_file and st.button("Process Video"):
        start_time = time.time()
        progress = st.progress(0, text="Initializing...")

        with tempfile.TemporaryDirectory() as tmpdir:
            progress.progress(10, text="📥 Saving uploaded video...")
            input_path = os.path.join(tmpdir, "input.mp4")
            with open(input_path, "wb") as f:
                f.write(uploaded_file.read())

            progress.progress(30, text="🎞️ Loading video...")
            clip = VideoFileClip(input_path)

            progress.progress(60, text="🎨 Applying style...")
            transform_func = get_transform_function(style)
            styled = clip.fl_image(transform_func)

            output_path = os.path.join(tmpdir, "styled.mp4")
            progress.progress(80, text="💾 Saving styled video...")
            styled.write_videofile(output_path, codec="libx264", audio_codec="aac")

            progress.progress(100, text="✅ Done!")
            st.video(output_path)
            st.success(f"Video processed in {int(time.time() - start_time)}s")

# Feature 2: Merge two videos with a selected effect
elif option == "2️⃣ Merge 2 Videos with Style":
    st.subheader("Upload Two Videos and Merge with Style")

    uploaded1 = st.file_uploader("Upload First Video", key="vid1")
    uploaded2 = st.file_uploader("Upload Second Video", key="vid2")
    style = st.selectbox("Select Style for Both Videos", ["Cartoon", "Grayscale", "Invert", "None"])

    if uploaded1 and uploaded2 and st.button("Merge and Process"):
        start_time = time.time()
        progress = st.progress(0, text="⏳ Starting...")

        with tempfile.TemporaryDirectory() as tmpdir:
            progress.progress(10, text="📥 Saving uploaded videos...")
            path1 = os.path.join(tmpdir, "vid1.mp4")
            with open(path1, "wb") as f1:
                f1.write(uploaded1.read())
            path2 = os.path.join(tmpdir, "vid2.mp4")
            with open(path2, "wb") as f2:
                f2.write(uploaded2.read())

            progress.progress(30, text="🎞️ Loading videos...")
            clip1 = VideoFileClip(path1)
            clip2 = VideoFileClip(path2)

            transform = get_transform_function(style)
            progress.progress(60, text="🎨 Applying style...")
            styled1 = clip1.fl_image(transform)
            styled2 = clip2.fl_image(transform)

            progress.progress(80, text="📽️ Merging videos...")
            final_clip = concatenate_videoclips([styled1, styled2])
            output_path = os.path.join(tmpdir, "merged.mp4")
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

            progress.progress(100, text="✅ Done!")
            st.video(output_path)
            st.success(f"Merged video created in {int(time.time() - start_time)}s")

# Feature 3: Add logo to video
elif option == "3️⃣ Add Logo to Video":
    st.subheader("Upload Video and Logo to Overlay")

    video_file = st.file_uploader("Upload Main Video", type=["mp4"], key="mainvid")
    logo_file = st.file_uploader("Upload Logo Image (PNG)", type=["png"], key="logo")

    if video_file and logo_file and st.button("Overlay Logo"):
        start_time = time.time()
        progress = st.progress(0, text="Initializing...")

        with tempfile.TemporaryDirectory() as tmpdir:
            progress.progress(10, text="📥 Saving uploaded files...")
            video_path = os.path.join(tmpdir, "main.mp4")
            logo_path = os.path.join(tmpdir, "logo.png")

            with open(video_path, "wb") as fvid:
                fvid.write(video_file.read())
            with open(logo_path, "wb") as flog:
                flog.write(logo_file.read())

            output_path = os.path.join(tmpdir, "output_with_logo.mp4")
            progress.progress(60, text="🔧 Overlaying logo with FFmpeg...")

            ffmpeg_cmd = [
                "ffmpeg",
                "-i", video_path,
                "-i", logo_path,
                "-filter_complex", "overlay=W-w-10:H-h-10",
                "-codec:a", "copy",
                output_path
            ]

            subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            progress.progress(100, text="✅ Done!")
            st.video(output_path)
            st.success(f"Video with logo processed in {int(time.time() - start_time)}s")
