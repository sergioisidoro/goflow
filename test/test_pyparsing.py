'''
This is an attempt to get an easy text-based syntax to specify workflows, the beginning of this were
initially inspired by dot-notation and the perl based Easy::Graph module.

pseudo BNF:

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
from pyparsing import Word, alphas, alphanums, QuotedString, Literal
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
    assert result.from_activity == 'activity1'
    assert result.transition_name == 'transition_name'
    assert result.to_activity == 'activity2'
    target = "activity1 --- transition_name [10 > var] --> activity2"
    result = sentence.parseString(target)
    condition = safe_eval(result.condition, var=15)
    print condition() # False
    assert not condition()

 

if __name__ == '__main__':
    test_parsing()
