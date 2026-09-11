# Computer use — probe record and scripting-channel inventory (2026-09-07)

Extracted from `ops/environment.md` on 2026-09-08 when that file passed its 26K
cap (40-maintenance.md S3: extract the CONCRETE behind a pointer, never compress
a rule to fit). What stayed there is the rule, the conditions and the routing;
what is here is the evidence they rest on — the probe measurements, the raw
observations, and the app-by-app channel inventory.

Owner: `ops/environment.md` § *Computer use — desktop control*, which links here.
Raw tool responses and the refutability statement live in a dated write-up
under the source's outputs/ tree, which this repo does not ship.

review-when: the parent section's own review-when fires (a click-to-front or
`switch_display` probe runs; the app settings page gains an allow-list or
persistent-grant control; a hook is written for `mcp__computer-use__*`; KiCad,
Blender MCP, or a non-portable Blender is installed) — this file is re-measured
WITH it, or it becomes a record of a machine that no longer exists.

### PROBE 2026-09-07 (a local session, user-authorised: FreeCAD + 記事本)

The grant path WORKS in the Desktop Code tab. One dialog, whole set, both
granted `tier: "full"`, `denied: []`. Measured behaviour, in order of how much
it should change a plan:

1. **A screenshot HIDES every non-allowlisted window — it does not mask them.**
   The response named them: Radmin VPN, Samsung Notes, Everything, Brave, plus
   `textinputhost.exe`, `msedgewebview2.exe`, `nvidia overlay.exe`,
   `systemsettings.exe`. The desktop came back empty but for the taskbar. The
   `request_access` response advertises `screenshotFiltering: "mask"`; the
   observed effect is HIDE, and the settings page's "Unhide apps when Claude
   finishes" is the restore path. **So one screenshot rearranges the user's
   session.** This, not foreground theft, is the real collision with the
   "foreground is not commandeerable" premise — and unlike a Browser-pane
   screenshot it cannot be routed out-of-process.
2. **`open_application` DOES bring the app to the front** (corrected — the
   first probe said otherwise and was wrong). A COLD launch of 記事本 left the
   desktop shell frontmost, which read as "no foreground steal"; calling
   `open_application` again on the already-running app raised it over the
   user's windows. The cold-start case is a timing artifact, not a policy. So
   this surface **does** commandeer the foreground, and the error text of the
   click gate says so outright: "use `open_application` to bring it forward".
3. **A THIRD gate: the desktop shell.** A click while the desktop, taskbar,
   Start menu, Search or File Explorer is frontmost is refused with:
   *"call request_access with exactly \"File Explorer\" in the apps array —
   that single grant covers all of them. That grant is click-only: typing into
   the shell stays blocked."* This tier rule is not in the MCP server
   instructions; it is a shell-specific click-only grant on top of the
   documented browser=read / IDE=click tiers.
4. **Coordinate frame 1389x868 — resolved, and the Display premise is
   CONFIRMED, not contradicted.** Measured: single monitor, physical
   2560x1600 (AMD 610M), logical desktop bounds 1707x1067, i.e. exactly the
   150% scaling the Display section records. 1389x868 preserves 16:10
   (1.6002) and is a uniform ~1.229x downscale of the logical desktop.
   Computer use simply reports its OWN frame with every screenshot — use that
   number, never derive coordinates from the Display section. **Single monitor
   means the video's multi-monitor drift cannot occur here**; `switch_display`
   is untested for want of a second display.
