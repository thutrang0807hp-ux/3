# .125 product-grounded reference script drafts

Problem: a reference-video dialogue node did not have an explicit product-facts brief, so a rewrite could carry the sample product's claims into the user's product. The existing script composer had a separate product context but did not bind reference-video line IDs/timing to that context.

The workflow now embeds `scripts/ui/product_script.js`. The existing shell already passes `data.product`; the room bridge seeds a per-room brief both on initial open and reuse. Untouched briefs can track the selected product's name/description; edited briefs remain local. A changed selected product blocks writing until the user explicitly reloads that product's information. Reload preserves old brief history. The original photos/storyboard mode is not given this new panel.

The node/dialog offers product name, factual description, audience, price/offer, exclusions and a reference URL (labelled not crawled). The new action uses the configured `ai/script-library` route with `action: adapt_product`; existing source/store pinning, request ledger, read-only recovery and uncertain-result no-redispatch behavior are retained. No image/video generation or website crawling is introduced.

`product_script.py` validates bounded input and output. Product fields and reference transcript/scenes are separate JSON objects; instructions restrict the reference to rhetorical order/pacing, require claims to come from user facts/offer/name, forbid importing sample prices/claims/testimonials, and allow at most three missing-information questions. Output must have exactly the expected ordered line IDs, new_text and valid fact_ids; AI-supplied timings/originals or unsupported evidence keys are rejected. This is schema/provenance validation, not semantic proof of truth.

Requests freeze their body, source/store and a content signature before dispatch. Results are persisted for explicit review; source/facts/current newText or scene changes invalidate application. Original and translated speech and source timings stay immutable. Apply saves prior speech/selections, changes only newText, and clears chosen clips/dialogue overrides only for changed scenes, retaining clip versions. The review draft can be edited before applying. The old source-analysis action is labelled separately from the product rewrite.

Validation:
- `python scripts/analysis/check_product_script.py`: input bounds/required facts/URL credential rejection; strict ID/order/field/evidence schema; missing-information branch; actual FastAPI/ledger request/recovery without redispatch or store switching (fake AI).
- `python scripts/analysis/check_product_script_ui.py`: real workflow/IndexedDB Chromium; prefill/edit fields; outbound product/reference separation; review/manual edit/apply; original/timing/clip-version preservation; persistence; delayed-result invalidation; frozen recovery; changed-product guard; actual initial/reused shell bridge hydration.
- Existing `check_script_composer.py` and `check_frame_identity.py` passed, preserving script workbench and image-reference behavior.
- JS syntax and embedded EXE source checksums verified. Cumulative .62+ update includes prior .119–.124 fixes, new product_script.py and updated script_library.py/workflow.html. Live Gemini content quality and Windows installer untested.
