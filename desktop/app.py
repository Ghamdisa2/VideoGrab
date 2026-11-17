import os, sys, threading, queue
from tkinter import filedialog
import customtkinter as ctk
import yt_dlp
import imageio_ffmpeg

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

T = {
    "ar": {
        "title": "VideoGrab - محمّل الفيديو والصوت",
        "hint": "الصق الروابط (رابط في كل سطر) - تيك توك، انستقرام، يوتيوب، اكس، فيسبوك، تيليجرام وغيرها",
        "modes": ["فيديو", "صوت MP3"],
        "qualities": ["أفضل جودة", "4K (2160p)", "1440p", "1080p", "720p", "480p"],
        "cookies": "كوكيز من:", "none": "بدون",
        "playlist": "تحميل قائمة التشغيل كاملة",
        "folder": "تغيير المجلد", "dl": "⬇  تحميل", "busy": "جارٍ التحميل...",
        "ready": "جاهز", "processing": "جارٍ المعالجة...", "item": "العنصر",
        "fail": "✘ فشل: ", "done": "اكتمل: {ok}/{n} - الملفات في {d}", "lang": "English",
    },
    "en": {
        "title": "VideoGrab - Video & Audio Downloader",
        "hint": "Paste links (one per line) - TikTok, Instagram, YouTube, X, Facebook, Telegram and more",
        "modes": ["Video", "Audio MP3"],
        "qualities": ["Best quality", "4K (2160p)", "1440p", "1080p", "720p", "480p"],
        "cookies": "Cookies from:", "none": "None",
        "playlist": "Download entire playlist",
        "folder": "Change folder", "dl": "⬇  Download", "busy": "Downloading...",
        "ready": "Ready", "processing": "Processing...", "item": "Item",
        "fail": "✘ Failed: ", "done": "Done: {ok}/{n} - files in {d}", "lang": "العربية",
    },
}
HEIGHTS = [None, 2160, 1440, 1080, 720, 480]
BROWSERS = [None, "chrome", "firefox", "edge", "brave"]


