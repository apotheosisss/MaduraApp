package cl.duoc.maduraapp

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Matrix
import android.os.Bundle
import android.util.Log
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import cl.duoc.maduraapp.data.dto.ScanResultDto
import cl.duoc.maduraapp.databinding.ActivityMainBinding
import cl.duoc.maduraapp.ui.ScanState
import cl.duoc.maduraapp.ui.ScanViewModel
import cl.duoc.maduraapp.ui.history.HistoryActivity
import java.io.ByteArrayOutputStream
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

/**
 * Activity principal: muestra preview de cámara, captura una imagen, la
 * comprime a JPEG y delega al [ScanViewModel] para enviarla al backend.
 *
 * Al recibir resultado, pinta el semáforo de madurez (verde/amarillo/rojo)
 * + recomendación + nivel de confianza.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val viewModel: ScanViewModel by viewModels()

    private var imageCapture: ImageCapture? = null
    private lateinit var cameraExecutor: ExecutorService

    private val requestCameraPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) startCamera() else showPermissionRationale()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        cameraExecutor = Executors.newSingleThreadExecutor()

        setSupportActionBar(binding.toolbar)

        binding.btnScan.setOnClickListener { takePictureAndSubmit() }
        binding.btnRetry.setOnClickListener {
            viewModel.reset()
        }
        binding.btnGrantPermission.setOnClickListener {
            requestCameraPermissionLauncher.launch(Manifest.permission.CAMERA)
        }

        observeState()

        if (hasCameraPermission()) {
            startCamera()
        } else {
            requestCameraPermissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean = when (item.itemId) {
        R.id.action_history -> {
            startActivity(Intent(this, HistoryActivity::class.java))
            true
        }
        else -> super.onOptionsItemSelected(item)
    }

    // ---------------------------------------------------------------- Camera

    private fun hasCameraPermission(): Boolean = ContextCompat.checkSelfPermission(
        this, Manifest.permission.CAMERA
    ) == PackageManager.PERMISSION_GRANTED

    private fun startCamera() {
        binding.permissionPanel.visibility = View.GONE
        binding.previewView.visibility = View.VISIBLE

        val providerFuture = ProcessCameraProvider.getInstance(this)
        providerFuture.addListener({
            val cameraProvider = providerFuture.get()

            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(binding.previewView.surfaceProvider)
            }
            imageCapture = ImageCapture.Builder()
                .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                .build()

            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    this,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    imageCapture,
                )
            } catch (exc: Exception) {
                Log.e(TAG, "No se pudo enlazar el ciclo de vida de la cámara", exc)
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun showPermissionRationale() {
        binding.previewView.visibility = View.GONE
        binding.permissionPanel.visibility = View.VISIBLE
    }

    // -------------------------------------------------------------- Capture

    private fun takePictureAndSubmit() {
        val capture = imageCapture ?: run {
            Toast.makeText(this, R.string.err_unknown, Toast.LENGTH_SHORT).show()
            return
        }

        capture.takePicture(
            ContextCompat.getMainExecutor(this),
            object : ImageCapture.OnImageCapturedCallback() {
                override fun onCaptureSuccess(image: ImageProxy) {
                    try {
                        val bytes = image.toCompressedJpeg()
                        viewModel.submitImage(bytes)
                    } finally {
                        image.close()
                    }
                }

                override fun onError(exception: ImageCaptureException) {
                    Log.e(TAG, "Captura falló", exception)
                    Toast.makeText(
                        this@MainActivity,
                        R.string.err_unknown,
                        Toast.LENGTH_SHORT,
                    ).show()
                }
            }
        )
    }

    // ---------------------------------------------------------------- State

    private fun observeState() {
        viewModel.state.observe(this) { state ->
            when (state) {
                is ScanState.Idle -> renderIdle()
                is ScanState.Loading -> renderLoading()
                is ScanState.Success -> renderSuccess(state.result)
                is ScanState.NoDetection -> renderNoDetection(state.message)
                is ScanState.Error -> renderError(state.cause)
            }
        }
    }

    private fun renderIdle() = with(binding) {
        progressBar.visibility = View.GONE
        resultPanel.visibility = View.GONE
        btnScan.visibility = View.VISIBLE
        btnRetry.visibility = View.GONE
    }

    private fun renderLoading() = with(binding) {
        progressBar.visibility = View.VISIBLE
        resultPanel.visibility = View.GONE
        btnScan.visibility = View.GONE
        btnRetry.visibility = View.GONE
    }

    private fun renderSuccess(result: ScanResultDto) = with(binding) {
        progressBar.visibility = View.GONE
        resultPanel.visibility = View.VISIBLE
        btnScan.visibility = View.GONE
        btnRetry.visibility = View.VISIBLE

        val colorRes = when (result.colorCode) {
            "green" -> R.color.ripeness_green
            "yellow" -> R.color.ripeness_yellow
            "red" -> R.color.ripeness_red
            else -> R.color.ripeness_yellow
        }
        ripenessIndicator.backgroundTintList =
            ContextCompat.getColorStateList(this@MainActivity, colorRes)

        txtFruit.text = getString(
            R.string.fmt_fruit_label,
            result.fruitType.toFruitDisplay(),
            result.maturityLabel.toMaturityDisplay(),
        )
        txtRecommendation.text = result.recommendation
        txtConfidence.text = getString(R.string.fmt_confidence, result.confidence * 100)
    }

    private fun renderNoDetection(message: String) = with(binding) {
        progressBar.visibility = View.GONE
        resultPanel.visibility = View.GONE
        btnScan.visibility = View.GONE
        btnRetry.visibility = View.VISIBLE
        Toast.makeText(this@MainActivity, message, Toast.LENGTH_LONG).show()
    }

    private fun renderError(cause: Throwable) = with(binding) {
        Log.e(TAG, "Error al escanear", cause)
        progressBar.visibility = View.GONE
        resultPanel.visibility = View.GONE
        btnScan.visibility = View.GONE
        btnRetry.visibility = View.VISIBLE
        Toast.makeText(this@MainActivity, R.string.err_network, Toast.LENGTH_LONG).show()
    }

    // ------------------------------------------------------------- Helpers

    private fun String.toFruitDisplay(): String = when (this) {
        "aguacate_hass" -> getString(R.string.fruit_aguacate_hass)
        "platano" -> getString(R.string.fruit_platano)
        "tomate_usda" -> getString(R.string.fruit_tomate_usda)
        "mango" -> getString(R.string.fruit_mango)
        else -> this
    }

    private fun String.toMaturityDisplay(): String = when (this) {
        "INMADURO" -> getString(R.string.maturity_inmaduro)
        "OPTIMO" -> getString(R.string.maturity_optimo)
        "SOBRE_MADURO" -> getString(R.string.maturity_sobre_maduro)
        else -> this
    }

    private fun ImageProxy.toCompressedJpeg(quality: Int = 85): ByteArray {
        // CameraX provee un YUV/JPEG según configuración. CAPTURE_MODE_*
        // por defecto entrega ImageFormat.JPEG en el plano 0.
        val buffer = planes[0].buffer
        val raw = ByteArray(buffer.remaining()).also { buffer.get(it) }

        // Si no es JPEG (algunos dispositivos), lo decodificamos y recomprimimos.
        val bitmap = android.graphics.BitmapFactory.decodeByteArray(raw, 0, raw.size)
            ?: return raw  // ya está en formato válido

        val rotated = if (imageInfo.rotationDegrees != 0) {
            val matrix = Matrix().apply { postRotate(imageInfo.rotationDegrees.toFloat()) }
            Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
        } else bitmap

        val out = ByteArrayOutputStream()
        rotated.compress(Bitmap.CompressFormat.JPEG, quality, out)
        return out.toByteArray()
    }

    private companion object {
        const val TAG = "MainActivity"
    }
}
