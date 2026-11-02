# Passive network probe — runtime integrated, live Flow schema unverified

`FlowNetworkProbe` observes existing page events only. It never intercepts a
request, calls a provider endpoint, clicks, downloads, retries, or writes a ledger.
It exports selected candidate IDs/state/progress fields and hashes, not raw bodies,
raw prompts, headers, cookies, query strings, fragments, or media URLs.

Attach before the current sender's one Generate click. Keep the existing account,
project, receipt validation, ledger claim and no-retry rules unchanged.

```python
probe = FlowNetworkProbe(
    page=service.page,
    request_id=rid,
    expected_prompt=payload['prompt'],
    check=service.assert_ready,
    context={k: payload[k] for k in ('room_id', 'scene_id', 'part', 'account_id')},
)
await probe.start()
try:
    # Existing final validation and durable pre-send bookkeeping remain here.
    await probe.mark_generate_attempt()
    await button.click(timeout=15000)  # The existing ONE click, never an extra one.
    probe.mark_click_returned()
    # Existing wait path runs here; the probe passively collects its traffic.
finally:
    evidence = await probe.stop()
    # Review/save this sanitized dictionary through a dedicated report path.
```

`http_request` is a LOCAL network-event label, not a Flow task ID. Response facts
stay attached to their observed browser Request object. Requests that began before
the click stay marked before-click even if their responses arrive afterward.

IDs and states remain candidates. Timing, an exact prompt match, HTTP 200, a failed
HTTP request, or a returned click alone do not confirm task attribution or outcome.
A live trace must establish the actual response schema, create-response identity,
status linkage and result identity before replacing the current observer.

Limits: 300 observed requests, 8 pending capture tasks, 10 minutes; parsed JSON
2 MiB, bounded tree depth/nodes/arrays/facts. Bodies are transiently read in memory.
When JSON Content-Length is absent, Playwright reads the whole body before the
size check: this is NOT a hard receive/RAM limit. Set
`allow_unannounced_json=False` to skip those bodies instead.

Known gaps: non-JSON/protobuf/WebSocket/service-worker-only traffic, task events
without accessible request.frame, bodies beyond limits, ID/state keys not yet in
the whitelist, and provider-specific media/result relationships. These are logged
or skipped, not guessed. No live Flow response has yet verified this draft.

## Draft refinements

- Each request/response has a Unix timestamp and signed `*_ms_from_generate`.
  Before-click traffic remains negative/marked pre-click, including late responses.
- Endpoint path keywords `generat`, `operation`, `media`, `video` prioritize parsing
  slots and output order. Other in-scope endpoints are still sampled, with a separate
  background-summary cap of one quarter of the overall request budget. This is not
  a whitelist proving which endpoint creates a task. Budget drops are reported.
- 4xx/5xx status and sanitized JSON facts are retained. HTTP failure is not proof of
  the generation's final outcome.
- After 15 seconds without a candidate response to a post-attempt request, record a
  warning and KEEP observing. A late candidate changes the wait label while keeping
  the warning in history. The warning does not stop/generate/retry or mark failure.
- A candidate response means only a keyword endpoint or selected JSON facts were
  seen. `association_confirmed` stays false. Endpoint labels use sanitized origin
  and path shape, never query strings or an unreviewed full raw path.

Chromium request/response fixtures and sender/Stop integration were tested. No live Flow capture yet. Selected facts have an additional 4 MiB export budget.