def res_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.lang = "ar"
        self.geometry("740x700")
        self.minsize(660, 620)
        try:
            self.iconbitmap(res_path("icon.ico"))
        except Exception:
            pass
        self.q = queue.Queue()
        self.out_dir = os.path.join(os.path.expanduser("~"), "Downloads", "VideoGrab")
        self.busy = False
        # state kept across language switches
        self.s_urls, self.s_mode, self.s_q, self.s_b, self.s_pl = "", 0, 0, 0, False
        self._build()
        self.after(100, self._poll)

    def t(self, k):
        return T[self.lang][k]

    def _save_state(self):
        self.s_urls = self.urls.get("1.0", "end").strip()
        self.s_mode = self.t("modes").index(self.mode.get())
        self.s_q = self.t("qualities").index(self.quality.get())
        bl = [self.t("none")] + BROWSERS[1:]
        self.s_b = bl.index(self.browser.get())
        self.s_pl = bool(self.playlist.get())

    def _toggle_lang(self):
        self._save_state()
        self.lang = "en" if self.lang == "ar" else "ar"
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        self.title(self.t("title"))
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=(14, 0))
        ctk.CTkButton(top, text=self.t("lang"), width=90, command=self._toggle_lang).pack(side="right")
        ctk.CTkLabel(self, text="VideoGrab", font=("Segoe UI", 28, "bold")).pack()
        ctk.CTkLabel(self, text=self.t("hint"), text_color="gray70").pack(pady=(0, 8))
        self.urls = ctk.CTkTextbox(self, height=110)
        self.urls.pack(fill="x", padx=20)
        self.urls.insert("1.0", self.s_urls)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(12, 4))
        self.mode = ctk.CTkSegmentedButton(row, values=self.t("modes"))
        self.mode.set(self.t("modes")[self.s_mode])
        self.mode.pack(side="left")
        self.quality = ctk.CTkOptionMenu(row, values=self.t("qualities"), width=130)
        self.quality.set(self.t("qualities")[self.s_q])
        self.quality.pack(side="left", padx=10)
        ctk.CTkLabel(row, text=self.t("cookies")).pack(side="left", padx=(10, 4))
        self.browser = ctk.CTkOptionMenu(row, values=[self.t("none")] + BROWSERS[1:], width=100)
        self.browser.set(([self.t("none")] + BROWSERS[1:])[self.s_b])
        self.browser.pack(side="left")

        self.playlist = ctk.CTkCheckBox(self, text=self.t("playlist"))
        if self.s_pl:
            self.playlist.select()
        self.playlist.pack(anchor="w", padx=22, pady=8)

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=20)
        self.dir_lbl = ctk.CTkLabel(row2, text=self.out_dir, anchor="w")
        self.dir_lbl.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row2, text=self.t("folder"), width=110, command=self._choose_dir).pack(side="right")

        self.btn = ctk.CTkButton(self, text=self.t("dl"), height=46, font=("Segoe UI", 18, "bold"), command=self._start)
        self.btn.pack(fill="x", padx=20, pady=14)
        self.bar = ctk.CTkProgressBar(self)
        self.bar.set(0)
        self.bar.pack(fill="x", padx=20)
        self.status = ctk.CTkLabel(self, text=self.t("ready"), text_color="gray70")
        self.status.pack(pady=4)
        self.log = ctk.CTkTextbox(self, height=150, state="disabled")
        self.log.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        if self.busy:
            self.btn.configure(state="disabled", text=self.t("busy"))

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.out_dir)
        if d:
            self.out_dir = d
            self.dir_lbl.configure(text=d)

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _poll(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "log":
                    self._log(val)
                elif kind == "progress":
                    self.bar.set(val[0])
                    self.status.configure(text=val[1])
                elif kind == "done":
                    self.busy = False
                    self.btn.configure(state="normal", text=self.t("dl"))
                    self.status.configure(text=val)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _start(self):
        links = [l.strip() for l in self.urls.get("1.0", "end").splitlines() if l.strip()]
        if not links or self.busy:
            return
        self._save_state()
        self.busy = True
        self.btn.configure(state="disabled", text=self.t("busy"))
        self.bar.set(0)
        threading.Thread(target=self._run, args=(links, self._opts()), daemon=True).start()

    def _opts(self):
        os.makedirs(self.out_dir, exist_ok=True)
        pl = bool(self.s_pl)
        name = "%(title).80s [%(id)s].%(ext)s"
        tmpl = f"%(playlist_title).60s/%(playlist_index)03d - {name}" if pl else name
        o = {
            "outtmpl": {"default": os.path.join(self.out_dir, tmpl)},
            "noplaylist": not pl,
            "ignoreerrors": "only_download" if pl else False,
            "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
            "progress_hooks": [self._hook],
            "quiet": True, "no_warnings": True,
            "windowsfilenames": True, "retries": 5,
        }
        if self.s_b:
            o["cookiesfrombrowser"] = (BROWSERS[self.s_b],)
        if self.s_mode == 1:
            o["format"] = "bestaudio/best"
            o["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}]
        else:
            h = HEIGHTS[self.s_q]
            o["format"] = f"bv*[height<={h}]+ba/b[height<={h}]/b" if h else "bv*+ba/b"
            o["merge_output_format"] = "mp4"
        return o

    def _hook(self, d):
        info = d.get("info_dict") or {}
        idx, n = info.get("playlist_index"), info.get("n_entries")
        prefix = f"{self.t('item')} {idx}/{n}  " if idx and n else ""
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            frac = (d.get("downloaded_bytes", 0) / total) if total else 0
            speed = d.get("speed")
            txt = prefix + f"{frac*100:.0f}%" + (f"  -  {speed/1e6:.1f} MB/s" if speed else "")
            self.q.put(("progress", (frac, txt)))
        elif d["status"] == "finished":
            self.q.put(("progress", (1, prefix + self.t("processing"))))

    def _run(self, links, opts):
        ok = 0
        for i, link in enumerate(links, 1):
            self.q.put(("log", f"[{i}/{len(links)}] {link}"))
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(link, download=True)
                    if info:
                        cnt = len(info.get("entries") or []) if info.get("_type") == "playlist" else 0
                        extra = f" ({cnt})" if cnt else ""
                        self.q.put(("log", f"✔ {info.get('title', '')}{extra}"))
                        ok += 1
            except Exception as e:
                self.q.put(("log", self.t("fail") + str(e)[:200]))
        self.q.put(("done", self.t("done").format(ok=ok, n=len(links), d=self.out_dir)))


if __name__ == "__main__":
    App().mainloop()
