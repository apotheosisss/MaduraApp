package cl.duoc.maduraapp.testing

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.rules.TestWatcher
import org.junit.runner.Description

/**
 * Reemplaza el `Dispatchers.Main` real por un [TestDispatcher] durante el test.
 *
 * Necesario para `viewModelScope.launch { ... }` — sin esta regla, las
 * coroutines disparadas en el `init` del ViewModel fallan con
 * `IllegalStateException: Module with the Main dispatcher had failed to initialize`.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class MainCoroutineRule(
    val testDispatcher: TestDispatcher = StandardTestDispatcher(),
) : TestWatcher() {

    override fun starting(description: Description) {
        Dispatchers.setMain(testDispatcher)
    }

    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
