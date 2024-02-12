package com.masamonoke.central.api

import com.fasterxml.jackson.databind.ObjectMapper
import com.masamonoke.central.api.service.topsis
import com.masamonoke.central.domain.company.BestMethod
import com.masamonoke.central.domain.company.Company
import com.masamonoke.central.domain.company.CompanyScore
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
import java.util.*
import kotlin.collections.ArrayList
import kotlin.collections.HashMap
import kotlin.collections.LinkedHashMap

private val logger = KotlinLogging.logger {}

@RestController
@RequestMapping("/report")
class ReportController(
    val restOperations: RestOperations,
	@Value("\${filters}") var filters: Array<String>,
    val objectMapper: ObjectMapper
    ) {

    @GetMapping
    fun report(@RequestBody map: Map<String, List<String>>): Any {
        val companiesScore = ArrayList<CompanyScore>()
        for (companyName in map["companies"]!!) {
            try {
                val symbol = requestSymbol(companyName)
                val company = Company(companyName, symbol)
                companiesScore.add(CompanyScore(company = company))
            } catch (e: Exception) {
                logger.info { "Can't find symbol for company: $companyName" }
            }
        }

		val evaluatedScores = evaluateScores(companiesScore)
		logger.info { "Evaluated companies" }
		val scores = assemble(evaluatedScores)
		val ranks = topsis(scores, methods(evaluatedScores))
		ranks.forEach {
			scores[it.first]?.put("topsis", it.second)
		}

		val sortedScores = ArrayList<Pair<String, HashMap<String, Double>>>()
		scores.forEach {
			sortedScores.add(Pair(it.key, it.value))
		}

		sortedScores.sortByDescending { it.second["topsis"] }

		return sortedScores
    }

	private fun methods(evaluatedScores: ArrayList<ArrayList<CompanyScore>>): ArrayList<BestMethod> {
		val map = ArrayList<BestMethod>()
		evaluatedScores.forEach {
			val entry = it.first()
			map.add(entry.bestMethod)
		}
		return map
	}

	private fun assemble(evaluatedScores: ArrayList<ArrayList<CompanyScore>>): LinkedHashMap<String, LinkedHashMap<String, Double>> {
		val sumScores = LinkedHashMap<String, LinkedHashMap<String, Double>>()
		for (scoresList in evaluatedScores) {
			for (companyScore in scoresList) {
				val name = companyScore.company.name
				if (!sumScores.contains(name)) {
					sumScores[name] = LinkedHashMap()
				}
				sumScores[name]!![companyScore.evaluatorName] = companyScore.score
			}
		}
		return sumScores
	}

	private fun evaluateScores(companiesScore: ArrayList<CompanyScore>): ArrayList<ArrayList<CompanyScore>> {
		val evaluatedScores = ArrayList<ArrayList<CompanyScore>>()
		val tasks = ArrayList<Thread>()
		for (filter in filters) {
			val t = Thread {
				val response = request(filter, companiesScore)
				val score = readResponse(response)
				synchronized(this) {
					evaluatedScores.add(score)
				}
				logger.info { "Completed request to filter: $filter" }
			}
			tasks.add(t)
		}

		try {
			for (t in tasks) {
				t.start()
			}
			for (t in tasks) {
				t.join()
			}
		} catch (e: ResourceAccessException) {
			logger.error { "Cannot reach resource: $e" }
		} catch (e: HttpServerErrorException) {
			logger.error { "Requested server thrown error: $e" }
		}

		return evaluatedScores
	}

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

	private fun request(url: String, companiesScore: ArrayList<CompanyScore>): String? {
		val headers = HttpHeaders()
		headers.contentType = MediaType.APPLICATION_JSON
		val restTemplate = RestTemplate()
		val json = objectMapper.writeValueAsString(companiesScore)
		val entity = HttpEntity<String>(json, headers)
		logger.info { "Getting $url" }
		val response = restTemplate.postForObject(url, entity, String::class.java)
		return response
	}

	private fun readResponse(response: String?): ArrayList<CompanyScore> {
		val mutatedCompanyScoreJsonList = objectMapper.readValue(response, ArrayList::class.java)
		val mutatedCompaniesScore = ArrayList<CompanyScore>()
		mutatedCompanyScoreJsonList.forEach {
		    it as LinkedHashMap<*, *>
		    val companyMap = it["company"] as HashMap<*, *>
		    val company = Company(
		        name = companyMap["name"] as String,
		        symbol = companyMap["symbol"] as String,
		    )
		    val score = it["score"]
			val evaluatorName = it["evaluator_name"]
			val method = it["best_method"] as String
		    val companyScore = CompanyScore(
		        company,
		        score = score as Double,
				evaluatorName = evaluatorName as String,
				bestMethod = BestMethod.fromInt(method.toInt())
		    )
		    mutatedCompaniesScore.add(companyScore)
		}
		return mutatedCompaniesScore
	}

}
