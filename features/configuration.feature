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

  # ===========================================================================
  # Edge Cases and Validation (TODO: Implement step definitions)
  # ===========================================================================

  @wip
  Scenario: Config with zero max_depth is invalid
    Given a config with max_depth 0
    When I validate the config
    Then there should be at least 1 validation issue
    And the issue should mention "max_depth"

  @wip
  Scenario: Config with extremely large values is accepted
    Given a configuration dictionary with:
      | key          | value     |
      | max_depth    | 1000000   |
      | max_thoughts | 10000000  |
    When I create a config from the dictionary
    Then the config should have max_depth 1000000

  @wip
  Scenario: Missing required fields use defaults
    Given an empty configuration dictionary
    When I create a config from the dictionary
    Then the config should have default values
    And max_depth should be greater than 0
    And max_thoughts should be greater than 0
