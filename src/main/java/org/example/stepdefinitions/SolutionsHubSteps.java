package org.example.stepdefinitions;

import io.cucumber.java.AfterAll;
import io.cucumber.java.BeforeAll;
import io.cucumber.java.en.And;
import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;
import java.util.List;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class SolutionsHubSteps {
    private static WebDriver driver;
    private static WebDriverWait wait;

    private static final String BASE_URL = "https://solutionshub.epam.com";

    @BeforeAll
    public static void setUp() {
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless=new");
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        options.addArguments("--window-size=1920,1080");
        options.addArguments("--disable-gpu");
        driver = new ChromeDriver(options);
        driver.manage().timeouts().pageLoadTimeout(Duration.ofSeconds(30));
        wait = new WebDriverWait(driver, Duration.ofSeconds(20));
    }

    @Given("I open the browser in headless mode")
    public void iOpenTheBrowserInHeadlessMode() {
        // Browser is already open via @BeforeAll
    }

    @And("I navigate to SolutionsHub homepage")
    public void iNavigateToSolutionsHubHomepage() {
        loadPageWithRetry(BASE_URL);
    }

    @When("I click on {string} in the header navigation")
    public void iClickOnInTheHeaderNavigation(String tabName) {
        WebElement navLink = wait.until(ExpectedConditions.elementToBeClickable(
                By.xpath("//header//a[normalize-space(.)='" + tabName + "']")));
        navLink.click();
        waitForPageLoad();
    }

    @When("I navigate to the {string} page")
    public void iNavigateToThePage(String path) {
        loadPageWithRetry(BASE_URL + path);
    }

    @Then("the page URL should contain {string}")
    public void thePageUrlShouldContain(String expectedPath) {
        String currentUrl = driver.getCurrentUrl().toLowerCase();
        assertTrue("Expected URL to contain '" + expectedPath + "' but was: " + currentUrl,
                currentUrl.contains(expectedPath.toLowerCase()));
    }

    @Then("the main section should contain links")
    public void theMainSectionShouldContainLinks() {
        List<WebElement> content = driver.findElements(By.cssSelector("main a[href]"));
        assertFalse("Expected links to be present in main section", content.isEmpty());
    }

    @Then("the page should contain text {string}")
    public void thePageShouldContainText(String expectedText) {
        String pageSource = driver.getPageSource();
        assertTrue("Expected page to contain text '" + expectedText + "'",
                pageSource.contains(expectedText));
    }

    @And("I open the first article link on the page")
    public void iOpenTheFirstArticleLinkOnThePage() {
        List<WebElement> items = wait.until(ExpectedConditions.presenceOfAllElementsLocatedBy(
                By.cssSelector("main a[href]")));
        assertFalse("Expected at least one link to be present", items.isEmpty());
        String currentUrl = driver.getCurrentUrl();
        for (WebElement item : items) {
            String href = item.getAttribute("href");
            if (href != null && !href.isEmpty() && !href.equals("#")
                    && href.startsWith(BASE_URL) && !href.equals(currentUrl)
                    && href.length() > currentUrl.length()) {
                driver.get(href);
                waitForPageLoad();
                return;
            }
        }
        // If no matching link found, click on first valid link
        for (WebElement item : items) {
            String href = item.getAttribute("href");
            if (href != null && href.startsWith("http") && !href.equals(currentUrl)) {
                driver.get(href);
                waitForPageLoad();
                return;
            }
        }
    }

    @Then("the item details page should load")
    public void theItemDetailsPageShouldLoad() {
        String currentUrl = driver.getCurrentUrl();
        assertTrue("Expected navigation to a details page but URL is: " + currentUrl,
                currentUrl.length() > BASE_URL.length() + 1);
        List<WebElement> content = driver.findElements(By.cssSelector("main, article, h1, h2"));
        assertFalse("Expected content to be present on the details page", content.isEmpty());
    }

    @Then("the page title should contain {string}")
    public void thePageTitleShouldContain(String expectedText) {
        String title = driver.getTitle();
        assertTrue("Expected page title to contain '" + expectedText + "' but was: '" + title + "'",
                title.contains(expectedText));
    }

    @Then("the page should contain key sections")
    public void thePageShouldContainKeySections() {
        List<WebElement> sections = driver.findElements(By.cssSelector("section, h1, h2, h3"));
        assertFalse("Expected structured sections on the page", sections.isEmpty());
    }

    @AfterAll
    public static void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    private void loadPageWithRetry(String url) {
        int maxRetries = 3;
        for (int i = 0; i < maxRetries; i++) {
            try {
                driver.get(url);
                wait.until(ExpectedConditions.presenceOfElementLocated(By.tagName("main")));
                waitForPageLoad();
                return;
            } catch (Exception e) {
                if (i == maxRetries - 1) {
                    throw e;
                }
                waitForPageLoad();
            }
        }
    }

    private void waitForPageLoad() {
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
