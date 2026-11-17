package com.videograb.app

import android.Manifest
import android.content.ContentValues
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.view.Gravity
import android.view.View
import android.view.ViewGroup.LayoutParams.MATCH_PARENT
import android.view.ViewGroup.LayoutParams.WRAP_CONTENT
import android.webkit.MimeTypeMap
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.yausername.youtubedl_android.YoutubeDL
import com.yausername.youtubedl_android.YoutubeDLRequest
import com.yausername.ffmpeg.FFmpeg
import kotlinx.coroutines.*
import java.io.File

class MainActivity : AppCompatActivity() {
    private lateinit var urlEdit: EditText
    private lateinit var audioRadio: RadioButton
    private lateinit var qualitySpinner: Spinner
    private lateinit var btn: Button
    private lateinit var bar: ProgressBar
    private lateinit var status: TextView
    private lateinit var playlistCheck: CheckBox
    private lateinit var langBtn: Button
    private var lang = "ar"
    private fun tr(ar: String, en: String) = if (lang == "ar") ar else en
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var ready = false
    private val qualityHeights = listOf(0, 2160, 1080, 720, 480)
    private fun qualityLabels() = listOf(tr("أفضل جودة", "Best quality"), "4K", "1080p", "720p", "480p")
    private val processId = "vg_download"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        lang = getSharedPreferences("vg", MODE_PRIVATE).getString("lang", null)
            ?: if (java.util.Locale.getDefault().language == "ar") "ar" else "en"
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
            val link = Regex("https?://\\S+").find(t)?.value ?: t
            urlEdit.setText(link)
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
                // keep yt-dlp fresh (sites change often)
                withContext(Dispatchers.IO) {
                    try { YoutubeDL.getInstance().updateYoutubeDL(applicationContext) } catch (_: Exception) {}
                }
            } catch (e: Exception) {
                status.text = tr("تعذّر تجهيز المحرك: ", "Engine error: ") + e.message
            }
        }
    }

    private fun buildUi() {
        val dp = resources.displayMetrics.density
        fun px(v: Int) = (v * dp).toInt()
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(px(20), px(40), px(20), px(20))
            setBackgroundColor(Color.parseColor("#0F1220"))
        }
        TextView(this).apply {
            text = "VideoGrab"; textSize = 30f; setTextColor(Color.WHITE)
            gravity = Gravity.CENTER; typeface = android.graphics.Typeface.DEFAULT_BOLD
            root.addView(this)
        }
        TextView(this).apply {
            text = tr("الصق رابط الفيديو أو شاركه مباشرة من أي تطبيق", "Paste a link or share it directly from any app")
            setTextColor(Color.parseColor("#9CA3AF")); gravity = Gravity.CENTER
            setPadding(0, px(4), 0, px(20)); root.addView(this)
        }
        urlEdit = EditText(this).apply {
            hint = "https://..."; setTextColor(Color.WHITE); setHintTextColor(Color.GRAY)
            setPadding(px(14), px(12), px(14), px(12)); textDirection = View.TEXT_DIRECTION_LTR
            background = GradientDrawable().apply { cornerRadius = px(12).toFloat(); setColor(Color.parseColor("#1B2033")) }
            root.addView(this, LinearLayout.LayoutParams(MATCH_PARENT, WRAP_CONTENT))
        }
        val group = RadioGroup(this).apply { orientation = RadioGroup.HORIZONTAL; setPadding(0, px(14), 0, 0) }
        val videoRadio = RadioButton(this).apply { text = tr("فيديو", "Video"); setTextColor(Color.WHITE); isChecked = true; id = View.generateViewId() }
        audioRadio = RadioButton(this).apply { text = tr("صوت MP3", "Audio MP3"); setTextColor(Color.WHITE); id = View.generateViewId() }
        group.addView(videoRadio); group.addView(audioRadio); root.addView(group)
        qualitySpinner = Spinner(this).apply {
            adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item, qualityLabels())
            root.addView(this, LinearLayout.LayoutParams(MATCH_PARENT, WRAP_CONTENT))
        }
        playlistCheck = CheckBox(this).apply {
            text = tr("تحميل قائمة التشغيل كاملة", "Download entire playlist"); setTextColor(Color.WHITE)
            root.addView(this, LinearLayout.LayoutParams(MATCH_PARENT, WRAP_CONTENT).apply { topMargin = px(8) })
        }
        btn = Button(this).apply {
            text = tr("⬇  تحميل", "⬇  Download"); textSize = 18f; setTextColor(Color.WHITE)
            background = GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,
                intArrayOf(Color.parseColor("#7C3AED"), Color.parseColor("#06B6D4"))).apply { cornerRadius = px(14).toFloat() }
            setOnClickListener { startDownload() }
            root.addView(this, LinearLayout.LayoutParams(MATCH_PARENT, px(54)).apply { topMargin = px(18) })
        }
        bar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            max = 100; root.addView(this, LinearLayout.LayoutParams(MATCH_PARENT, WRAP_CONTENT).apply { topMargin = px(16) })
        }
        status = TextView(this).apply { setTextColor(Color.parseColor("#9CA3AF")); gravity = Gravity.CENTER; setPadding(0, px(8), 0, 0); root.addView(this) }
        langBtn = Button(this).apply {
            text = tr("English", "العربية"); setOnClickListener { switchLang() }
            root.addView(this, LinearLayout.LayoutParams(WRAP_CONTENT, WRAP_CONTENT).apply { gravity = Gravity.CENTER; topMargin = px(24) })
        }
        setContentView(ScrollView(this).apply { setBackgroundColor(Color.parseColor("#0F1220")); isFillViewport = true; addView(root) })
    }

    private fun switchLang() {
        val url = urlEdit.text.toString(); val audio = audioRadio.isChecked
        val q = qualitySpinner.selectedItemPosition; val pl = playlistCheck.isChecked
        lang = if (lang == "ar") "en" else "ar"
        getSharedPreferences("vg", MODE_PRIVATE).edit().putString("lang", lang).apply()
        buildUi()
        urlEdit.setText(url); audioRadio.isChecked = audio; qualitySpinner.setSelection(q); playlistCheck.isChecked = pl
        btn.isEnabled = ready
        status.text = if (ready) tr("جاهز", "Ready") else tr("جارٍ تجهيز المحرك...", "Preparing engine...")
    }

    private fun startDownload() {
        val url = urlEdit.text.toString().trim()
        if (url.isEmpty() || !ready) return
        val audio = audioRadio.isChecked
        val h = qualityHeights[qualitySpinner.selectedItemPosition]
        val playlist = playlistCheck.isChecked
        btn.isEnabled = false; bar.progress = 0; status.text = tr("جارٍ التحميل...", "Downloading...")
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
                status.text = tr("تم الحفظ في مجلد Download/VideoGrab ✔", "Saved to Download/VideoGrab ✔")
            } catch (e: Exception) {
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
