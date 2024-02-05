package com.masamonoke.central.api.service

import com.masamonoke.central.domain.company.BestMethod
import kotlin.math.abs
import kotlin.math.sqrt

private fun normalize(matrix: List<List<Double>>): Array<DoubleArray> {
    val rows = matrix.size
    val cols = matrix[0].size

    val normalizedMatrix = Array(rows) { DoubleArray(cols) }

    matrix.forEachIndexed() { row, column ->
        column.forEachIndexed { col, score ->
            var sum = 0.0
            for (r in 0 until rows) {
                sum += abs(matrix[r][col])
            }
            normalizedMatrix[row][col] = score / sum
        }
    }

    return normalizedMatrix
}

private fun bestWorst(normalizedMatrix: Array<DoubleArray>, methods: List<BestMethod>): Pair<DoubleArray, DoubleArray> {
    val rows = normalizedMatrix.size
    val cols = normalizedMatrix[0].size

    val vMinus = DoubleArray(cols)
    val vPlus = DoubleArray(cols)
    for (c in 0 until cols) {

        var min = Double.MAX_VALUE
        var max = Double.MIN_VALUE
        for (r in 0 until rows) {
            if (normalizedMatrix[r][c] < min) {
                min = normalizedMatrix[r][c]
            }
            if (normalizedMatrix[r][c] > max) {
                max = normalizedMatrix[r][c]
            }

        }

        if (methods[c] == BestMethod.MAXIMIZE) {
            vMinus[c] = min
            vPlus[c] = max
        } else {
            vMinus[c] = max
            vPlus[c] = min
        }

    }

    return Pair(vPlus, vMinus)
}

private fun euclideanDistance(normalizedMatrix: Array<DoubleArray>, vPlus: DoubleArray, vMinus: DoubleArray): Pair<DoubleArray, DoubleArray> {

    val rows = normalizedMatrix.size
    val cols = normalizedMatrix[0].size

    val euclideanBest = DoubleArray(rows)
    val euclideanWorst = DoubleArray(rows)
    for (r in 0 until rows) {
        var bestSum = 0.0
        var worstSum = 0.0
        for (c in 0 until cols) {
            bestSum += Math.pow((normalizedMatrix[r][c] - vPlus[c]), 2.0)
            worstSum += Math.pow((normalizedMatrix[r][c] - vMinus[c]), 2.0)
        }
        euclideanBest[r] = sqrt(bestSum)
        euclideanWorst[r] = sqrt(worstSum)
    }

    return Pair(euclideanBest, euclideanWorst)
}

private fun performance(matrix: List<List<Double>>, methods: List<BestMethod>): DoubleArray {


    val normalizedMatrix = normalize(matrix)

    val (vPlus, vMinus) = bestWorst(normalizedMatrix, methods)

    val (euclideanBest, euclideanWorst) = euclideanDistance(normalizedMatrix, vPlus, vMinus)

    val rows = normalizedMatrix.size

    val performance = DoubleArray(rows)
    for (r in 0 until rows) {
        performance[r] = euclideanWorst[r] / (euclideanWorst[r] + euclideanBest[r])
    }

    return performance
}

fun topsis(companiesScore: LinkedHashMap<String, LinkedHashMap<String, Double>>, methods: ArrayList<BestMethod>): List<Pair<String, Double>> {
    val matrix = ArrayList<ArrayList<Double>>()
    companiesScore.forEach { company ->
        val l = ArrayList<Double>()
        company.value.forEach { score ->
            l.add(score.value)
        }
        matrix.add(l)
    }

    val p = performance(matrix, methods)
    val rank = ArrayList<Pair<String, Double>>()
    var r = 0
    companiesScore.forEach {company ->
        rank.add(Pair(company.key, p[r]))
        r += 1
    }

    return rank.sortedBy { it.second }.asReversed()
}