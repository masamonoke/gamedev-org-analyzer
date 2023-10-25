package com.masamonoke.central.domain.company

import java.util.Date

data class Company (
    val name: String,
    var symbol: String,
    val founded: Date? = null,
    val size: CompanySize? = null,
    val region: Region? = null,
    val country: String? = null
)