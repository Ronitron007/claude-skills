#!/bin/bash
# Make a copy of an explainer video small enough for SendUserFile to reach the phone (limit 30 MiB).
# Usage: phone_copy.sh <input.mp4> <output.mp4>
# 480p, 15 fps, two-pass H.264 at about 62 kbps, AAC mono at 32 kbps: about 28 MiB for 40 minutes of slides.
# For a longer video, lower the video bitrate: 30 MiB * 8 / seconds - 32 kbps of audio.
set -e
in="$1"
out="$2"
# one pass log per run: parallel runs in one folder must not share it
log="$(mktemp -d)/x264pass"
ffmpeg -v error -y -i "$in" -vf scale=854:480,fps=15 -c:v libx264 -preset slow -b:v 62k -pass 1 -passlogfile "$log" -an -f mp4 /dev/null
ffmpeg -v error -y -i "$in" -vf scale=854:480,fps=15 -c:v libx264 -preset slow -b:v 62k -pass 2 -passlogfile "$log" -c:a aac -b:a 32k -ac 1 "$out"
ls -la "$out"
