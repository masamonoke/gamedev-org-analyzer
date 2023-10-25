package com.masamonoke.central.api

import com.fasterxml.jackson.databind.ObjectMapper
import com.masamonoke.central.domain.company.Company
import com.masamonoke.central.domain.company.CompanyScore
import com.masamonoke.central.domain.company.CompanySize
import com.masamonoke.central.domain.company.Region
import io.github.oshai.kotlinlogging.KotlinLogging
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.*
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController
import org.springframework.web.client.HttpServerErrorException
import org.springframework.web.client.ResourceAccessException
import org.springframework.web.client.RestOperations
import org.springframework.web.client.RestTemplate
import org.springframework.web.util.UriComponentsBuilder
import java.lang.NullPointerException
import java.util.*
import kotlin.collections.ArrayList
import kotlin.collections.HashMap
import kotlin.collections.LinkedHashMap

private val logger = KotlinLogging.logger {}

@RestController
@RequestMapping("/report")
class ReportController(
    val restOperations: RestOperations,
    @Value("\${stock_predictor}") var stockPredictorUrl: String,
    val objectMapper: ObjectMapper
    ) {

    private fun requestSymbol(companyName: String): String {
        val url = "https://query2.finance.yahoo.com/v1/finance/search"
        val userAgent =
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        val params = HashMap<String, Any>()
        params["q"] = companyName
        params["quotes_count"] = 1
        params["country"] = "United States"
        val headers = HttpHeaders()
        headers.accept = Collections.singletonList(MediaType.ALL)
        headers.add("User-Agent", userAgent)
        val entity = HttpEntity("parameters", headers)
        val urlTemplate = UriComponentsBuilder.fromHttpUrl(url)
            .queryParam("q", "{q}")
            .queryParam("quotes_count", "{quotes_count}")
            .queryParam("country", "{country}")
            .build().toUriString()
        val response = restOperations.exchange(urlTemplate, HttpMethod.GET, entity, Map::class.java, params)
        val quotes = response.body?.get("quotes") as ArrayList<*>
        val quote = quotes[0] as LinkedHashMap<*, *>
        return quote["symbol"] as String
    }

    @GetMapping
    fun report(@RequestBody map: Map<String, List<String>>): Any {
        val companiesScore = ArrayList<CompanyScore>()
        for (companyName in map["companies"]!!) {
            try {
                val symbol = requestSymbol(companyName)
                val company = Company(companyName, symbol)
                companiesScore.add(CompanyScore(company))
            } catch (e: Exception) {
                logger.info { "Can't find symbol for company: $companyName" }
            }
        }

        try {
            val headers = HttpHeaders()
            headers.contentType = MediaType.APPLICATION_JSON
            val restTemplate = RestTemplate()
            val json = objectMapper.writeValueAsString(companiesScore)
            val entity = HttpEntity<String>(json, headers)
            val response = restTemplate.postForObject(stockPredictorUrl, entity, String::class.java)
            val mutatedCompanyScoreJsonList = objectMapper.readValue(response, ArrayList::class.java)
            val mutatedCompaniesScore = ArrayList<CompanyScore>()
            mutatedCompanyScoreJsonList.forEach {
                it as LinkedHashMap<*, *>
                val companyMap = it["company"] as HashMap<*, *>
                val size = companyMap["size"]
                val region = companyMap["region"]
                val country = companyMap["country"]
                val company = Company(
                    name = companyMap["name"] as String,
                    symbol = companyMap["symbol"] as String,
                    size = if (size == null) null else size as CompanySize,
                    region = if (region == null) null else region as Region,
                    country = if (country == null) null else country as String
                )
                val totalScore = it["total_score"]
                val playerReputation = it["players_reputation"]
                val investorsScore = it["investers_score"]
                val companyScore = CompanyScore(
                    company,
                    totalScore = totalScore as Double,
                    playersReputation = playerReputation as Double,
                    investorsScore = investorsScore as Double
                )
                mutatedCompaniesScore.add(companyScore)
            }
            return mutatedCompaniesScore
        } catch (e: ResourceAccessException) {
            logger.error { "Cannot reach resource $stockPredictorUrl: $e" }
            return ResponseEntity("Cannot reach recourse", HttpStatus.INTERNAL_SERVER_ERROR)
        } catch (e: HttpServerErrorException) {
            logger.error { "Requested server thrown error: $e" }
            return ResponseEntity("Filter service error", HttpStatus.INTERNAL_SERVER_ERROR)
        } catch (e: NullPointerException) {
            logger.error { "Double value cannot be null: $e" }
            return ResponseEntity("Double object is null", HttpStatus.CONFLICT)
        }
    }

}
