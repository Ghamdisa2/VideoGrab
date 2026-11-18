package com.videograb.app

import android.Manifest
import android.content.ClipboardManager
import android.content.ContentValues
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup.LayoutParams.MATCH_PARENT
import android.view.ViewGroup.LayoutParams.WRAP_CONTENT
import android.webkit.MimeTypeMap
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.SwitchCompat
import com.yausername.ffmpeg.FFmpeg
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import kotlinx.coroutines.*
import java.io.File

class MainActivity : AppCompatActivity() {
    // palette
    private val BG = Color.parseColor("#0B0F1A")
    private val CARD = Color.parseColor("#141A2B")
    private val CARD2 = Color.parseColor("#1B2338")
    private val BORDER = Color.parseColor("#232C45")
    private val ACCENT = Color.parseColor("#7C3AED")
    private val CYAN = Color.parseColor("#06B6D4")
    private val MUTED = Color.parseColor("#94A3B8")
    private val OKC = Color.parseColor("#34D399")

    private lateinit var urlEdit: EditText
    private lateinit var videoPill: TextView
    private lateinit var audioPill: TextView
    private lateinit var chipsRow: LinearLayout
    private lateinit var playlistSwitch: SwitchCompat
    private lateinit var btn: Button
    private lateinit var bar: ProgressBar
    private lateinit var status: TextView
    private val chips = mutableListOf<TextView>()

    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var ready = false
    private var lang = "ar"
    private var audioMode = false
    private var qIdx = 0
    private val qualityHeights = listOf(0, 2160, 1080, 720, 480)
    private val processId = "vg_download"

