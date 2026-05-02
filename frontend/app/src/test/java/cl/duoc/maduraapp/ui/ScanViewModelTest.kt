package cl.duoc.maduraapp.ui

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import cl.duoc.maduraapp.data.dto.PredictResponseDto
import cl.duoc.maduraapp.data.dto.ScanResultDto
import cl.duoc.maduraapp.data.repository.FruitRepository
import cl.duoc.maduraapp.testing.MainCoroutineRule
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ScanViewModelTest {

    @get:Rule val mainCoroutineRule = MainCoroutineRule()

    /** LiveData en JVM tests requiere ejecutor síncrono. */
    @get:Rule val instantTaskExecutorRule = InstantTaskExecutorRule()

    private lateinit var repository: FruitRepository
    private lateinit var viewModel: ScanViewModel

    private val sampleScan = ScanResultDto(
        fruitType = "aguacate_hass",
        maturityLabel = "OPTIMO",
        confidence = 0.91,
        bbox = listOf(120.5, 80.3, 340.2, 290.1),
        recommendation = "Consumir hoy o refrigerar hasta 2 días",
        colorCode = "yellow",
    )

    @Before
    fun setUp() {
        repository = mockk()
        viewModel = ScanViewModel(repository)
    }

    @Test
    fun `estado inicial es Idle`() {
        assertTrue(viewModel.state.value is ScanState.Idle)
    }

    @Test
    fun `submitImage cuando hay deteccion transiciona a Success`() = runTest {
        val response = PredictResponseDto(success = true, data = sampleScan)
        coEvery { repository.predict(any(), any()) } returns Result.success(response)

        viewModel.submitImage("img".toByteArray())
        advanceUntilIdle()

        val state = viewModel.state.value
        assertTrue("Esperaba Success pero fue $state", state is ScanState.Success)
        assertEquals(sampleScan, (state as ScanState.Success).result)
    }

    @Test
    fun `submitImage cuando el backend no detecta nada transiciona a NoDetection`() = runTest {
        val response = PredictResponseDto(
            success = false,
            data = null,
            error = "No se detectó ninguna fruta soportada",
        )
        coEvery { repository.predict(any(), any()) } returns Result.success(response)

        viewModel.submitImage("img".toByteArray())
        advanceUntilIdle()

        val state = viewModel.state.value
        assertTrue("Esperaba NoDetection pero fue $state", state is ScanState.NoDetection)
        assertEquals(
            "No se detectó ninguna fruta soportada",
            (state as ScanState.NoDetection).message,
        )
    }

    @Test
    fun `submitImage cuando success false y no hay error mensaje usa fallback`() = runTest {
        val response = PredictResponseDto(success = false, data = null, error = null)
        coEvery { repository.predict(any(), any()) } returns Result.success(response)

        viewModel.submitImage("img".toByteArray())
        advanceUntilIdle()

        val state = viewModel.state.value as ScanState.NoDetection
        assertEquals("No se detectó ninguna fruta soportada", state.message)
    }

    @Test
    fun `submitImage transiciona a Error cuando el repository falla`() = runTest {
        val cause = RuntimeException("network down")
        coEvery { repository.predict(any(), any()) } returns Result.failure(cause)

        viewModel.submitImage("img".toByteArray())
        advanceUntilIdle()

        val state = viewModel.state.value
        assertTrue("Esperaba Error pero fue $state", state is ScanState.Error)
        assertEquals(cause, (state as ScanState.Error).cause)
    }

    @Test
    fun `reset vuelve el estado a Idle`() = runTest {
        coEvery { repository.predict(any(), any()) } returns Result.success(
            PredictResponseDto(success = true, data = sampleScan)
        )
        viewModel.submitImage("img".toByteArray())
        advanceUntilIdle()
        assertTrue(viewModel.state.value is ScanState.Success)

        viewModel.reset()

        assertTrue(viewModel.state.value is ScanState.Idle)
    }
}
