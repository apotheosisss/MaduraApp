package cl.duoc.maduraapp.ui.history

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.asLiveData
import androidx.lifecycle.viewModelScope
import cl.duoc.maduraapp.data.dto.ScanResultDto
import cl.duoc.maduraapp.data.repository.FruitRepository
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

/**
 * ViewModel del historial.
 *
 * Emite dos streams:
 *  - [cachedItems]: refleja siempre el cache local Room (LiveData reactivo
 *    que actualiza la UI ante nuevos escaneos).
 *  - [state]: estado del último intento de sincronización con el backend.
 *
 * La Activity decide qué priorizar — típicamente muestra `cachedItems` y
 * superpone un spinner / banner de error según [state].
 */
class HistoryViewModel(
    private val repository: FruitRepository = FruitRepository(),
) : ViewModel() {

    /** Stream reactivo del cache local — siempre disponible aún sin red. */
    val cachedItems: LiveData<List<ScanResultDto>> =
        repository.observeLocalHistory(limit = MAX_ITEMS).asLiveData()

    private val _state = MutableLiveData<HistoryState>(HistoryState.Loading)
    val state: LiveData<HistoryState> = _state

    init {
        refresh()
    }

    fun refresh(bearerToken: String? = null) {
        _state.value = HistoryState.Loading

        viewModelScope.launch {
            repository.refreshHistory(limit = MAX_ITEMS, bearerToken = bearerToken)
                .onSuccess { response ->
                    _state.value = HistoryState.Loaded(response.items)
                }
                .onFailure { throwable ->
                    val cached = repository.observeLocalHistory(MAX_ITEMS).first()
                    _state.value = HistoryState.Error(throwable, cached)
                }
        }
    }

    private companion object {
        const val MAX_ITEMS = 50
    }
}
