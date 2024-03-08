FROM gradle:7.2.0-jdk17

COPY central/src src

COPY central/build.gradle.kts build.gradle.kts

COPY central/settings.gradle.kts settings.gradle.kts

COPY central/gradlew gradlew

COPY central/gradle gradle

EXPOSE 3003

CMD ["./gradlew", "bootRun"]