5. **Portable-exe hypothesis CONFIRMED.** A `Blender.lnk` written to
   `%APPDATA%\Microsoft\Windows\Start Menu\Programs\` made the portable
   `blender.exe` immediately grantable (`tier: "full"`, resolved to the real
   `model3d-pipeline\...` path). **The installed-apps list is live, not cached at
   session start** — the shortcut was seconds old. This is the 30-second
   workaround to the 2026-08-21 bench-claude-arms limit: the limit is real,
   its practical bite is not.
6. **`bundleId` shapes differ by install kind**: a filesystem path for
   FreeCAD/Blender, an MSIX AUMID for Notepad
   (`Microsoft.WindowsNotepad_8wekyb3d8bbwe!App`).
7. Grant flags stay false unless requested in the SAME `request_access` call —
   adding one later costs a second dialog.

**Friction points from the other product — status after the probe.** Source: a
2026-09-06 YouTube walkthrough of ChatGPT/Codex GPT-6 Astra computer use
(analysis: a dated write-up in the user's private media-analysis notes).

| # | Claim | Status here |
|---|---|---|
| 1 | Foreground request hangs | no hang, but foreground IS taken — `open_application` raises the app over the user's windows |
| 2 | Multi-monitor drift | **cannot occur — single monitor** |
| 3 | Human locked out of input while agent drives | unprobed; the window-hiding of probe 1 is the nearer problem |
| 4 | Per-app dialog, conversation-scoped | CONFIRMED here, by construction |

That walkthrough is a FAILURE demo, not a capability demo: it ran out of
credits having produced nothing, and its author's own conclusion was to stop
using computer use. Its one architectural lesson is that GUI control was used
only to BOOTSTRAP (open apps, tick a checkbox) while the real work was routed
through Blender MCP — the same "script/protocol channel does the work"
conclusion `model3d-pipeline` reached independently.

### Scripting channels for candidate GUI targets (inventory 2026-09-07)

The routing question is never "can computer use drive app X" but "does X have a
channel that makes GUI driving unnecessary". Measured:

All three headless channels SMOKE-TESTED 2026-09-07, not merely found on disk:

| App | Present | Channel | Smoke test | GUI needed? |
|---|---|---|---|---|
| Blender 5.2.1 LTS | portable, `model3d-pipeline\tools\blender-5.2.1-windows-x64\blender.exe` | `-b --python-expr`, wired in `m3p/render_blender.py` (`BLENDER_EXE`) | **PASS** (`bpy` 5.2.1 LTS) | no |
| FreeCAD 1.1.3 | `FreeCAD\bin\FreeCADCmd.exe` | FreeCADCmd `-c`, wired (`FREECAD_CMD`) | **PASS** (1.1) | no |
| COMSOL 6.2 | `COMSOL62\Multiphysics\bin\win64\` | `comsolbatch.exe` (+ `comsolclusterbatch`) | **PASS** (help) | no |
| KiCad | **not installed** | would be `kicad-cli` | — | n/a |
| **Keysight ADS 2016.01** | **GONE** — was residue only (13 files / 47 MB, DLLs, zero executables); user deleted `ADS2016_01` 2026-09-07. `EEsof_License_Tools` REMAINS: 899 files / 308 MB (`bin` 211 MB, `jre` 88 MB, own uninstaller, `license.lic`); no EEsof/HPEESOF env vars | see below | n/a | n/a |

Supporting toolchain, smoke-tested same day: Python 3.12.7, Node 24.14.1,
git 2.51.0, ffmpeg 8.1, yt-dlp 2026.08.18, Docker 29.7.2, pdfTeX (TeX Live
2026). Ollama installed but **no running instance**. `klayout` is not on PATH
but lives in the model3d-pipeline venv (0.30.12) alongside gdsfactory 9.49.0,
build123d 0.11.1, trimesh 5.0.0, ezdxf 1.4.4, shapely 2.1.2, numpy 2.5.2.

**Keysight ADS — the version gate matters more than the install.** Even a
working ADS 2016.01 would have AEL only: the Process API for bidirectional
external-program communication arrived in **ADS 2022 Update 2**, and the
Python API / `run_python_ads2024beta()` in **ADS 2024** (Keysight docs, checked
2026-09-07). So automating ADS is not a computer-use question at all — it is a
licence-and-version question. The remaining `EEsof_License_Tools` half is
`app-residue-sweep`'s object and the user owns that cleanup; its own
uninstaller ships in the folder, and the licence-server service and registry
residue were NOT surveyed.

review-when: ADS is (re)installed — check the version against the 2022 U2 /
2024 API gates before assuming any scripting surface.

Full probe log, raw tool responses, the two conclusions this session
overturned, and the refutability statement live in a dated probe write-up
under the source's outputs/ tree, which this repo does not ship.

**Blender MCP is NOT installed on this machine** — no addon matching `*mcp*` in
the portable tree, no `blender-mcp` pip package; the user config dir
(`%APPDATA%\Blender Foundation\Blender\5.2`) holds only an empty extensions
cache. Configured MCP servers are `prism` (ConnectionRefused) and
`playwright-headless` only. So the video's actual working channel does not
exist here yet; adopting it is an unmade decision, not a gap to backfill.

review-when: a click-to-front or `switch_display` probe runs (settles friction
2-3 and the 1389x868 discrepancy); the app settings page gains an allow-list or
persistent-grant control; a hook is written for `mcp__computer-use__*`; KiCad,
Blender MCP, or a non-portable Blender is installed.
