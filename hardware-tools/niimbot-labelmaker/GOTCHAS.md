# GOTCHAS - NIIMBOT D110 / D110_M from macOS

A record of every issue hit while building this tool and the fix for each, so we
never rediscover them. Format: Symptom / Cause / Fix.

## 0. The #1 lesson
Trust the `page` counter (did a label physically come out?), NOT `progress` (did
the printer process the data?). Almost every dead end was a sequence that returned
"success" while producing a blank label. A clean trace proves the bytes were
accepted, never that ink hit paper.

---

## 1. The printer is a `D110_M` and needs the `mv4` protocol (THE big one)
- Symptom: every command ACKs, status reaches `page=1, progress 100/100` (a perfect
  trace), but the label feeds out blank. The printer's own button self-test prints
  fine, so head/roll are good.
- Cause: the device advertises as `D110_M-XXXXXXXX`. NIIMBOT ships visually identical
  hardware with different firmware dialects. The standard D110 sequence is accepted
  by `_M` firmware but never engages the head as it expects.
- Fix: use the `mv4` sequence (niimblue `D110MV4PrintTask`), now the default.
  - `printStart` is 9 bytes (`pages, 0,0,0,0, color, speed, flag`), not 1 byte.
  - per page: a one-way `printStatus` ping, then `setPageSize` 13 bytes
    (`rows, cols, copies, cutHeight, cutType, 0, sendAll, partHeight`), and NO
    `printClear`, `pageStart`, or separate `setQuantity`.
  - A plain D110 (non-`_M`) uses `--variant std`.
- Tell: the `_M` in the BLE device name. Always log the connected device name.

## 2. Copies do not work via the copies field (loop sessions instead)
- Symptom: `"Cabbage" "Cabbage" "Cabbage"` prints 3, but `"Cabbage x3"` (or `--3`)
  prints only 1, and the status poll then false-stalls waiting for `page=3`.
- Cause: on the D110_M the copies field inside `setPageSize13b` is ignored; it prints
  one label and the page counter stops at 1.
- Fix: print N copies as N separate full `start_print..end_print` sessions
  (`print_image` loops). Always pass `quantity=1` to `print_page`.

## 3. Blank prints because of the bitmap "black pixel count" bytes
- Symptom: connects, processes, every label totally blank.
- Cause: each image-row packet (`0x85`) has 3 header bytes = count of black pixels in
  each third of the row. We copied the AndBondStyle/NiimPrintX shortcut of sending
  `0,0,0`. The firmware uses those counts to decide heat; `0,0,0` = burn nothing.
- Fix: compute real per-third counts (chunk = printheadPixels/8/3 = 4 bytes for a
  96-dot head). See `_encode_image_rows`.

## 4. A shared multi-page session prints NOTHING
- Symptom: restructured to one `start_print..end_print` for the whole batch and zero
  labels came out; the `page` counter went `1,3,5,7,9` (cumulative, never committing).
- Cause: on this hardware `end_print` is what commits the page to paper AND resets the
  page counter the completion check depends on.
- Fix: one full `start_print..end_print` session per label. Never share a session.

## 5. `printClear` (0x20) before each page (std variant only)
- AndBondStyle commented it out ("unsupported on B21"); niimblue's `D110PrintTask`
  sends it each page. Needed in `std`, not used in `mv4`.

## 6. "Successful" trace but page stuck at 0 -> printer STALLED
- Symptom: `progress` hits 100 but `page` never reaches the target; status polls loop.
- Cause: out of labels, cover not fully latched, or a jam. Data rasterized, nothing
  to feed onto.
- Fix: `print_page` bails after ~8s with a clear STALLED message. (Note: the target is
  `page>=1` per session now, not the copy count, or copies would false-stall.)

## 7. First 1-2 labels blank / "some designs don't print"
- Looked positional ("worked from Bokchoy on") then design-specific. Byte analysis
  showed every design encodes identically, so not a content bug. It was mostly the
  variant mismatch (#1) making `std` engage inconsistently. With `mv4` it is reliable.
- If a genuine first-feed warm-up remains: `--prime N` prints N throwaways first, or
  order the batch so a multi-copy item is first.

## 8. Solid-black labels come out blank
- A battery thermal head cannot sustain ~100% coverage; it browns out (still reports
  success). Not a bug. Do not use solid fills as a print test. Raise `--density` for
  darker output.

## 9. macOS blocks Bluetooth from automated/sandboxed processes
- Symptom: any BLE call from a non-Terminal process aborts instantly
  (`Abort trap: 6` / exit 134).
- Cause: macOS TCC ties Bluetooth permission to the owning app. Terminal.app has the
  grant + `NSBluetoothAlwaysUsageDescription`; a tool-spawned process does not.
  "Bluetooth enabled" only means the radio is on.
- Fix: run real prints in your own Terminal. For logic iteration with no hardware or
  labels, use `--dry-run` (in-process simulator that records the full byte stream to
  `debug.log`).

## 10. System Python too old
- Anaconda Python 3.8 cannot run modern `bleak`. Use the `labelmaker` conda env
  (Python 3.12) + `bleak` + `pillow`. No GUI/Homebrew C libs (we talk the protocol
  directly, not via NiimPrintX's GUI stack).

## 11. Quantity suffix printed as label text
- Symptom: `Cabbage 06/13 2 pcs` printed "2 pcs" as text.
- Cause: the parser only stripped `- N pcs` (with a hyphen).
- Fix: `parse_label_line` accepts `--N` (preferred), `xN`, and `N pcs`/`N pieces`
  (hyphen optional), and never mistakes a date like `06/13` for a count.

---

## Hardware facts
- D110/D110_M/D11/D101: 96-dot print head (12 mm), 203 DPI (8 dots/mm).
- Label preset used here: 40 x 12 mm -> image 320 x 96 (render landscape, rotate 90).
- BLE service `e7810a71-...`, data characteristic `bef8d6c9-...`
  (`read` + `write-without-response` + `notify`).

## Best reference
- niimblue / niimbluelib (MultiMote) is the source of truth: it has per-variant print
  tasks (`D110PrintTask`, `D110MV4PrintTask`). AndBondStyle/niimprint and
  labbots/NiimPrintX are useful but their generic path hides the `_M` differences.
