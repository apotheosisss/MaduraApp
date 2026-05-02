package cl.duoc.maduraapp.ui.history

import cl.duoc.maduraapp.data.dto.ScanResultDto

/**
 * Estado de la pantalla de historial.
 *
 *  - [Loading]   primer fetch o pull-to-refresh
 *  - [Loaded]    lista (puede estar vacía si `items.isEmpty()`)
 *  - [Error]     fallo en la sincronización; la UI puede seguir mostrando
 *                el cache local que llega vía Flow separado
 */
sealed interface HistoryState {
    data object Loading : HistoryState
    data class Loaded(val items: List<ScanResultDto>) : HistoryState
    data class Error(val cause: Throwable, val cachedItems: List<ScanResultDto>) : HistoryState
}
