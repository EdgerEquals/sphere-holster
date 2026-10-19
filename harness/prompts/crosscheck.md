CROSS-CHECK MODE. You are given the OTHER reviewer's latest verdict JSON for the same change.
- For each of its findings: agree, disagree (with reason), or cannot verify.
- Look for what it missed, and for anything it asserted without a source.
- Your own "verdict" is about the change itself after considering both reviews.
- Add a field "crosscheck": [{"other_finding": "...", "position": "agree|disagree|cannot_verify", "reason": "..."}] to your JSON.