    private fun tr(ar: String, en: String) = if (lang == "ar") ar else en
    private fun qualityLabels() = listOf(tr("أفضل جودة", "Best"), "4K", "1080p", "720p", "480p")
    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        lang = getSharedPreferences("vg", MODE_PRIVATE).getString("lang", null)
            ?: if (java.util.Locale.getDefault().language == "ar") "ar" else "en"
        window.statusBarColor = BG
        window.navigationBarColor = BG
        buildUi()
        handleIntent(intent)
        if (Build.VERSION.SDK_INT < 29 &&
            checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED
        ) requestPermissions(arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE), 1)
        initEngine()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIntent(intent)
    }

    private fun handleIntent(i: Intent?) {
        if (i?.action == Intent.ACTION_SEND) {
            val t = i.getStringExtra(Intent.EXTRA_TEXT) ?: return
            urlEdit.setText(Regex("https?://\\S+").find(t)?.value ?: t)
        }
    }

    private fun initEngine() {
        status.text = tr("جارٍ تجهيز المحرك...", "Preparing engine...")
        btn.isEnabled = false
        scope.launch {
            try {
                withContext(Dispatchers.IO) {
                    YoutubeDL.getInstance().init(applicationContext)
                    FFmpeg.getInstance().init(applicationContext)
                }
                ready = true
                status.text = tr("جاهز", "Ready")
                btn.isEnabled = true
                withContext(Dispatchers.IO) {
                    try { YoutubeDL.getInstance().updateYoutubeDL(applicationContext) } catch (_: Exception) {}
                }
            } catch (e: Exception) {
                status.text = tr("تعذّر تجهيز المحرك: ", "Engine error: ") + e.message
            }
        }
    }

    // ---------- UI helpers ----------
    private fun rounded(color: Int, radiusDp: Int, stroke: Int? = null) = GradientDrawable().apply {
        cornerRadius = dp(radiusDp).toFloat(); setColor(color)
        if (stroke != null) setStroke(dp(1), stroke)
    }

    private fun lp(w: Int, h: Int, top: Int = 0, start: Int = 0, end: Int = 0, bottom: Int = 0, weight: Float = 0f) =
        LinearLayout.LayoutParams(w, h, weight).apply {
            topMargin = dp(top); bottomMargin = dp(bottom); marginStart = dp(start); marginEnd = dp(end)
        }

    private fun label(text: String) = TextView(this).apply {
        this.text = text; textSize = 12f; setTextColor(MUTED); textAlignment = View.TEXT_ALIGNMENT_VIEW_START
    }

    private fun pill(text: String, bg: Int, fg: Int = Color.WHITE, size: Float = 13f) = TextView(this).apply {
        this.text = text; textSize = size; setTextColor(fg); gravity = Gravity.CENTER
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        setPadding(dp(14), dp(10), dp(14), dp(10)); background = rounded(bg, 12)
    }

    private fun card(root: LinearLayout, title: String? = null): LinearLayout {
        val c = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; setPadding(dp(16), dp(14), dp(16), dp(16))
            background = rounded(CARD, 16, BORDER)
        }
        if (title != null) c.addView(label(title), lp(MATCH_PARENT, WRAP_CONTENT, bottom = 8))
        root.addView(c, lp(MATCH_PARENT, WRAP_CONTENT, bottom = 12))
        return c
    }

    private fun styleSel(v: TextView, sel: Boolean) {
        v.background = rounded(if (sel) ACCENT else CARD2, 12)
        v.setTextColor(if (sel) Color.WHITE else MUTED)
    }

    private fun refreshMode() {
        styleSel(videoPill, !audioMode); styleSel(audioPill, audioMode)
        chipsRow.alpha = if (audioMode) 0.35f else 1f
    }

    private fun refreshChips() = chips.forEachIndexed { i, c -> styleSel(c, i == qIdx) }

    // ---------- UI ----------
    private fun buildUi() {
        chips.clear()
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(24), dp(16), dp(24))
            layoutDirection = if (lang == "ar") View.LAYOUT_DIRECTION_RTL else View.LAYOUT_DIRECTION_LTR
        }

        // header
        val header = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        header.addView(ImageView(this).apply { setImageResource(R.mipmap.ic_launcher) }, lp(dp(52), dp(52)))
        val titles = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        titles.addView(TextView(this).apply {
            text = "VideoGrab"; textSize = 24f; setTextColor(Color.WHITE); typeface = android.graphics.Typeface.DEFAULT_BOLD
        })
        titles.addView(TextView(this).apply {
            text = tr("حمّل الفيديو والصوت من أي منصة", "Download video & audio from any platform")
            textSize = 12f; setTextColor(MUTED)
        })
        header.addView(titles, lp(0, WRAP_CONTENT, start = 12, weight = 1f))
        header.addView(pill(tr("English", "العربية"), CARD2, Color.WHITE, 12f).apply {
            setOnClickListener { switchLang() }
        }, lp(WRAP_CONTENT, WRAP_CONTENT))
        root.addView(header, lp(MATCH_PARENT, WRAP_CONTENT, bottom = 18))

        // link card
        val c1 = card(root, tr("رابط الفيديو", "Video link"))
        urlEdit = EditText(this).apply {
            hint = "https://..."; setTextColor(Color.WHITE); setHintTextColor(MUTED); textSize = 14f
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI or InputType.TYPE_TEXT_FLAG_MULTI_LINE
            minLines = 2; maxLines = 4; gravity = Gravity.TOP or Gravity.START
            textDirection = View.TEXT_DIRECTION_LTR
            setPadding(dp(14), dp(12), dp(14), dp(12)); background = rounded(CARD2, 12, BORDER)
        }
        c1.addView(urlEdit, lp(MATCH_PARENT, WRAP_CONTENT))
        val r1 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        r1.addView(pill(tr("📋  لصق", "📋  Paste"), ACCENT, Color.WHITE, 13f).apply { setOnClickListener { pasteLink() } },
            lp(WRAP_CONTENT, WRAP_CONTENT, end = 8))
        r1.addView(pill(tr("مسح", "Clear"), CARD2, MUTED, 13f).apply { setOnClickListener { urlEdit.setText("") } },
            lp(WRAP_CONTENT, WRAP_CONTENT))
        c1.addView(r1, lp(WRAP_CONTENT, WRAP_CONTENT, top = 10))

        // options card
        val c2 = card(root, tr("الخيارات", "Options"))
        val modes = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        videoPill = pill(tr("🎬  فيديو", "🎬  Video"), CARD2).apply { setOnClickListener { audioMode = false; refreshMode() } }
        audioPill = pill(tr("🎵  صوت MP3", "🎵  Audio MP3"), CARD2).apply { setOnClickListener { audioMode = true; refreshMode() } }
        modes.addView(videoPill, lp(0, WRAP_CONTENT, end = 6, weight = 1f))
        modes.addView(audioPill, lp(0, WRAP_CONTENT, start = 6, weight = 1f))
        c2.addView(modes, lp(MATCH_PARENT, WRAP_CONTENT))

        c2.addView(label(tr("الجودة", "Quality")), lp(MATCH_PARENT, WRAP_CONTENT, top = 14, bottom = 6))
        chipsRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        qualityLabels().forEachIndexed { i, name ->
            val chip = pill(name, CARD2, MUTED, 12f).apply { setOnClickListener { qIdx = i; refreshChips() } }
            chips.add(chip)
            chipsRow.addView(chip, lp(WRAP_CONTENT, WRAP_CONTENT, end = 6))
        }
        c2.addView(HorizontalScrollView(this).apply { isHorizontalScrollBarEnabled = false; addView(chipsRow) },
            lp(MATCH_PARENT, WRAP_CONTENT))

        playlistSwitch = SwitchCompat(this).apply {
            text = tr("تحميل قائمة التشغيل كاملة", "Download entire playlist"); setTextColor(Color.WHITE); textSize = 14f
            val st = arrayOf(intArrayOf(android.R.attr.state_checked), intArrayOf())
            trackTintList = ColorStateList(st, intArrayOf(CYAN, BORDER))
            thumbTintList = ColorStateList(st, intArrayOf(Color.WHITE, MUTED))
        }
        c2.addView(playlistSwitch, lp(MATCH_PARENT, WRAP_CONTENT, top = 16))

        // download button
        btn = Button(this).apply {
            text = tr("⬇   ابدأ التحميل", "⬇   Start download"); textSize = 17f; setTextColor(Color.WHITE)
            isAllCaps = false; typeface = android.graphics.Typeface.DEFAULT_BOLD
            background = GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, intArrayOf(ACCENT, CYAN))
                .apply { cornerRadius = dp(16).toFloat() }
            setOnClickListener { startDownload() }
        }
        root.addView(btn, lp(MATCH_PARENT, dp(56), bottom = 12))

        // progress card
        val c3 = card(root)
        bar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            max = 100
            progressTintList = ColorStateList.valueOf(CYAN)
            progressBackgroundTintList = ColorStateList.valueOf(CARD2)
        }
        c3.addView(bar, lp(MATCH_PARENT, dp(10)))
        status = TextView(this).apply { setTextColor(MUTED); textSize = 13f; gravity = Gravity.CENTER }
        c3.addView(status, lp(MATCH_PARENT, WRAP_CONTENT, top = 10))

        refreshMode(); refreshChips()
        setContentView(ScrollView(this).apply { setBackgroundColor(BG); isFillViewport = true; addView(root) })
    }

    private fun pasteLink() {
        val cm = getSystemService(CLIPBOARD_SERVICE) as ClipboardManager
        val t = cm.primaryClip?.takeIf { it.itemCount > 0 }?.getItemAt(0)?.coerceToText(this)?.toString()?.trim()
        if (!t.isNullOrEmpty()) urlEdit.setText(Regex("https?://\\S+").find(t)?.value ?: t)
    }

    private fun switchLang() {
        val url = urlEdit.text.toString(); val pl = playlistSwitch.isChecked
        lang = if (lang == "ar") "en" else "ar"
        getSharedPreferences("vg", MODE_PRIVATE).edit().putString("lang", lang).apply()
        buildUi()
        urlEdit.setText(url); playlistSwitch.isChecked = pl
        btn.isEnabled = ready
        status.text = if (ready) tr("جاهز", "Ready") else tr("جارٍ تجهيز المحرك...", "Preparing engine...")
    }

    // ---------- download ----------
    private fun startDownload() {
        val url = urlEdit.text.toString().trim()
        if (url.isEmpty() || !ready) return
        val audio = audioMode
        val h = qualityHeights[qIdx]
        val playlist = playlistSwitch.isChecked
        btn.isEnabled = false; bar.progress = 0
        status.setTextColor(MUTED); status.text = tr("جارٍ التحميل...", "Downloading...")
        scope.launch {
            val tmp = File(getExternalFilesDir(null), "tmp").apply { deleteRecursively(); mkdirs() }
            try {
                withContext(Dispatchers.IO) {
                    val req = YoutubeDLRequest(url)
                    if (playlist) {
                        req.addOption("--yes-playlist"); req.addOption("--ignore-errors")
                        req.addOption("-o", tmp.absolutePath + "/%(playlist_title).60s/%(playlist_index)03d - %(title).80s.%(ext)s")
                    } else {
                        req.addOption("--no-playlist")
                        req.addOption("-o", tmp.absolutePath + "/%(title).80s.%(ext)s")
                    }
                    if (audio) {
                        req.addOption("-x"); req.addOption("--audio-format", "mp3"); req.addOption("--audio-quality", "0")
                    } else {
                        val f = if (h == 0) "bv*+ba/b" else "bv*[height<=$h]+ba/b[height<=$h]/b"
                        req.addOption("-f", f); req.addOption("--merge-output-format", "mp4")
                    }
                    var item = ""
                    val itemRe = Regex("Downloading item (\\d+) of (\\d+)")
                    YoutubeDL.getInstance().execute(req, processId) { p, eta, line ->
                        itemRe.find(line)?.let { item = tr("العنصر ", "Item ") + "${it.groupValues[1]}/${it.groupValues[2]}  " }
                        runOnUiThread { bar.progress = p.toInt(); status.text = item + "${p.toInt()}%  -  " + tr("متبقي ${eta}ث", "${eta}s left") }
                    }
                    tmp.walkTopDown().filter { it.isFile && !it.name.endsWith(".part") && !it.name.endsWith(".ytdl") }
                        .forEach { saveToDownloads(it, tmp) }
                }
                bar.progress = 100
                status.setTextColor(OKC)
                status.text = tr("تم الحفظ في مجلد Download/VideoGrab ✔", "Saved to Download/VideoGrab ✔")
            } catch (e: Exception) {
                status.setTextColor(Color.parseColor("#F87171"))
                status.text = tr("فشل: ", "Failed: ") + e.message?.take(150)
            } finally {
                tmp.deleteRecursively(); btn.isEnabled = true
            }
        }
    }

    private fun saveToDownloads(f: File, root: File) {
        val sub = f.parentFile?.relativeTo(root)?.path.orEmpty()
        val rel = if (sub.isEmpty()) "VideoGrab" else "VideoGrab/$sub"
        val mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(f.extension) ?: "application/octet-stream"
        if (Build.VERSION.SDK_INT >= 29) {
            val v = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, f.name)
                put(MediaStore.Downloads.MIME_TYPE, mime)
                put(MediaStore.Downloads.RELATIVE_PATH, "Download/$rel")
            }
            val uri = contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v) ?: return
            contentResolver.openOutputStream(uri)?.use { out -> f.inputStream().use { it.copyTo(out) } }
        } else {
            val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), rel).apply { mkdirs() }
            f.copyTo(File(dir, f.name), overwrite = true)
            sendBroadcast(Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE).setData(android.net.Uri.fromFile(File(dir, f.name))))
        }
    }

    override fun onDestroy() { super.onDestroy(); scope.cancel() }
}
