package cl.duoc.maduraapp.ui

import cl.duoc.maduraapp.data.dto.ScanResultDto

/**
 * Estados posibles del flujo de escaneo. Mutex: la UI siempre está en exactamente
 * uno de estos estados a la vez.
 */
sealed interface ScanState {

    /** Estado inicial — cámara lista, esperando captura. */
    data object Idle : ScanState

    /** Imagen enviada al backend, esperando respuesta. */
    data object Loading : ScanState

    /** Inferencia exitosa con detección. */
    data class Success(val result: ScanResultDto) : ScanState

    /** Inferencia exitosa pero sin detección (success=false del backend). */
    data class NoDetection(val message: String) : ScanState

    /** Error de red, servidor o validación. */
    data class Error(val cause: Throwable) : ScanState
}
