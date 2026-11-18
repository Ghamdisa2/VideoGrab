# Run on the target OS:  python build.py   -> dist/VideoGrab(.exe)
import PyInstaller.__main__ as p, os
sep = ";" if os.name == "nt" else ":"
p.run(["app.py", "--name", "VideoGrab", "--onefile", "--windowed", "--icon", "icon.ico",
       "--add-data", f"icon.ico{sep}.", "--add-data", f"icon.png{sep}.", "--collect-all", "customtkinter", "--collect-all", "yt_dlp",
       "--collect-all", "imageio_ffmpeg", "--collect-all", "curl_cffi", "--collect-all", "yt_dlp_ejs"])
