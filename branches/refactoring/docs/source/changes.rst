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

* addition of goflow.utils for custom management commands, decorators, logger, etc...

* better documentation..

Improved API
^^^^^^^^^^^^

* moved api into models and managers to make it more object oriented, still some way to go...

Improvement documentation system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* sphinx autodoc now working 
* add uml diagram of model (80%)

restructuring
^^^^^^^^^^^^^

- moved goflow.workflow.logger into goflow.utils.logger
- moved goflow.workflow.decorators into goflow.utils.decorators

Improved Logging Machinery
^^^^^^^^^^^^^^^^^^^^^^^^^^

- use custom log class for all logging (including event logging)

Bug Fixes
*********

* fixes here...

Backwards Incompatible Changes
******************************

* new api...

Version 0.51
++++++++++++

New Features
************

* Improved documentation based on leo-editor, Sphinx and epydoc.

Bug Fixes
*********

* a bug was found here.

Backwards Incompatible Changes
******************************

* api was cleaned up to make it more consistent.

