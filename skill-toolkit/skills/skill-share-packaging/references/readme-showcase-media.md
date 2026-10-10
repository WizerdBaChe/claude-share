# README showcase media — classes and reuse recipe

Read when a share repo's README gets motion/picture samples of what the shared thing makes
(first used 2026-10-06, `motion-video-skill`). The point of this file: the next showcase
picks a CLASS and copies a MEASURED recipe instead of guessing sizes.

## Classes

| Class | Shape | Status | Measured recipe |
|---|---|---|---|
| `inline-large` (near full width) | landscape 16:9, markdown image `![alt](assets/x.gif)` with NO width attribute | USED 2026-10-06 | below |
| `inline-partial` (a cropped region, a UI detail, side-by-side pair) | landscape or square crop | NOT MADE | fill from first real use |
| `inline-vertical` (9:16 phone film) | portrait | NOT MADE | fill from first real use |
| `linked-full` (full-length film) | mp4 as a release asset / Pages, README holds only a still + link | NOT MADE | fill from first real use |

A class marked NOT MADE has no numbers on purpose: when one is first built, record its
width, fps, duration, colours and bytes here in the same change. Do not extrapolate from
`inline-large`; vertical sources exist in the lab (720x1280) but no vertical GIF was ever
rendered, so its size budget is unmeasured.

## `inline-large` — what was actually produced

Source films 1280x720, 30 fps, silent after `-an`. Three clips of 5.0 s each:

| Clip | GIF size | fps | frames | bytes |
|---|---|---|---|---|
| hype ad | 640x360 | 15 | 75 | 1,020,788 |
| explainer | 640x360 | 15 | 75 | 299,986 |
| data showreel | 560x315 | 12 | 60 | 1,570,270 |

The showreel was cut to 560 px / 12 fps / 96 colours only because 640 px / 15 fps / 128
colours came to 2.6 MB (dense tile pattern defeats GIF palettes). Rule of thumb that held:
target at most ~1.6 MB per clip; shrink width and fps before colours. Total README media
was 2.9 MB for three clips.

Recipe (two-pass palette, `-an` = no audio; change `-ss`, the input and the output):

```
ffmpeg -ss <start> -t 5 -i <film.mp4> -an -vf "fps=15,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" <out.gif>
```

Showreel variant: `fps=12,scale=560:-1`, `max_colors=96`, `bayer_scale=5`.

## Not measured (do not state as fact)

- GitHub's rendered README column width and how it scales an image wider than the column.
  A web search on 2026-10-06 found no GitHub documentation with the number; only that
  GitHub allows `<img width=...>` in READMEs. The three GIFs were NOT checked on the
  rendered GitHub page by the author of this note; the user passed them.
- Whether a GIF beats an uploaded mp4 (`user-attachments`) for the same clip on GitHub.

## Picking the clip (decisions that held)

- One class per film type: hype ad, data showreel, explainer. Pick the 5 s where something
  visibly forms (logo assembling, a hook line landing, an icon being struck out).
- Silent; no music (user ruling 2026-10-06).
- Only films whose picture is original content. Imitation arms of a source film are not
  shown, even when their own content is original, unless the user rules otherwise for
  that clip (user cleared one explainer made in a source film's form, 2026-10-06).
- A product shown in a clip must be one the user is willing to have public; ask before
  pushing (a "-private" repo name was the trigger on 2026-10-06).

## review-when

The first time `inline-partial`, `inline-vertical` or `linked-full` is built (fill its row);
GitHub documents its README column width; a showcase is rendered on GitHub and a size looks
wrong (then replace the 640/560 numbers with measured ones).
