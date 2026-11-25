---
name: stream-clip-studio
description: Set up a reusable Windows creator profile, import gameplay recordings, select and render vertical clips with a post-style layout, and schedule approved batches in the native TikTok Studio. Use for gameplay clips, initial creator setup, or verified TikTok scheduling.
---

# Stream Clip Studio

Run the commands from this skill directory. Read [README.md](README.md) for syntax and requirements.
The runner checks GitHub for updates at startup. If it prints an update notice, relay it to the user. Use `run.ps1 check-update` for a manual check and keep local profiles and media when replacing the skill files.

## Initial setup

Ask for the posting profile's display name, profile picture, @handle, and one Windows folder for originals and output clips. Ask for these four together. Run `setup.ps1 onboard` with the provided values or let the user answer the interactive prompts. The setup stores the profile outside this folder, then opens a dedicated Chromium window for manual TikTok login. Never ask for or store a password. Use the saved profile for later clips. If login or a security challenge needs intervention, let the user complete it in the browser. Setup does not upload or schedule anything.

## Import and cut

- Process a recording only after the user asks. Use `run.ps1 import` with a local video or a direct recording URL. It keeps the original at the root of the chosen media folder. Each original gets one subfolder named after its filename without extension for final MP4s.
- Run `analyze` with the requested duration range. Use the Gaming Clip candidates, timestamped transcript and frames to choose openings with action, surprise, euphoria or humor. Avoid idle stretches and overlapping picks. Use the requested clip count, duration and publish timing.
- Find the webcam during ingest. Inspect the crop before using it. Pass its source pixel rectangle to `render`; omit it if absent. Use a compact profile/title header and full-width gameplay from y=300 to the bottom of the 1080 × 1920 canvas (84% of its height). Place the webcam as a small 270 × 220 inset at the upper left of the gameplay, focusing on face/headphones/shoulders; it must not create a separate band or reduce the gameplay area. Credit the streamer's correct @ over the lower left of the game. If the streamer handle is unknown and needed for the credit, ask.
- Keep the avatar, header text, captions and streamer credit inside mobile safe margins. Use a discreet 46 px watermark at 15% opacity in the upper gameplay area. Keep the title readable in at most two lines. Use `--badge 'GTA 6'` for GTA clips; omit the optional badge for other games. Avoid large panels, a white footer or duplicated titles.
- Before a first batch or a layout change, run `render` with `--preview` to produce a real-frame PNG for the user's evaluation. This preview does not render or upload a video. Preserve the source image geometry; adjust `--focus-x` when zooming would cut off the important subject. A generated visual mockup is a reference only, not evidence of the exact game framing. Apply a reviewed layout to future renders; do not replace already scheduled posts unless requested.
- Use an engaging, grounded Portuguese title that doubles as the posting caption. Pick a moment within the clip for its first-frame cover and write a Portuguese cover hook of 2–5 words. The renderer builds the cover from the real frame, embeds it only as frame 0 and delivers an MP4. The profile's @ is the center watermark at 15% opacity.
- When dialogue has Portuguese and English, inspect the source and give the renderer only reliable Portuguese word timings via `--words`. Each word uses relative seconds and `language: pt`. English dialogue gets no burned-in caption. Check the first two frames, a captioned frame, and final resolution/duration/audio before delivery.

## Schedule

- Only schedule the exact files requested. Point the plan YAML at the relevant clips subfolder and preview the chosen video, fully dated schedule, timezone, caption, hashtags and privacy. Ask for a single approval of the batch; then run the approved plan hash. Keep a single window during the batch, and stop when it finishes.
- Never click immediate publishing instead of scheduling. The optional `confirm_pending_check` is for an explicitly approved Studio content-check dialog only, and it rereads schedule controls first. Keep it off unless approved for that batch. Let the user handle CAPTCHA/MFA.
- One safe recovery may replace a failed tab within the same Chromium window. After submission, repeat only read-only verification; reconcile ambiguous results and never resubmit them automatically. Report verified posts with links. Close the dedicated Chromium when the batch ends; do not reopen it after completion.
- Keep all login profiles, local settings, logs, databases, photos, video files, and generated plans outside this repository.
