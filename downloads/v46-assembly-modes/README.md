# SceneForge .79 — two assembly modes

Requires .78. Close app, apply updater, reopen Ghép video. Existing placement values retained: library = Tự ghép trong Dựng (selected clips go into editor library); assembled = Ghép & phát (local sequential playback of existing files). Mode selection and inclusion toggles update only assembly node and use autosave. Automatic mode has primary play and optional Chỉnh / xuất trong Dựng for existing assembled transfer.

Automatic playback reuses the caption/assembly player with native clip sound, selected voice/music/captions, ordering, tail holds and explicit gaps. It does not create new videos, spend credits, create an MP4 file or mutate the existing editor timeline. Full-screen and caption controls remain available. Missing parts labelled Phát nháp; zero local files disables play. Playback errors stay in assembly node. Manual transfer still uses the original guarded handoff, placement library; existing assembled transfer remains as explicit secondary action.

Preparing state guards repeated clicks. Mode switch, competing viewer request and room/pause invalidate stale opens; shared player request token ensures older async builds cannot pop over a newer choice. Closing player cleans media URLs as before. Shared audio JS updated in workflow/photos; photos assembly UI unchanged.

Validation: check_assembly_modes_ui.py real two-clip MP4 playback, automatic start, seek switches clip URL, inclusion toggles, no editor messages/mutation on play, delayed auto request cancelled by manual selection, actual editor-transfer payload library vs assembled, missing-file draft status, no generation POST, frame DOM identity. Existing workflow/photos caption viewer and real short-tail Veo regression passed. Not live Flow/model or Windows updater validation.

EXE: SceneForge-Update-20261109-v46.79-Assembly-Modes.exe
SHA256: 3ce749a57f50bf76671deadd218a027ec2a53526469d6f164fefe7a8295fe0e9
