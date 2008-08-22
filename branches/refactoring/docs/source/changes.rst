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

* addition of goflow.common for custom management commands, decorators, logger, etc...

* better documentation..

Improved API
^^^^^^^^^^^^

* removed incomplete modules to reduce size of code

* moved api into models and managers to make it more object oriented, still some way to go...

* added goflow.common.errors module for goflow related exceptions / msgs

* change goflow.instances to goflow.runtime: this change was simply to improve understanding of the differences between goflow.runtime (dynamic model) and goflow.workflow (static model), I felt 'instances' was too generic

* moved goflow.workflow.logger into goflow.common.logger

* moved goflow.workflow.decorators into goflow.common.decorators

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

* introduced safe_eval and dynamic object imports in goflow.common

Bug Fixes
*********

* synchronization with Django trunk 1.0

Backwards Incompatible Changes
******************************

* given the completely new api this branched version is not backwards compatible at all with goflow version 0.5x

