---
paths:
  - "**/AndroidManifest.xml"
  - "**/*Activity.{kt,java}"
  - "**/src-tauri/gen/android/**"
  - "**/capacitor.config.{ts,json}"
  - "**/android/app/build.gradle*"
---

# Android device and window states: the baseline every Android app is accepted against

Written 2026-09-28 from RetortAndRove's first full state run on a Samsung Galaxy Tab S8+ (Android 16, One UI):
16 normal states + 3 DeX states, 5 defects, each reproduced and fixed
(the project's own test report, procedure and `device-states` instruments — internal to that
project, not shared).
The trigger is "an
Android shell file is in play", which `paths:` observes. Vendor facts below verified 2026-09-28.
review-when: a new Android major version (behaviour changes for large screens, edge-to-edge, configChanges); a new
One UI major version (multi-window entry points, DeX); the first phone (not tablet) or foldable in a project; a
project whose UI is native views rather than a WebView (the config-change clause then follows ViewModel/state
restoration, the state list stays).

## The property

**An Android app is not accepted on one window.** Any Android app build carries a state-matrix result: every state
and every transition in the list below, judged by invariants that hold at any size, with the device's state READ (not
inferred) before and after each step. A size is a recorded condition, never an acceptance value: split dividers and
pop-up windows are user-sized.

## The states (a phone skips the rows it cannot enter; record them as not applicable, not as passed)

| Group | States | What changes for the app |
|---|---|---|
| Posture | portrait full screen; landscape full screen | width/height swap; Android 16 ignores orientation and resizability locks on large screens (sw ≥ 600 dp) for apps targeting 36 |
| Split screen | either half; swapped; divider at the app's minimum and maximum; split while rotated (top/bottom halves) | width down to the 220 dp floor; **status-bar inset drops to 0 in a split half on Samsung** |
| Pop-up / freeform | default size; smallest (≈ 220 × 204 dp on the Tab S8+); largest; minimised to a bubble and back; pop-up → full screen | any size; inset 0 → 31 px on return to full screen with or without a width change |
| DeX / desktop windowing | window; maximised | `mWindowingMode=freeform` even when maximised, no status bar; apps open as pop-ups; no split screen |
| Lifecycle | background → foreground; process death in the background → reopen | reading/editing position must survive both |
| System settings (the user changes them, never the agent) | font size; bold text; display size (density); dark mode; navigation mode (gestures vs three buttons); taskbar shown; physical keyboard; RTL locale | each is a configuration change: undeclared ones RECREATE the activity |
| Multi-resume | the other app focused in split screen | the app stays visible but unfocused (`document.hasFocus()` false) |

## The invariants (the class; each project names its own widgets)

1. No horizontal page scroll; every fixed-position widget inside the window and clear of every other one.
2. Content that is the user's current place (reading spot, form field, selection) is the same after every transition
   — width, height AND inset changes, not width alone.
3. Overlays (dialogs, panels) cover the window; their controls stay on screen at the smallest window; the primary
   content of an overlay keeps a stated share of the height.
4. A prompt waiting for an answer is never under another widget (rectangle overlap, not a centre-point hit test) — also
   in the task where a hidden widget is shown again (an overlay closing), not one observer tick later, and focus
   never returns to a widget that is about to step aside.
5. Exactly one WebView/page after every step (a recreated activity can leave the old WebView alive).
6. No reload unless the step is a declared recreation.

Each invariant has a known-bad control that must make it FAIL once per session before a pass is trusted.

**A stored user preference that places a widget is a condition of the run, not a constant.** A draggable pill's stored
side and height decided which geometry the 2026-09-28 runs exercised: three Windows runs disagreed because an earlier
drag test had stored a new spot, and a width-limit control passed for the wrong reason at a spot outside the corner's
band. Every such preference is set explicitly per run (the default and each side at least), recorded with the
snapshot, and restored after.

## Reading the state

Window size, orientation, dpr from the page (CDP `innerWidth` / `screen.orientation.type`); insets from a probe element
padded with `env(safe-area-inset-*)`; DeX vs normal from `adb shell dumpsys activity activities` (`mWindowingMode`:
`fullscreen` normal, `freeform` DeX/pop-up) together with the top inset. **Check for DeX before a run**: a DeX session
silently turns every state into a pop-up. Never name a posture from a width.

## Configuration changes (WebView apps: Tauri, Capacitor, Cordova, plain WebView)

Declare every `android:configChanges` value (`orientation|keyboardHidden|keyboard|screenSize|locale|
smallestScreenSize|screenLayout|uiMode|fontScale|fontWeightAdjustment|density|layoutDirection|navigation|touchscreen|
colorMode|mcc|mnc|grammaticalGender`) so the activity is never recreated, AND re-apply the font scale yourself: the
Chromium WebView reads `Configuration.fontScale` only when it is constructed (`AwSettings`), so set
`webView.settings.textZoom = round(fontScale * 100)` in `onConfigurationChanged` (Tauri/wry: capture the WebView in
`onWebViewCreate`). Density changes reach an existing WebView through its display listener; bold text has no
WebView wiring either way — test it on the device. Sources:
https://developer.android.com/guide/topics/manifest/activity-element ,
https://developer.android.com/guide/topics/resources/runtime-changes ,
https://source.chromium.org/chromium/chromium/src/+/main:android_webview/java/src/org/chromium/android_webview/AwSettings.java

## Sizes a desktop build cannot reach

A desktop WebView with a minimum window size can still exercise small-window layout logic through a CDP viewport
override (`Emulation.setDeviceMetricsOverride`) held by one client while the probe runs from another. It cannot
reproduce insets, dpr and font rendering, recreation, or the window manager: a desktop pass is layout evidence only,
the device run stays the acceptance.
