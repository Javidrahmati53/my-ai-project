# Koh-i-Noor: Mountain of Light — 3D film

A procedural Blender project for a 30-second, vertical, silent cinematic short. It creates five connected 3D scenes and renders an H.264 MP4 locally or in GitHub Actions.

## Scenes
1. Diamond emerging from darkness (0–6s)
2. Mughal imperial treasury (6–12s)
3. Nader Shah's 1739 Delhi campaign — presented as a historical reconstruction; the naming story is explicitly legendary (12–18s)
4. Koh-i-Noor in the Queen Mother's Crown (1937 crown-inspired reconstruction; verify against licensed references) (18–24s)
5. Diamond legacy end card (24–30s)

## Requirements
- Blender 4.2+ (includes Python API)
- FFmpeg available on PATH
- 8 GB+ RAM recommended; GPU rendering optional

## Render
```bash
blender -b -t 8 --python kohinoor_film.py
```
The script renders 5 scene segments to `renders/`, then FFmpeg joins them into `kohinoor_30s.mp4`.

For a quick test, edit `QUALITY = "PREVIEW"` near the top of the script. For final output use `QUALITY = "FINAL"`.

## Notes on historical accuracy
The early provenance of the Koh-i-Noor is uncertain. The story that Nader Shah coined the name in 1739 is a legend, not a securely documented fact. The British acquisition followed the 1849 Treaty of Lahore after the annexation of Punjab. The crown scene is a stylized reconstruction, not a claim of exact gem dimensions or setting. Use museum/licensed reference photography for a historically exact crown model.

No voice, music, or sound is generated. Narration and subtitles are intentionally delivered separately.
