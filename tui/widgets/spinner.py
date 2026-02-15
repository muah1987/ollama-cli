"""Qarin spinner widget -- thematic narrative arc thinking indicator.

Each spinner session picks a random theme and progresses through its
natural story arc, mapping to actual coding workflow phases:

    Setup → Analysis → Implementation → Testing → Refinement → Completion

One theme is chosen per ``start()`` call and the spinner advances through
that theme's frames sequentially, looping the middle frames if the task
takes longer than the story.
"""

from __future__ import annotations

import random

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label

# ---------------------------------------------------------------------------
# Narrative arc themes — each list maps to workflow phases:
#   [0] Analysis  [1] Planning  [2] Implementation  [3] Testing
#   [4] Refinement  [5] Completion
# ---------------------------------------------------------------------------

THEMES: dict[str, list[str]] = {
    # ☕ Arabic Coffee Ritual
    "coffee": [
        "☕ Grinding the beans... (محمصة)",
        "☕ Boiling the dallah... (يغلي)",
        "☕ Adding cardamom... (هيل)",
        "☕ First pour attempt... (صب أول)",
        "☕ Perfecting the foam... (رغوة)",
        "☕ Serving with dates... (تمر وقهوة)",
    ],
    # 🐪 Desert Caravan
    "caravan": [
        "🐪 Loading the camels... (يحمّل الجمل)",
        "🐪 Consulting desert maps... (ينظر النجوم)",
        "🐪 Following ancient routes... (يبحث عن الواحة)",
        "🐪 Resting under palms... (استراحة)",
        "🐪 Oasis spotted! (قريب من الهدف)",
        "🐪 Destination reached! (وصلنا)",
    ],
    # 📚 Islamic Scholarly Debate
    "scholarly": [
        "📚 Opening the kitab... (فتح الكتاب)",
        "📚 Examining the daleel... (فحص الدليل)",
        "📚 Weighing the madhahib... (موازنة المذاهب)",
        "📚 Consulting the shuyukh... (مشاورة)",
        "📚 Connecting the sources... (ربط المصادر)",
        "📚 Reaching ijma'! (إجماع!)",
    ],
    # 🎯 Sufi Maqamat (Spiritual Stations)
    "maqamat": [
        "🎯 Station of Yearning... (مقام الشوق)",
        "🎯 Station of Patience... (مقام الصبر)",
        "🎯 Station of Trust... (مقام التوكل)",
        "🎯 Station of Gratitude... (مقام الشكر)",
        "🎯 Station of Certainty... (مقام اليقين)",
        "🎯 Arrival! (وصول)",
    ],
    # 🍵 Shisha Cafe Debugging
    "shisha": [
        "🍵 Preparing the hookah... (تنظيف الشيشة)",
        "🍵 Packing apple tobacco... (تعبئة التبغ)",
        "🍵 Lighting coconut coals... (إشعال الفحم)",
        "🍵 First puff check... (أول نفخة)",
        "🍵 Smooth sailing... (تمام)",
        "🍵 زبطت! Perfect smoke 💨",
    ],
    # 🔍 Detective Investigation
    "detective": [
        "🔍 Examining the crime scene...",
        "🔍 Dusting for fingerprints...",
        "🔍 Following the clues...",
        "🔍 Interrogating witnesses...",
        "🔍 Connecting the dots...",
        "🔍 Case closed!",
    ],
    # 🏔️ Mountain Climbing
    "climbing": [
        "🏔️ Studying the mountain face...",
        "🏔️ Roping up the team...",
        "🏔️ Setting the pitons...",
        "🏔️ Testing handholds...",
        "🏔️ Finding the final route...",
        "🏔️ Summit reached! 🎉",
    ],
    # 👨‍🍳 Master Chef
    "chef": [
        "👨‍🍳 Reading the recipe...",
        "👨‍🍳 Prepping the mise en place...",
        "👨‍🍳 Mixing the ingredients...",
        "👨‍🍳 Taste testing the batter...",
        "👨‍🍳 Adding the finishing touches...",
        "👨‍🍳 Bon appétit! 🍽️",
    ],
}

# Flat list for backwards-compat (tests that import _LLAMA_SPINNER_FRAMES)
_LLAMA_SPINNER_FRAMES: list[str] = []
for _frames in THEMES.values():
    _LLAMA_SPINNER_FRAMES.extend(_frames)


def pick_theme() -> list[str]:
    """Pick a random narrative theme and return its frame list."""
    return random.choice(list(THEMES.values()))


class LlamaSpinner(Widget):
    """Animated themed spinner with narrative arc progression.

    Each ``start()`` call picks a new random theme.  The spinner advances
    through the theme's story sequentially; once all frames are shown it
    loops back through the middle frames (implementation → refinement)
    until ``stop()`` is called.
    """

    DEFAULT_CSS = """
    LlamaSpinner {
        height: 1;
        width: 100%;
        padding: 0 2;
        color: #a78bfa;
        text-style: italic;
    }
    """

    frame_index: reactive[int] = reactive(0)
    spinning: reactive[bool] = reactive(False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._active_frames: list[str] = pick_theme()

    def compose(self) -> ComposeResult:
        yield Label("", id="spinner-label")

    def start(self) -> None:
        """Start the spinner animation with a fresh random theme."""
        self._active_frames = pick_theme()
        self.spinning = True
        self.frame_index = 0
        self.display = True
        self._advance()
        self.set_interval(1.8, self._advance, name="spinner-timer")

    def stop(self) -> None:
        """Stop the spinner animation."""
        self.spinning = False
        self.display = False
        try:
            for timer in list(self._timers):
                if timer.name == "spinner-timer":
                    timer.stop()
        except Exception:
            pass

    def _advance(self) -> None:
        """Advance to the next frame in the active theme's narrative arc."""
        if not self.spinning:
            return
        try:
            label = self.query_one("#spinner-label", Label)
            frames = self._active_frames
            n = len(frames)
            if self.frame_index < n:
                # Sequential playthrough of the story
                label.update(frames[self.frame_index])
            else:
                # Loop the middle frames (indices 1..n-2) after first pass
                mid_start = 1
                mid_end = max(mid_start + 1, n - 1)
                mid_frames = frames[mid_start:mid_end]
                loop_idx = (self.frame_index - n) % len(mid_frames)
                label.update(mid_frames[loop_idx])
            self.frame_index += 1
        except Exception:
            pass
