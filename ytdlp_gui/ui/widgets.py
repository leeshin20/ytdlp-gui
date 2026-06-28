import customtkinter as ctk
from core.downloader import QUALITIES


class FormatSelector(ctk.CTkFrame):
    FORMATS = ["mp4", "mp3", "webm"]

    def __init__(self, master, on_change, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_change = on_change
        self._var = ctk.StringVar(value="mp4")

        ctk.CTkLabel(self, text="포맷").pack(side="left", padx=(0, 8))
        for fmt in self.FORMATS:
            ctk.CTkRadioButton(
                self, text=fmt, variable=self._var, value=fmt,
                command=self._changed,
            ).pack(side="left", padx=4)

    def _changed(self):
        self._on_change(self._var.get())

    def get(self) -> str:
        return self._var.get()

    def set(self, value: str):
        self._var.set(value)


class QualitySelector(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text="화질").pack(side="left", padx=(0, 8))
        self._menu = ctk.CTkOptionMenu(self, values=QUALITIES, width=120)
        self._menu.pack(side="left")

    def get(self) -> str:
        return self._menu.get()

    def set(self, value: str):
        self._menu.set(value)

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self._menu.configure(state=state)


class ProgressSection(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._bar = ctk.CTkProgressBar(self, width=400)
        self._bar.set(0)
        self._bar.pack(fill="x", pady=(0, 4))
        self._label = ctk.CTkLabel(self, text="대기 중", anchor="w")
        self._label.pack(fill="x")

    def set_progress(self, value: float):
        self._bar.set(value)

    def set_status(self, text: str):
        self._label.configure(text=text)

    def update(self, progress: float, status: str):
        self._bar.set(progress)
        self._label.configure(text=status)

    def reset(self):
        self._bar.set(0)
        self._label.configure(text="대기 중")
