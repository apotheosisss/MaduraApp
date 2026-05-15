package cl.duoc.maduraapp.ui.history

import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import cl.duoc.maduraapp.R
import cl.duoc.maduraapp.databinding.ActivityHistoryBinding

/**
 * Pantalla de historial — RecyclerView que muestra los escaneos recientes.
 *
 * Combina dos fuentes:
 *  - Stream del cache local Room ([HistoryViewModel.cachedItems]): siempre
 *    visible, incluso offline.
 *  - Estado de sincronización remota ([HistoryViewModel.state]): controla
 *    spinner del SwipeRefreshLayout y banners de error.
 */
class HistoryActivity : AppCompatActivity() {

    private lateinit var binding: ActivityHistoryBinding
    private val viewModel: HistoryViewModel by viewModels()
    private val adapter = HistoryAdapter()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityHistoryBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setSupportActionBar(binding.toolbar)
        binding.toolbar.setNavigationOnClickListener { finish() }

        binding.recyclerHistory.layoutManager = LinearLayoutManager(this)
        binding.recyclerHistory.adapter = adapter

        binding.swipeRefresh.setOnRefreshListener { viewModel.refresh() }

        observeViewModel()
    }

    private fun observeViewModel() {
        viewModel.cachedItems.observe(this) { items ->
            adapter.submitList(items)
            binding.emptyState.visibility =
                if (items.isEmpty()) View.VISIBLE else View.GONE
        }

        viewModel.state.observe(this) { state ->
            when (state) {
                is HistoryState.Loading -> {
                    binding.swipeRefresh.isRefreshing = true
                }
                is HistoryState.Loaded -> {
                    binding.swipeRefresh.isRefreshing = false
                }
                is HistoryState.Error -> {
                    binding.swipeRefresh.isRefreshing = false
                    Log.w(TAG, "Fallo al refrescar historial", state.cause)
                    Toast.makeText(
                        this,
                        R.string.err_network,
                        Toast.LENGTH_SHORT,
                    ).show()
                }
            }
        }
    }

    private companion object {
        const val TAG = "HistoryActivity"
    }
}
