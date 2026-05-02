package cl.duoc.maduraapp

import android.app.Application
import cl.duoc.maduraapp.data.local.MaduraDatabase
import cl.duoc.maduraapp.data.local.ScanDao

/**
 * Application class — punto de inicialización temprana y singleton holder
 * para componentes que requieren Context (Room).
 *
 * Sin DI framework por simplicidad — para Sprint 2 alcanza con accesos
 * via `applicationContext`.
 */
class MaduraApp : Application() {

    val scanDao: ScanDao by lazy { MaduraDatabase.get(this).scanDao() }

    override fun onCreate() {
        super.onCreate()
        instance = this
    }

    companion object {
        @Volatile
        private var instance: MaduraApp? = null

        fun get(): MaduraApp =
            instance ?: error("MaduraApp todavía no se ha inicializado")
    }
}
