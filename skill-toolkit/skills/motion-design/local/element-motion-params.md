# Element motion parameters measured on source films

Written 2026-09-30 from a private motion lab's cards T02 (spring) and T03 (colour
swap); raw measurements and instruments stay in that lab and are not shipped. Whole-film
work (sections, transitions, camera, export) belongs to a separate whole-film skill this
share does not ship; this file holds only what one element does.

## Springs (T02) — measured on C05; verified by a repeat round

Numbers are what the VIEWER sees in screen space (element x any camera scale combined).
Do not set an element to these values and then stack a separate camera spring on top: the
composite gets slower (r1 measured omega 13.1 against the source's 17.8 that way). With the
screen-space note, repeat runs read omega 17.9 and 18.2; without the card, 13.6-20.4.

```
container morph : zeta 0.85, omega 18 rad/s   (settle ~0.25 s, overshoot ~0.6%)
big expand      : zeta 0.67, omega 18         (one visible bounce, ~6%)
indicator edges : leading omega 24, trailing omega 14, both zeta 0.85 -> ~1.35x stretch mid-move
retarget        : x(t) = x_start + sum_i (target_i - target_{i-1}) * (1 - g(t - t_i))  (sum of step responses)
```

`g` is the unit spring step response (closed form; the lab's fitting tool is not
shipped). In a frame-rendered film compute it from `t` every frame; never simulate with
a timer.

## Black/white container swap (T03) — measured on C05; user ruling: keep as the source does

1. Swap colour together with the morph, interpolated; the swap passes through grey for
   ~0.07-0.17 s each time. This is correct, not a bug to fix.
2. Keep any single grey spell <= ~0.17 s (the source's longest), or it reads as a stuck
   grey block.
3. Run the grey during the morph so motion blur covers the in-between.

Imitation runs without this card already fell in the source's range; the card exists so
a reviewer does not "fix" the grey.

## Beat-timed element motion

Peak velocity on the beat, start ~30-40 ms early (a film-rhythm rule, owned by the
whole-film skill this share does not ship).
