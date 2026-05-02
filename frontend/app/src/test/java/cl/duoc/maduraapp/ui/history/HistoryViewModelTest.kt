package cl.duoc.maduraapp.ui.history

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import cl.duoc.maduraapp.data.dto.HistoryResponseDto
import cl.duoc.maduraapp.data.dto.ScanResultDto
import cl.duoc.maduraapp.data.repository.FruitRepository
import cl.duoc.maduraapp.testing.MainCoroutineRule
import io.mockk.coEvery
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class HistoryViewModelTest {

    @get:Rule val mainCoroutineRule = MainCoroutineRule()
    @get:Rule val instantTaskExecutorRule = InstantTaskExecutorRule()

    private val sampleScan = ScanResultDto(
        fruitType = "platano",
        maturityLabel = "INMADURO",
        confidence = 0.78,
        bbox = listOf(5.0, 10.0, 200.0, 300.0),
        recommendation = "Madurar en bolsa de papel 2-3 días",
        colorCode = "green",
    )

    private fun buildRepository(
        observeFlow: List<ScanResultDto> = emptyList(),
        refreshResult: Result<HistoryResponseDto> = Result.success(
            HistoryResponseDto(items = emptyList(), total = 0, limit = 50, offset = 0)
        ),
    ): FruitRepository = mockk<FruitRepository>().also { repo ->
        every { repo.observeLocalHistory(any()) } returns flowOf(observeFlow)
        coEvery { repo.refreshHistory(any(), any(), any()) } returns refreshResult
    }

    @Test
    fun `init dispara refresh y termina en Loaded cuando el backend responde`() = runTest {
        val items = listOf(sampleScan)
        val repository = buildRepository(
            refreshResult = Result.success(
                HistoryResponseDto(items = items, total = 1, limit = 50, offset = 0)
            )
        )
        val viewModel = HistoryViewModel(repository)

        advanceUntilIdle()

        val state = viewModel.state.value
        assertTrue("Esperaba Loaded pero fue $state", state is HistoryState.Loaded)
        assertEquals(items, (state as HistoryState.Loaded).items)
    }

    @Test
    fun `cuando el refresh falla expone Error con cache local`() = runTest {
        val cached = listOf(sampleScan)
        val cause = RuntimeException("ECONNREFUSED")
        val repository = buildRepository(
            observeFlow = cached,
            refreshResult = Result.failure(cause),
        )

        val viewModel = HistoryViewModel(repository)
        advanceUntilIdle()

        val state = viewModel.state.value
        assertTrue("Esperaba Error pero fue $state", state is HistoryState.Error)
        val error = state as HistoryState.Error
        assertEquals(cause, error.cause)
        assertEquals(cached, error.cachedItems)
    }

    @Test
    fun `cachedItems refleja el stream del repository`() = runTest {
        val cached = listOf(sampleScan)
        val repository = buildRepository(observeFlow = cached)

        val viewModel = HistoryViewModel(repository)
        advanceUntilIdle()

        assertEquals(cached, viewModel.cachedItems.value)
    }

    @Test
    fun `refresh manual vuelve a Loading antes del resultado`() = runTest {
        val repository = buildRepository()
        val viewModel = HistoryViewModel(repository)
        advanceUntilIdle() // termina el refresh inicial

        viewModel.refresh()
        // Sin avanzar dispatcher, el estado debe estar en Loading
        assertTrue(viewModel.state.value is HistoryState.Loading)

        advanceUntilIdle()
        assertTrue(viewModel.state.value is HistoryState.Loaded)
    }
}
