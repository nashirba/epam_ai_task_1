# SolutionsHub Test Automation Framework

Cucumber BDD test automation framework for [solutionshub.epam.com](https://solutionshub.epam.com/), based on the [TechOrda_TA](https://github.com/Fentezi3/TechOrda_TA) prototype.

## Tech Stack

- **Java 17**
- **Gradle 8.14**
- **Cucumber 7.15.0** (BDD framework)
- **Selenium 4.11.0** (browser automation)
- **JUnit 5** (test runner with JUnit Vintage for Cucumber compatibility)
- **Headless Chrome** (no visible browser window needed)

## Project Structure

```
src/
├── main/java/org/example/
│   └── stepdefinitions/
│       ├── SampleSteps.java            # Original sample step definitions
│       └── SolutionsHubSteps.java      # SolutionsHub test step definitions
├── main/resources/
│   └── log4j2.xml                      # Logging configuration
└── test/
    ├── java/org/example/runners/
    │   └── CucumberTest.java           # Cucumber test runner
    └── resources/org/example/features/
        └── solutionshub.feature        # 10 test scenarios
```

## Test Scenarios

| ID     | Test                              | Validates                          |
|--------|-----------------------------------|------------------------------------|
| TC_001 | Navigate to Solutions page        | Header nav -> `/catalog`           |
| TC_002 | Navigate to Blog page             | Header nav -> `/blog`              |
| TC_003 | Navigate to About page            | Header nav -> `/about`             |
| TC_004 | Verify homepage title             | Title contains "SolutionsHub"      |
| TC_005 | Verify homepage loads content     | Main section has links             |
| TC_006 | Navigate to Industries page       | Direct nav -> `/industries`        |
| TC_007 | Navigate to Financial Services    | Catalog filtering works            |
| TC_008 | Open a blog post                  | Blog article details load          |
| TC_009 | Verify About shows EPAM info      | Page contains "EPAM" text          |
| TC_010 | Check About page sections         | Page has structured sections       |

## Prerequisites

- Java 17 (e.g. `brew install openjdk@17`)
- Google Chrome installed

## How to Run

```bash
# Run all tests
./gradlew clean test

# Build without tests
./gradlew build -x test
```

Test reports are generated at `build/reports/tests/test/index.html`.
