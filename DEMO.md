# Recording the demo GIF (10-20 s)

Goal: a short clip of a shelf photo being uploaded and the counted boxes appearing. Used on the portfolio site and in a LinkedIn post.

## 1. Prepare (once)

1. Pick a clear, well-lit shelf photo with many repeated items (drinks, cans, boxed goods). Save it as `demo-shelf.jpg` on the Desktop. Check first that it detects well; a few test uploads are fine.
2. Start the backend (`cd backend`, activate the venv, `uvicorn app.main:app --port 8000`). Wait for "Application startup complete" so the first upload is not slow.
3. Start the frontend (`cd frontend && npm run dev`) and open http://localhost:5173.
4. Run `python create_sample_data.py` once so a store and product exist and the Timeline has data.
5. Do one throwaway upload to warm the model, then reload the page.
6. Browser window about 1280x720, zoom 100%, bookmarks bar hidden, notifications off.

## 2. Record

Tool: ScreenToGif (Windows, free) or Win+Shift+S is not enough; use ScreenToGif, or record with OBS and convert in step 3.

Script (about 15 s):

| Time | Action |
|------|--------|
| 0-2 s | Land on the Upload page. |
| 2-5 s | Choose the store and product, then pick `demo-shelf.jpg` so the preview shows. |
| 5-7 s | Click Analyze. |
| 7-12 s | Result appears: the count and confidence. Click the annotated-image toggle so the boxes show. Pause 2 s on the boxes. |
| 12-15 s | Click Timeline in the sidebar and let the chart load. Stop. |

Keep the cursor slow and deliberate; no scrolling.

## 3. Export

- ScreenToGif: Editor, trim to 10-20 s, Save as GIF, 12-15 fps, width 960 px. Aim for under 8 MB.
- If you recorded video with OBS:
  `ffmpeg -i demo.mp4 -vf "fps=12,scale=960:-1:flags=lanczos" -loop 0 stocksnap-demo.gif`
- For LinkedIn, upload the MP4 instead of the GIF (better quality, native playback).

## 4. Add to the repo

Save as `docs/stocksnap-demo.gif`, take a still of the annotated result as `docs/screenshot-upload.png`, then fill in the placeholders in the README with `![demo](docs/stocksnap-demo.gif)`.
