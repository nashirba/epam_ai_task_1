Feature: SolutionsHub Website Navigation Testing
  As a user of solutionshub.epam.com
  I want to verify that all main navigation tabs work correctly
  So that I can access all sections of the website

  Background:
    Given I open the browser in headless mode
    And I navigate to SolutionsHub homepage

  Scenario: TC_001 - Navigate to Solutions page
    When I click on "Solutions" in the header navigation
    Then the page URL should contain "/catalog"

  Scenario: TC_002 - Navigate to Blog page
    When I click on "Blog" in the header navigation
    Then the page URL should contain "/blog"

  Scenario: TC_003 - Navigate to About page
    When I click on "About" in the header navigation
    Then the page URL should contain "/about"

  Scenario: TC_004 - Verify homepage title
    Then the page title should contain "SolutionsHub"

  Scenario: TC_005 - Verify homepage loads content
    Then the main section should contain links

  Scenario: TC_006 - Navigate to Industries page
    When I navigate to the "/industries" page
    Then the page should contain text "Industries"

  Scenario: TC_007 - Navigate to Financial Services catalog
    When I navigate to the "/catalog/financial-services" page
    Then the page should contain text "Financial Services"

  Scenario: TC_008 - Open a blog post from Blog page
    When I click on "Blog" in the header navigation
    And I open the first article link on the page
    Then the item details page should load

  Scenario: TC_009 - Verify About page shows EPAM info
    When I click on "About" in the header navigation
    Then the page should contain text "EPAM"

  Scenario: TC_010 - Check About page has sections
    When I click on "About" in the header navigation
    Then the page should contain key sections
