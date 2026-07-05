from bzl.ui.widgets.compose_modal import ComposeModal

from .test_dashboard_pilot import _build_test_app


async def test_arrow_key_does_not_reset_discard_confirmation(tmp_path):
    app = _build_test_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.screen.query_one("#command-bar")
        bar.focus()
        await pilot.press("f2")
        await pilot.pause()
        assert len(app.screen_stack) == 3

        modal = app.screen
        assert isinstance(modal, ComposeModal)
        text_area = app.screen.query_one("#compose-text-area")
        text_area.text = "some draft text"
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()
        assert modal._confirming_discard is True, "first escape should arm the discard confirmation"
        assert len(app.screen_stack) == 3, "should not close on first escape when dirty"

        await pilot.press("left")
        await pilot.pause()
        assert modal._confirming_discard is True, (
            "cursor movement is not a text change, so it should not disarm the confirmation"
        )

        await pilot.press("escape")
        await pilot.pause()
        assert len(app.screen_stack) == 2, "second escape should confirm the discard and close"


async def test_ctrl_s_submits_instead_of_inserting_newline(tmp_path):
    app = _build_test_app(tmp_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        bar = app.screen.query_one("#command-bar")
        bar.focus()
        await pilot.press("f2")
        await pilot.pause()

        text_area = app.screen.query_one("#compose-text-area")
        text_area.text = "some draft text"
        await pilot.pause()

        await pilot.press("ctrl+s")
        await pilot.pause()

        assert len(app.screen_stack) == 2, "ctrl+s should submit and close the modal, not insert a newline"
