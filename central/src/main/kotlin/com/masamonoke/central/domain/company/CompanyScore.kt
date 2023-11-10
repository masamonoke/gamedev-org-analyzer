package com.masamonoke.central.domain.company

data class CompanyScore (
    val company: Company,
    var totalScore: Double = 0.0,
    val playersReputation: Double? = 0.0,
    val investorsScore: Double? = 0.0
)
