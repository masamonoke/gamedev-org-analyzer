package com.masamonoke.central.domain.company

data class CompanyScore (
		val company: Company,
		var score: Double = 0.0,
		var evaluatorName: String = "",
		var bestMethod: BestMethod = BestMethod.MAXIMIZE
)

enum class BestMethod(val value: Int) {
	MAXIMIZE(0),
	MINIMIZE(1);

	companion object {
		fun fromInt(value: Int) = BestMethod.values().first { it.value == value }
	}
}
