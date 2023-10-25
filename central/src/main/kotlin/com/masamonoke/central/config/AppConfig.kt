package com.masamonoke.central.config

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.http.converter.ByteArrayHttpMessageConverter
import org.springframework.http.converter.HttpMessageConverter
import org.springframework.web.client.RestOperations
import org.springframework.web.client.RestTemplate

@Configuration
class AppConfig {
    @Bean
    fun restOperations(messageConverters: List<HttpMessageConverter<Any>>): RestOperations {
        return RestTemplate(messageConverters)
    }

    @Bean
    fun byteArrayHttpMessageConverter(): ByteArrayHttpMessageConverter {
        return ByteArrayHttpMessageConverter()
    }

}