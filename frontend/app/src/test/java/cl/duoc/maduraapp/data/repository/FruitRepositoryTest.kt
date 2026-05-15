package cl.duoc.maduraapp.data.repository

import app.cash.turbine.test
import cl.duoc.maduraapp.data.api.MaduraApiService
import cl.duoc.maduraapp.data.dto.HistoryResponseDto
import cl.duoc.maduraapp.data.dto.PredictResponseDto
import cl.duoc.maduraapp.data.dto.ScanResultDto
import cl.duoc.maduraapp.data.local.LocalScanDataSource
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.coVerifySequence
import io.mockk.mockk
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import okhttp3.MultipartBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class FruitRepositoryTest {

    private lateinit var api: MaduraApiService
    private lateinit var local: LocalScanDataSource
    private lateinit var repository: FruitRepository

    private val sampleScan = ScanResultDto(
        fruitType = "mango",
        maturityLabel = "OPTIMO",
        confidence = 0.92,
        bbox = listOf(10.0, 20.0, 300.0, 400.0),
        recommendation = "Consumir hoy, refrigerar si no lo consumes",
        colorCode = "yellow",
    )

    @Before
    fun setUp() {
        api = mockk(relaxed = true)
        local = mockk(relaxed = true)
        repository = FruitRepository(api = api, local = local)
    }

    // ─────────────────────────────────────────────────────────────── predict

    @Test
    fun `predict cachea el resultado cuando el backend detecta una fruta`() = runTest {
        val response = PredictResponseDto(success = true, data = sampleScan)
        coEvery { api.predict(any<MultipartBody.Part>(), any()) } returns response

        val result = repository.predict("fake".toByteArray())

        assertTrue(result.isSuccess)
        assertEquals(sampleScan, result.getOrNull()?.data)
        coVerify(exactly = 1) { local.cache(sampleScan) }
    }

    @Test
    fun `predict NO cachea cuando el backend no detecta nada`() = runTest {
        val response = PredictResponseDto(
            success = false,
            data = null,
            error = "No se detectó ninguna fruta soportada",
        )
        coEvery { api.predict(any<MultipartBody.Part>(), any()) } returns response

        val result = repository.predict("fake".toByteArray())

        assertTrue(result.isSuccess)
        assertEquals(null, result.getOrNull()?.data)
        coVerify(exactly = 0) { local.cache(any(), any()) }
    }

    @Test
    fun `predict propaga la excepcion del API como Result failure`() = runTest {
        coEvery { api.predict(any<MultipartBody.Part>(), any()) } throws
            RuntimeException("network down")

        val result = repository.predict("fake".toByteArray())

        assertTrue(result.isFailure)
        assertEquals("network down", result.exceptionOrNull()?.message)
        coVerify(exactly = 0) { local.cache(any(), any()) }
    }

    @Test
    fun `predict envia bearer token cuando se provee`() = runTest {
        coEvery { api.predict(any<MultipartBody.Part>(), any()) } returns
            PredictResponseDto(success = true, data = sampleScan)

        repository.predict("fake".toByteArray(), bearerToken = "abc.def.ghi")

        coVerify { api.predict(any<MultipartBody.Part>(), "Bearer abc.def.ghi") }
    }

    @Test
    fun `predict NO envia header cuando no hay token`() = runTest {
        coEvery { api.predict(any<MultipartBody.Part>(), any()) } returns
            PredictResponseDto(success = true, data = sampleScan)

        repository.predict("fake".toByteArray(), bearerToken = null)

        coVerify { api.predict(any<MultipartBody.Part>(), null) }
    }

    // ────────────────────────────────────────────────────────── refreshHistory

    @Test
    fun `refreshHistory exitoso reemplaza el cache local cuando offset es 0`() = runTest {
        val items = listOf(sampleScan, sampleScan.copy(maturityLabel = "INMADURO"))
        val response = HistoryResponseDto(items = items, total = 2, limit = 50, offset = 0)
        coEvery { api.history(any(), any(), any()) } returns response

        val result = repository.refreshHistory(limit = 50, offset = 0)

        assertTrue(result.isSuccess)
        coVerifySequence {
            api.history(50, 0, null)
            local.clear()
            local.cache(items[0])
            local.cache(items[1])
        }
    }

    @Test
    fun `refreshHistory con offset mayor a 0 NO limpia el cache`() = runTest {
        val response = HistoryResponseDto(
            items = listOf(sampleScan),
            total = 100,
            limit = 50,
            offset = 50,
        )
        coEvery { api.history(any(), any(), any()) } returns response

        repository.refreshHistory(limit = 50, offset = 50)

        coVerify(exactly = 0) { local.clear() }
        coVerify(exactly = 0) { local.cache(any(), any()) }
    }

    @Test
    fun `refreshHistory falla devuelve Result failure sin tocar cache`() = runTest {
        coEvery { api.history(any(), any(), any()) } throws
            RuntimeException("timeout")

        val result = repository.refreshHistory()

        assertTrue(result.isFailure)
        assertNotNull(result.exceptionOrNull())
        coVerify(exactly = 0) { local.clear() }
        coVerify(exactly = 0) { local.cache(any(), any()) }
    }

    // ─────────────────────────────────────────────────────── observeLocal

    @Test
    fun `observeLocalHistory emite los items del cache local`() = runTest {
        val cached = listOf(sampleScan)
        coEvery { local.observeRecent(any()) } returns flowOf(cached)

        repository.observeLocalHistory(limit = 50).test {
            assertEquals(cached, awaitItem())
            awaitComplete()
        }
    }

    // ──────────────────────────────────────────────────────────────── health

    @Test
    fun `isBackendHealthy retorna true cuando el endpoint responde con status ok`() = runTest {
        coEvery { api.health() } returns mapOf("status" to "ok")

        val healthy = repository.isBackendHealthy()

        assertTrue(healthy)
    }

    @Test
    fun `isBackendHealthy retorna false ante excepcion de red`() = runTest {
        coEvery { api.health() } throws RuntimeException("ECONNREFUSED")

        val healthy = repository.isBackendHealthy()

        assertFalse(healthy)
    }
}
