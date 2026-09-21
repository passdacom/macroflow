# Integrated execution and editor boundaries

## Runtime ownership

`SequenceRunSession` freezes the flow and loads/deep-copies referenced macro documents before its worker starts. Whole-flow repetition is session-only: one cycle by default, finite count, or explicitly confirmed until-stop. Completion callbacks do not release ownership; both the flow worker and its owned player must exit. `request_stop()` closes the start gate synchronously and reaps asynchronously. UI generations discard stale callbacks and retain controls until exit.

`FlowClock` measures active time for flow fixed waits, color polling and cycle gaps. Input pause stays owned by the existing player: an open gesture completes its release before requested pause becomes actual pause. Stop wakes pause waits. Main-window runtime actions route to the active session across tabs.

## Partial execution

Editor selection resolves contiguous display rows to complete raw gestures, including hidden moves within the range. Incomplete gestures and ambiguous nested raw input are rejected, not widened to the document. Every editor partial route uses the same boundary checks and cancelable three-second preparation. The target must be an external foreground window on Windows; cancellation or document generation change prevents playback.

Sequencer context-menu partial execution uses actual visible rows, including inline and wait steps. `selected_flow()` constructs an independent linear graph with success/error terminals, preserving only internal implicit gaps for macro-only sequences. Partial execution is always one cycle, independent of whole-flow repeat controls. A confirmation describes the exact row range and reminds the operator to prepare application state. It cannot recreate omitted preconditions. No separate start/end spinboxes are added; contiguous selection is the range control.

## Editing and merge safety

Merge cleanup is per placement, never inferred from source labels. Only still-held keys receive synthetic key-up at that placement's final timestamp; original events and timing remain intact. Repeated IDs are remapped. Open mouse buttons, orphan releases and branch-dependent nested input are rejected with a flow alternative rather than guessed cleanup.

Copy/paste uses a same-document in-memory buffer, not the OS clipboard. Complete fragments preserve event fields and relative timing, obtain fresh IDs and use the existing neutral gesture insertion boundary. The transaction uses one existing Undo/Redo snapshot and leaves raw recording events untouched. Loading a document clears the buffer. Existing authored Ctrl+C/V actions remain distinct.

## Verification boundary

Linux tests use real Qt in subprocesses and simulated native adapters. They do not validate actual Windows focus, hooks, input injection, desktop timing or release binaries. Independent review and Windows/package gates remain required before user delivery.
