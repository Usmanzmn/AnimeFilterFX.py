# ========== FEATURE 3 (Sequential Playback: Raw + Styled + Watermark) ==========
st.markdown("---")
st.header("🕒 Play 3 Videos Sequentially with Freeze & Watermark")

# Initialize session state
if "seq_raw_output" not in st.session_state:
    st.session_state["seq_raw_output"] = None
if "seq_final_output" not in st.session_state:
    st.session_state["seq_final_output"] = None

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
            with tempfile.TemporaryDirectory() as tmpdir:
                paths = []
                for i, f in enumerate(uploaded_seq):
                    p = os.path.join(tmpdir, f"seq{i}.mp4")
                    with open(p, "wb") as out:
                        out.write(f.read())
                    paths.append(p)

                transform = get_transform_function(style_seq)
                width = int(1280 / 3)  # ~426
                height = 720
                video_raw = [VideoFileClip(p).resize((width, height)) for p in paths]
                video_styled = [VideoFileClip(p).fl_image(transform).resize((width, height)) for p in paths]

                raw_clips = []
                styled_clips = []

                intro_duration = 1  # 1-second freeze

                # Intro freeze frame
                for video_set, target_list in [(video_raw, raw_clips), (video_styled, styled_clips)]:
                    freeze_frames = []
                    for j in range(3):
                        freeze = video_set[j].to_ImageClip(t=0).set_duration(intro_duration).set_position((j * width, 0))
                        freeze_frames.append(freeze)
                    intro_clip = CompositeVideoClip(freeze_frames, size=(1280, height)).set_duration(intro_duration)
                    target_list.append(intro_clip)

                # Sequential play
                for i in range(3):
                    dur = video_raw[i].duration

                    # Raw
                    raw_parts = []
                    for j in range(3):
                        if j == i:
                            clip = video_raw[j].set_position((j * width, 0))
                        else:
                            still = video_raw[j].to_ImageClip(t=1).set_duration(dur).set_position((j * width, 0)).set_opacity(0.4)
                            clip = still
                        raw_parts.append(clip)
                    raw_composite = CompositeVideoClip(raw_parts, size=(1280, height)).set_duration(dur)
                    raw_clips.append(raw_composite)

                    # Styled
                    styled_parts = []
                    for j in range(3):
                        if j == i:
                            clip = video_styled[j].set_position((j * width, 0))
                        else:
                            still = video_styled[j].to_ImageClip(t=1).set_duration(dur).set_position((j * width, 0)).set_opacity(0.4)
                            clip = still
                        styled_parts.append(clip)
                    styled_composite = CompositeVideoClip(styled_parts, size=(1280, height)).set_duration(dur)
                    styled_clips.append(styled_composite)

                # Final videos
                raw_sequence = concatenate_videoclips(raw_clips)
                styled_sequence = concatenate_videoclips(styled_clips)

                # Save raw
                raw_output_path = os.path.join(tmpdir, "seq_raw.mp4")
                raw_sequence.write_videofile(raw_output_path, codec="libx264", audio_codec="aac")

                # Save styled with watermark
                styled_temp_path = os.path.join(tmpdir, "seq_styled_temp.mp4")
                styled_sequence.write_videofile(styled_temp_path, codec="libx264", audio_codec="aac")
                final_output_path = os.path.join(tmpdir, "seq_final.mp4")
                apply_watermark(styled_temp_path, final_output_path)

                # Save to session
                with open(raw_output_path, "rb") as f:
                    st.session_state["seq_raw_output"] = f.read()
                with open(final_output_path, "rb") as f:
                    st.session_state["seq_final_output"] = f.read()

        st.success("✅ Sequential videos generated with intro freeze and styled output!")

# Display
if st.session_state["seq_raw_output"]:
    st.subheader("🎬 Raw Sequential Video (No Style, No Watermark)")
    st.video(st.session_state["seq_raw_output"])
    st.download_button("⬇️ Download Raw", st.session_state["seq_raw_output"], file_name="sequential_raw.mp4")

if st.session_state["seq_final_output"]:
    st.subheader("🌟 Final Sequential Video (Styled + Watermark)")
    st.video(st.session_state["seq_final_output"])
    st.download_button("⬇️ Download Final", st.session_state["seq_final_output"], file_name="sequential_styled.mp4")
