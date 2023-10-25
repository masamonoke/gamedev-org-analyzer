package com.masamonoke.central

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class CentralApplication

fun main(args: Array<String>) {
    runApplication<CentralApplication>(*args)
}
