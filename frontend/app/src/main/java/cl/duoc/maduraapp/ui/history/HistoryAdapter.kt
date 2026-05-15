package cl.duoc.maduraapp.ui.history

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import cl.duoc.maduraapp.R
import cl.duoc.maduraapp.data.dto.ScanResultDto
import cl.duoc.maduraapp.databinding.ItemScanHistoryBinding

/**
 * Adapter del historial. Usa [ListAdapter] + [DiffUtil] para que actualizar
 * la lista cuando llega un escaneo nuevo no recicle todas las filas.
 */
class HistoryAdapter : ListAdapter<ScanResultDto, HistoryAdapter.ScanViewHolder>(DIFF) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ScanViewHolder {
        val binding = ItemScanHistoryBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return ScanViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ScanViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class ScanViewHolder(
        private val binding: ItemScanHistoryBinding,
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(item: ScanResultDto) = with(binding) {
            val ctx = root.context

            val colorRes = when (item.colorCode) {
                "green" -> R.color.ripeness_green
                "yellow" -> R.color.ripeness_yellow
                "red" -> R.color.ripeness_red
                else -> R.color.ripeness_yellow
            }
            itemRipenessIndicator.backgroundTintList =
                ContextCompat.getColorStateList(ctx, colorRes)

            itemFruit.text = ctx.getString(
                R.string.fmt_fruit_label,
                item.fruitType.toFruitDisplay(ctx),
                item.maturityLabel.toMaturityDisplay(ctx),
            )
            itemRecommendation.text = item.recommendation
            itemConfidence.text = ctx.getString(
                R.string.fmt_confidence,
                item.confidence * 100,
            )
        }

        private fun String.toFruitDisplay(ctx: android.content.Context): String = when (this) {
            "aguacate_hass" -> ctx.getString(R.string.fruit_aguacate_hass)
            "platano" -> ctx.getString(R.string.fruit_platano)
            "tomate_usda" -> ctx.getString(R.string.fruit_tomate_usda)
            "mango" -> ctx.getString(R.string.fruit_mango)
            else -> this
        }

        private fun String.toMaturityDisplay(ctx: android.content.Context): String = when (this) {
            "INMADURO" -> ctx.getString(R.string.maturity_inmaduro)
            "OPTIMO" -> ctx.getString(R.string.maturity_optimo)
            "SOBRE_MADURO" -> ctx.getString(R.string.maturity_sobre_maduro)
            else -> this
        }
    }

    companion object {
        private val DIFF = object : DiffUtil.ItemCallback<ScanResultDto>() {
            // Sin un id estable propio del DTO, comparamos por contenido completo.
            override fun areItemsTheSame(old: ScanResultDto, new: ScanResultDto): Boolean =
                old == new

            override fun areContentsTheSame(old: ScanResultDto, new: ScanResultDto): Boolean =
                old == new
        }
    }
}
