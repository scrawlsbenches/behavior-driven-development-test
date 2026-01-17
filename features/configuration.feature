@core @config @critical
Feature: Configuration
  As a developer using Graph of Thought
  I want to configure the graph behavior
  So that I can customize it for different use cases

  Scenario: Loading configuration from dictionary
    Given a configuration dictionary with:
      | key          | value |
      | allow_cycles | True  |
      | max_depth    | 15    |
      | max_thoughts | 500   |
      | beam_width   | 5     |
    When I create a config from the dictionary
    Then the config should have allow_cycles True
    And the config should have max_depth 15
    And the config should have max_thoughts 500
    And the config should have beam_width 5

  Scenario: Validating invalid configuration
    Given a config with max_thoughts -1
    And the config has beam_width 0
    When I validate the config
    Then there should be at least 2 validation issues

  Scenario: Configuration JSON serialization
    Given a config with max_depth 25
    When I serialize the config to JSON
    And I deserialize the config from JSON
    Then the restored config should have max_depth 25
