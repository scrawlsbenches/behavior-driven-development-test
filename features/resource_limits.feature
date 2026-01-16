Feature: Resource Limits
  As a developer using Graph of Thought
  I want the graph to enforce resource limits
  So that I can prevent runaway computation

  Scenario: Max thoughts limit is enforced
    Given a config with max_thoughts 5
    And a graph with the config
    When I add 5 thoughts
    And I try to add another thought
    Then a ResourceExhaustedError should be raised
