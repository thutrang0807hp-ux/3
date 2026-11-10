# SceneForge .110 — Local wheel zoom

Disables native WebView2 user zoom controls and initializes ZoomFactor at 1. All five page documents cancel Ctrl/Meta wheel browser default without stopping propagation, so embedded iframe canvases still receive gestures. Timeline Ctrl/Meta wheel updates existing 20–160 pixels/second zoom, anchors time under pointer and coalesces rendering with requestAnimationFrame. Workflow canvas accepts modified wheel even over node controls; ordinary control scrolling remains unchanged. Photo canvas supports Meta and anchors local zoom to pointer.

Validation: real Chromium documents verified modified wheel changes only local timeline/canvas values, browser default is canceled, and ordinary body wheel remains uncanceled. Native Framework host compiled successfully. Windows GUI not run; static test server lacks backend routes by design.
