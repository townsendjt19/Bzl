1. Log/activity panel doesn't support text selection or copy-paste (Textual widget limitation). Add a way to copy content out - either enable Textual's native text selection if the current Textual version supports it, or add a `copylast` command that copies the most recent AI response to the OS clipboard.

2. Change the input field cursor from a solid block to a thin line/underscore style - the block feels heavy.

3. Activity log timestamps currently show UTC (+00:00). Convert to local timezone for display (store UTC internally, format for display in local time).

4. The command input field has a length limit that's too short - I hit it trying to type a longer chat message and couldn't. Either remove the limit, raise it significantly, or switch to a multi-line input mode so longer prompts (like detailed bug reports) can be typed directly instead of needing a workaround.