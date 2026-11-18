import os, sys, threading, queue
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image
import yt_dlp
import imageio_ffmpeg

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---- palette ----
BG, CARD, CARD2, BORDER = "#0B0F1A", "#141A2B", "#1B2338", "#232C45"
ACCENT, ACCENT_H, CYAN = "#7C3AED", "#6D28D9", "#06B6D4"
TEXT, MUTED, OK, ERR = "#E5E7EB", "#94A3B8", "#34D399", "#F87171"
FONT = "Segoe UI" if sys.platform == "win32" else "Helvetica"

T = {
    "ar": {
        "title": "VideoGrab - محمّل الفيديو والصوت",
        "sub": "حمّل الفيديو والصوت من أي منصة بجودة عالية",
        "link": "رابط الفيديو",
        "hint": "الصق الرابط هنا - يمكنك لصق عدة روابط (رابط في كل سطر)",
        "modes": ["🎬  فيديو", "🎵  صوت MP3"],
        "qualities": ["أفضل جودة", "4K (2160p)", "1440p", "1080p", "720p", "480p"],
        "opts": "الخيارات", "quality": "الجودة", "cookies": "كوكيز من المتصفح", "none": "بدون",
        "playlist": "تحميل قائمة التشغيل كاملة",
        "folder": "مجلد الحفظ", "change": "تغيير", "dl": "⬇   ابدأ التحميل", "busy": "جارٍ التحميل...",
        "ready": "جاهز", "processing": "جارٍ المعالجة...", "item": "العنصر",
        "fail": "✘ فشل: ", "done": "اكتمل: {ok}/{n} - الملفات في {d}", "lang": "English",
        "paste": "📋  لصق", "clear": "مسح", "log": "السجل",
        "m": ["قص", "نسخ", "لصق", "تحديد الكل"], "anchor": "e",
    },
    "en": {
        "title": "VideoGrab - Video & Audio Downloader",
        "sub": "Download video and audio from any platform in high quality",
        "link": "Video link",
        "hint": "Paste the link here - you can paste several links (one per line)",
        "modes": ["🎬  Video", "🎵  Audio MP3"],
        "qualities": ["Best quality", "4K (2160p)", "1440p", "1080p", "720p", "480p"],
        "opts": "Options", "quality": "Quality", "cookies": "Cookies from browser", "none": "None",
        "playlist": "Download entire playlist",
        "folder": "Save folder", "change": "Change", "dl": "⬇   Start download", "busy": "Downloading...",
        "ready": "Ready", "processing": "Processing...", "item": "Item",
        "fail": "✘ Failed: ", "done": "Done: {ok}/{n} - files in {d}", "lang": "العربية",
        "paste": "📋  Paste", "clear": "Clear", "log": "Log",
        "m": ["Cut", "Copy", "Paste", "Select all"], "anchor": "w",
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
        self.configure(fg_color=BG)
        self.geometry("820x900")
        self.minsize(720, 820)
        try:
            self.iconbitmap(res_path("icon.ico"))
        except Exception:
            pass
        try:
            self.logo = ctk.CTkImage(Image.open(res_path("icon.png")), size=(56, 56))
        except Exception:
            self.logo = None
        self.q = queue.Queue()
        self.out_dir = os.path.join(os.path.expanduser("~"), "Downloads", "VideoGrab")
        self.busy = False
        self.s_urls, self.s_mode, self.s_q, self.s_b, self.s_pl = "", 0, 0, 0, False
        self._build()
        self.after(100, self._poll)

    def t(self, k):
        return T[self.lang][k]

    # ---------- state / language ----------
    def _save_state(self):
        self.s_urls = self.urls.get("1.0", "end").strip()
        self.s_mode = self.t("modes").index(self.mode.get())
        self.s_q = self.t("qualities").index(self.quality.get())
        self.s_b = ([self.t("none")] + BROWSERS[1:]).index(self.browser.get())
        self.s_pl = bool(self.playlist.get())

    def _toggle_lang(self):
        self._save_state()
        self.lang = "en" if self.lang == "ar" else "ar"
        for w in self.winfo_children():
            w.destroy()
        self._build()

    # ---------- UI ----------
    def _card(self, parent, title=None):
        c = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=16, border_width=1, border_color=BORDER)
        c.pack(fill="x", padx=24, pady=(0, 12))
        if title:
            ctk.CTkLabel(c, text=title, font=(FONT, 13, "bold"), text_color=MUTED,
                         anchor=self.t("anchor")).pack(fill="x", padx=18, pady=(14, 6))
        return c

    def _build(self):
        a = self.t("anchor")
        self.title(self.t("title"))

        # header
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(20, 14))
        ctk.CTkButton(head, text=self.t("lang"), width=92, height=32, corner_radius=16,
                      fg_color=CARD2, hover_color=BORDER, text_color=TEXT,
                      font=(FONT, 12, "bold"), command=self._toggle_lang).pack(side="right", anchor="n")
        if self.logo:
            ctk.CTkLabel(head, text="", image=self.logo).pack(side="left")
        tb = ctk.CTkFrame(head, fg_color="transparent")
        tb.pack(side="left", padx=14)
        ctk.CTkLabel(tb, text="VideoGrab", font=(FONT, 30, "bold"), text_color="white", anchor="w").pack(anchor="w")
        ctk.CTkLabel(tb, text=self.t("sub"), font=(FONT, 12), text_color=MUTED, anchor="w").pack(anchor="w")

        # link card
        c1 = self._card(self, self.t("link"))
        self.urls = ctk.CTkTextbox(c1, height=84, fg_color=CARD2, border_width=1, border_color=BORDER,
                                   corner_radius=12, text_color=TEXT, font=(FONT, 13), wrap="word")
        self.urls.pack(fill="x", padx=18)
        self.urls.insert("1.0", self.s_urls)
        self._edit_bindings()
        r = ctk.CTkFrame(c1, fg_color="transparent")
        r.pack(fill="x", padx=18, pady=(8, 14))
        ctk.CTkLabel(r, text=self.t("hint"), font=(FONT, 11), text_color=MUTED).pack(side="left")
        ctk.CTkButton(r, text=self.t("clear"), width=64, height=30, corner_radius=10, fg_color=CARD2,
                      hover_color=BORDER, text_color=MUTED, command=self._clear).pack(side="right")
        ctk.CTkButton(r, text=self.t("paste"), width=96, height=30, corner_radius=10, fg_color=ACCENT,
                      hover_color=ACCENT_H, font=(FONT, 12, "bold"), command=self._paste).pack(side="right", padx=8)

        # options card
        c2 = self._card(self, self.t("opts"))
        g = ctk.CTkFrame(c2, fg_color="transparent")
        g.pack(fill="x", padx=18, pady=(0, 14))
        g.grid_columnconfigure((0, 1), weight=1, uniform="o")
        self.mode = ctk.CTkSegmentedButton(g, values=self.t("modes"), height=38, corner_radius=12,
                                           selected_color=ACCENT, selected_hover_color=ACCENT_H,
                                           unselected_color=CARD2, unselected_hover_color=BORDER,
                                           font=(FONT, 13, "bold"))
        self.mode.set(self.t("modes")[self.s_mode])
        self.mode.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        def field(col, label, widget_factory):
            f = ctk.CTkFrame(g, fg_color="transparent")
            f.grid(row=1, column=col, sticky="ew", padx=(0 if col == 0 else 8, 8 if col == 0 else 0))
            ctk.CTkLabel(f, text=label, font=(FONT, 11), text_color=MUTED, anchor=a).pack(fill="x")
            w = widget_factory(f)
            w.pack(fill="x", pady=(4, 0))
            return w

        menu_kw = dict(height=36, corner_radius=10, fg_color=CARD2, button_color=BORDER,
                       button_hover_color=ACCENT, dropdown_fg_color=CARD2, text_color=TEXT, font=(FONT, 12))
        self.quality = field(0, self.t("quality"), lambda p: ctk.CTkOptionMenu(p, values=self.t("qualities"), **menu_kw))
        self.quality.set(self.t("qualities")[self.s_q])
        names = [self.t("none")] + BROWSERS[1:]
        self.browser = field(1, self.t("cookies"), lambda p: ctk.CTkOptionMenu(p, values=names, **menu_kw))
        self.browser.set(names[self.s_b])

        self.playlist = ctk.CTkSwitch(g, text=self.t("playlist"), progress_color=CYAN, button_color="white",
                                      fg_color=BORDER, font=(FONT, 12), text_color=TEXT)
        self.playlist.grid(row=2, column=0, columnspan=2, sticky="w", pady=(14, 0))
        if self.s_pl:
            self.playlist.select()

        # folder card
        c3 = self._card(self, self.t("folder"))
        f = ctk.CTkFrame(c3, fg_color="transparent")
        f.pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkButton(f, text=self.t("change"), width=90, height=34, corner_radius=10, fg_color=CARD2,
                      hover_color=BORDER, text_color=TEXT, command=self._choose_dir).pack(side="right")
        self.dir_lbl = ctk.CTkLabel(f, text="📁  " + self.out_dir, anchor="w", font=(FONT, 12), text_color=TEXT)
        self.dir_lbl.pack(side="left", fill="x", expand=True)

        # download button
        self.btn = ctk.CTkButton(self, text=self.t("dl"), height=54, corner_radius=16, fg_color=ACCENT,
                                 hover_color=ACCENT_H, font=(FONT, 18, "bold"), command=self._start)
        self.btn.pack(fill="x", padx=24, pady=(4, 12))

        # progress + log card
        c4 = self._card(self)
        self.bar = ctk.CTkProgressBar(c4, height=10, corner_radius=5, fg_color=CARD2, progress_color=CYAN)
        self.bar.set(0)
        self.bar.pack(fill="x", padx=18, pady=(16, 6))
        self.status = ctk.CTkLabel(c4, text=self.t("ready"), font=(FONT, 12), text_color=MUTED)
        self.status.pack(pady=(0, 6))
        self.log = ctk.CTkTextbox(c4, height=110, fg_color=CARD2, corner_radius=12, text_color=MUTED,
                                  font=(FONT, 11), state="disabled")
        self.log.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        c4.pack_configure(fill="both", expand=True, pady=(0, 20))
        self.log.tag_config("ok", foreground=OK)
        self.log.tag_config("err", foreground=ERR)
        if self.busy:
            self.btn.configure(state="disabled", text=self.t("busy"))

    # ---------- clipboard / editing ----------
    def _paste(self):
        try:
            txt = self.clipboard_get().strip()
        except Exception:
            return
        if not txt:
            return
        sep = "\n" if self.urls.get("1.0", "end").strip() else ""
        self.urls.insert("end", sep + txt)
        self.urls.see("end")

    def _clear(self):
        self.urls.delete("1.0", "end")

    def _edit_bindings(self):
        """Ctrl+C/V/X/A that work with ANY keyboard layout (e.g. Arabic) + right-click menu."""
        inner = self.urls._textbox

        def on_ctrl(e):
            if sys.platform != "win32":
                return None
            k = e.keycode
            if k == 86:
                self._paste()
            elif k == 67:
                inner.event_generate("<<Copy>>")
            elif k == 88:
                inner.event_generate("<<Cut>>")
            elif k == 65:
                inner.tag_add("sel", "1.0", "end-1c")
            else:
                return None
            return "break"

        inner.bind("<Control-KeyPress>", on_ctrl)
        m = self.t("m")
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=m[0], command=lambda: inner.event_generate("<<Cut>>"))
        menu.add_command(label=m[1], command=lambda: inner.event_generate("<<Copy>>"))
        menu.add_command(label=m[2], command=self._paste)
        menu.add_command(label=m[3], command=lambda: inner.tag_add("sel", "1.0", "end-1c"))
        inner.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.out_dir)
        if d:
            self.out_dir = d
            self.dir_lbl.configure(text="📁  " + d)

    # ---------- log / queue ----------
    def _log(self, msg):
        tag = "ok" if msg.startswith("✔") else "err" if msg.startswith("✘") else None
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n", tag) if tag else self.log.insert("end", msg + "\n")
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
                    self.status.configure(text=val[1], text_color=TEXT)
                elif kind == "done":
                    self.busy = False
                    self.btn.configure(state="normal", text=self.t("dl"))
                    self.status.configure(text=val, text_color=OK)
        except queue.Empty:
            pass
        self.after(100, self._poll)

    # ---------- download logic ----------
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
                        self.q.put(("log", f"✔ {info.get('title', '')}" + (f" ({cnt})" if cnt else "")))
                        ok += 1
            except Exception as e:
                self.q.put(("log", self.t("fail") + str(e)[:200]))
        self.q.put(("done", self.t("done").format(ok=ok, n=len(links), d=self.out_dir)))


if __name__ == "__main__":
    App().mainloop()
