'''
This is an attempt to get an easy text-based syntax to specify workflows, the beginning of this were
initially inspired by dot-notation and the perl based Easy::Graph module.

BNF:

    identifier      :: group of alphabetic characters
    from_activity   :: identifier
    to_activity     :: identifier
    transition_name :: identifier
    condition       :: [expression]
    from_relation   :: '---'
    to_relation     :: '-->'
    sentence        :: from_activity from_relation transition_name condition to_relation to_activity

the general syntax is as follows::

    activity1 --- transition_name [transition_condition] --> activity2

an example of this:

    start      --- send_to_approval   [OK: Forward to supervisor] --> end
    start      --- send_to_refinement [Denied: Back to requestor] --> refinement
    approval   --- request_approved   [OK: Forward to secretary]  --> updatehr
    approval   --- not_approved       [Denied: Back to requestor] --> refinement
    refinement --- re_request         [Re-request]                --> start
    refinement --- cancel_request     [Withdraw request]          --> end
    updatehr   --- tell_employee      [tell_employee]             --> end


How should I define a transition condition ?
--------------------------------------------

transitions have a condition attribute: it is a python expression that returns a boolean. 
The only variables that can be used in the boolean expression are instance and workitem. 

Examples:

    * OK: the user has pushed the OK button
    * instance.condition == "OK": the user has pushed the OK button
    * workitem.timeout(delay=5, unit='days'): the task is waiting for 5 days or more (NYI but soon)

'''

from pyparsing import *
from goflow.common import safe_eval

identifier      = Word( alphas+"_", alphanums+"_" )
from_activity   = identifier.setResultsName('from_activity')
to_activity     = identifier.setResultsName('to_activity')
transition_name = identifier.setResultsName('transition_name')
condition       = QuotedString(quoteChar='[', endQuoteChar=']').setResultsName('condition')
from_relation   = Literal("---").suppress()
to_relation     = Literal("-->").suppress()
sentence        = from_activity + from_relation + transition_name + condition + to_relation + to_activity

def test_parsing():
    workflow = '''
    start      --- send_to_approval   [OK: Forward to supervisor] --> end
    start      --- send_to_refinement [Denied: Back to requestor] --> refinement
    approval   --- request_approved   [OK: Forward to secretary]  --> updatehr
    approval   --- not_approved       [Denied: Back to requestor] --> refinement
    refinement --- re_request         [Re-request]                --> start
    refinement --- cancel_request     [Withdraw request]          --> end
    updatehr   --- tell_employee      [tell_employee]             --> end
    '''
    
    target = "activity1 --- transition_name [10 > var] --> activity2"
    result = sentence.parseString(target)
    condition = safe_eval(result.condition, var=5)
    print condition() # True
    assert condition()
    target = "activity1 --- transition_name [10 > var] --> activity2"
    result = sentence.parseString(target)
    condition = safe_eval(result.condition, var=15)
    print condition() # False
    assert not condition()


def eval_transition_condition(transition):
    # the absence of a condition implies a True value
    if not transition.condition:
        return True
    try:
        # boolean expression evaluation
        result = safe_eval(transition.condition, 
                      workitem=self, instance=self.instance)()
        #if bool type:
        if type(result) == type(True):
            return result
        #elif string type:
        elif type(result) == type(''):
            return (self.instance.condition==result)
    except Exception, v:
        return (self.instance.condition==transition.condition)
    # otherwise
    return False


def eval_tc(transition, instance_condition=None):
    if not transition.condition:
        print 'transition.condition'
        return True
    try:
        result = safe_eval(transition.condition)()
        if type(result) == type(True):
            print 'type(result) == type(True)'
            return result
        if type(result) == type(''):
            print 'type(result) == type('')'
            return (instance_condition==transition.condition)
    except NameError, e:
        return (instance_condition==transition.condition)
    return

def test_eval_transition_condition():
    class Transition:
        def __init__(self, condition):
            self.condition = condition
    t1 = Transition('OK')
    t2 = Transition('instance.condition == "OK"')
    t3 = Transition("workitem.timeout(delay=5, unit='days')")
    print eval_tc(t1, instance_condition="OK")
    print eval_tc(t2, instance_condition="OK")
    
    
if __name__ == '__main__':
    test_eval_transition_condition()
