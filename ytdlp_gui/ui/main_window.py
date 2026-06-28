import customtkinter as ctk
from tkinter import filedialog
from core import config
from core.downloader import Downloader
from ui.widgets import FormatSelector, QualitySelector, ProgressSection


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("yt-dlp GUI")
        self.resizable(False, False)
        self._cfg = config.load()
        self._downloader = Downloader()
        self._downloading = False
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 6}

        # Theme toggle
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", **pad)
        ctk.CTkLabel(top, text="yt-dlp GUI", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkSwitch(top, text="다크모드", command=self._toggle_theme).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color="gray50").pack(fill="x", padx=16, pady=2)

        # URL row
        url_row = ctk.CTkFrame(self, fg_color="transparent")
        url_row.pack(fill="x", **pad)
        ctk.CTkLabel(url_row, text="URL", width=50).pack(side="left")
        self._url_entry = ctk.CTkEntry(url_row, width=340, placeholder_text="https://youtube.com/watch?v=...")
        self._url_entry.pack(side="left", padx=4)
        ctk.CTkButton(url_row, text="붙여넣기", width=70, command=self._paste_url).pack(side="left", padx=4)

        # Playlist checkbox (hidden by default)
        self._playlist_var = ctk.BooleanVar(value=True)
        self._playlist_check = ctk.CTkCheckBox(self, text="플레이리스트 전체 다운로드", variable=self._playlist_var)
        self._url_entry.bind("<FocusOut>", self._check_playlist)

        # Format selector
        self._format_sel = FormatSelector(self, on_change=self._on_format_change)
        self._format_sel.pack(fill="x", **pad)
        self._format_sel.set(self._cfg.get("format", "mp4"))

        # Quality selector
        self._quality_sel = QualitySelector(self)
        self._quality_sel.pack(fill="x", **pad)
        self._quality_sel.set(self._cfg.get("quality", "best"))
        if self._cfg.get("format") == "mp3":
            self._quality_sel.set_enabled(False)

        # Save folder row
        folder_row = ctk.CTkFrame(self, fg_color="transparent")
        folder_row.pack(fill="x", **pad)
        ctk.CTkLabel(folder_row, text="저장폴더", width=60).pack(side="left")
        self._folder_entry = ctk.CTkEntry(folder_row, width=300)
        self._folder_entry.insert(0, self._cfg.get("save_folder", ""))
        self._folder_entry.pack(side="left", padx=4)
        ctk.CTkButton(folder_row, text="찾아보기", width=70, command=self._browse_folder).pack(side="left", padx=4)

        ctk.CTkFrame(self, height=1, fg_color="gray50").pack(fill="x", padx=16, pady=4)

        # Download button
        self._dl_button = ctk.CTkButton(self, text="다운로드 시작", command=self._on_download_click)
        self._dl_button.pack(pady=8)

        # Progress section
        self._progress = ProgressSection(self)
        self._progress.pack(fill="x", **pad, pady=(0, 12))

    # ---- event handlers ----

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("light" if current == "Dark" else "dark")

    def _paste_url(self):
        try:
            text = self.clipboard_get()
            self._url_entry.delete(0, "end")
            self._url_entry.insert(0, text)
            self._check_playlist()
        except Exception:
            pass

    def _check_playlist(self, _event=None):
        url = self._url_entry.get().strip()
        if "playlist" in url or "list=" in url:
            self._playlist_check.pack(padx=16, pady=(0, 4))
        else:
            self._playlist_check.pack_forget()

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self._folder_entry.delete(0, "end")
            self._folder_entry.insert(0, folder)

    def _on_format_change(self, fmt: str):
        self._quality_sel.set_enabled(fmt != "mp3")

    def _on_download_click(self):
        if self._downloading:
            self._downloader.cancel()
            return

        url = self._url_entry.get().strip()
        if not url:
            self._progress.update(0, "URL을 입력하세요.")
            return

        fmt = self._format_sel.get()
        quality = self._quality_sel.get()
        save_folder = self._folder_entry.get().strip()

        self._downloading = True
        self._dl_button.configure(text="취소")
        self._progress.reset()

        self._downloader.download(
            url=url,
            fmt=fmt,
            quality=quality,
            save_folder=save_folder,
            on_progress=self._on_progress,
            on_status=self._on_status,
            on_complete=self._on_complete,
        )

        cfg = {"format": fmt, "quality": quality, "save_folder": save_folder}
        config.save(cfg)

    # ---- thread-safe callbacks (called from downloader thread) ----

    def _on_progress(self, value: float):
        self.after(0, lambda v=value: self._progress.set_progress(v))

    def _on_status(self, text: str):
        self.after(0, lambda t=text: self._progress.set_status(t))

    def _on_complete(self, success: bool, message: str):
        def _update():
            self._downloading = False
            self._dl_button.configure(text="다운로드 시작")
            self._progress.update(1.0 if success else 0.0, message)
        self.after(0, _update)
