# SceneForge .78 — bounded codec-tail approval and precise reasons

Requires .77. Close app, apply updater, reopen same project and explicitly approve existing clips. Do not regenerate videos just to address this check.

Screenshot: 7/7 clips received, all show 7.9s; approval throws generic image/prompt/time mismatch. Source receipt accepts 7.5–8.5s but approval and assembly eligibility allowed only 25ms shortfall. Reproduced independently with actual 7.917s H264 MP4. Screenshot alone does not establish duration is the only mismatch in every user clip; new errors expose scene/part plus exact frame/prompt/slot/time reason.

clipTimingInfo retains old full-duration check; adds at most 150ms tolerance ONLY for 8s-required Flow clips with flow requestId, valid captured tail data URL, real numeric duration and zero source offset. Other providers, missing tails/IDs, source offsets, larger deficits remain blocked. Actual clip.duration/file untouched. Explicit approval records codec-tail-hold seconds; existing handoff passes real sourceDuration plus tail, and native editor already creates a short static final-image item for the remaining timeline interval. Trimmed shorter slots need no extra hold. No new Flow request/transcode/credit. No auto-approval on receipt. Clip tile explains any held tail after approval. Frame, prompt, slot and continuity remain required; slot mismatch now explicitly checked in manual accept as in eligibility.

Validation: check_veo_redesign_ui.py --short-tail generates actual ~7.917s MP4, imports and explicitly accepts, preserves source duration and tail adjustment. Rejects changed frame/prompt/slot, 7.7s, missing tail, non-Flow source and nonzero sourceIn; tests 7.849/7.85 boundary, missing requestId and nonnumeric duration. Standard 8s regression also run. Assembly refresh/no duplicate, room guards, no editor overwrite retained. Native hold implementation inspected in baseline source (real source video item plus image for positive gap); no new editor code or timing metadata fabrication. Not live Flow or Windows updater validation. Payload only workflow.html.

EXE: SceneForge-Update-20261108-v46.78-Veo-Clip-Timing.exe
SHA256: d08ac6131b15edba6fc89cc8c135180b5162de96debf291b5b95d0d98c18b220
