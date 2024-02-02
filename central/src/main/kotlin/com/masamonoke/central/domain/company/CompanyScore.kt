package com.masamonoke.central.domain.company

data class CompanyScore (
		val company: Company,
		var score: Double = 0.0,
		var evaluatorName: String = ""
)
