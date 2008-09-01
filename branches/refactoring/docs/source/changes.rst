.. rst3: filename: changes.rst

.. _changes:

==========================
Changes
==========================


.. contents::

Version 0.6 (refactored branch)
+++++++++++++++++++++++++++++++

New Features
************

* new more 'object-oriented' api using model classes and managers

* addition of goflow.tools for custom management commands, decorators, logger, etc...

* better documentation..

Improved API
^^^^^^^^^^^^

* unification of the goflow.runtime and goflow.workflow into goflow.workflow

* removed incomplete modules to reduce size of code

* more object oriented simplified api, still some way to go...

* added goflow.workflow.errors module for goflow related exceptions / msgs

* moved goflow.workflow.logger into goflow.tools.logger

* moved goflow.workflow.decorators into goflow.tools.decorators

Improved documentation system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* sphinx autodoc now working 

* add uml diagram of model (80%)

* more autodoc compatible doctests / doctrings

Improved Logging Machinery
^^^^^^^^^^^^^^^^^^^^^^^^^^

- use custom log class for all logging (including event logging)

More tests
^^^^^^^^^^

* we are trying to provide extensive tests of all goflow functionality, with a preference for doctests.

Safe Evaluation of Expressions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* introduced safe_eval and dynamic object imports in goflow.tools

Bug Fixes
*********

* synchronization with Django trunk 1.0

Backwards Incompatible Changes
******************************

* given the completely new api this branched version is not backwards compatible at all with goflow version 0.5x

