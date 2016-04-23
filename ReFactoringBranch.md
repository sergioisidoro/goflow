# The Refactoring Branch #

Essentially this branch is an attempt to deliver the same functionality as the 0.50 trunk version but with a more maintainable and better documented codebase.

This is also an opportunity to experiment with API changes without touching the trunk.


# Details #

  * moved goflow.workflow.logger into goflow.common.logger
  * moved goflow.workflow.decorators into goflow.common.decorators
  * improved Logging Machinery
  * moved api into models and managers to make it more object oriented, still some way to go...
  * try to minimize eval use or at least render it safe.
  * Add documentation system based on sphinx to collect source and non-source docs
  * add uml diagram of model (80%)