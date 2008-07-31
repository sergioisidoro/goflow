
def run_pushapp(self):
    '''run pushappplication on self (workitem)
    
    This replaces exec_push_application and provides
    the same functionality without eval
    
    examples are::
    
        def route_to_requester(workitem):
            "Simplest possible pushapp"
            return lambda: workitem.instance.user
    
        def route_to_user(workitem, username):
            "Route to user given a username"    
            return lambda: User.objects.get(username=username)
        
        class SimpleRouter:
            def __init__(self, workitem):
                self.workitem
            def __call__(self):
                return self.workitem.instance.user
        
    a parameter would look like::
        
        #this is the earlier version as a dict
        push_app_param = {'username': 'admin'} 
        
        in yaml:
            username: admin
        
    '''
    import yaml
    if not self.activity.process.enabled:
        raise error('process disabled', workitem)
    #TODO: this should be by pushapp.name not by pushapp.url
    appname = self.activity.push_application.url
    params_yaml = self.activity.pushapp_param
    # first try standard pushapps in goflow.workflow.pushapps
    
    try:
        modpath = 'goflow.workflow.pushapps'
        Router = get_class(modpath, appname)
    except ImportError, e:
        modpath = settings.WF_PUSH_APPS_PREFIX+'.'+appname
        try:
            Router = get_class(modpath, appname)
            try:
                if params_yaml:
                    params = yaml.load(params)
                    user = Router(workitem=self, **params)()
                    return user
                else:
                    user = Router(workitem=self)()
                    return user
            except AttributeError, e:
                log.error(e)
        except ImportError, e:
            log.error(e)
    self.fallout()
    return


def transition_condition(self, transition):
    '''safely evaluate the condition of a transition
    '''
    # the absence of a condition implies a True value
    if not transition.condition:
        return True

    try:
        result = rule(transition.condition, 
                      workitem=self, instance=self.instance)
        # boolean expression evaluation
        #if bool type:
        if type(result) == type(True):
            return result()
        #if string type:
        if type(result) == type(''):
            return instance.condition==result
    except Exception, v:
        pass




def eval_transition_condition(self, transition):
    '''
    evaluate the condition of a transition
    '''
    if not transition.condition:
        return True
    workitem = self # HACK!!! there's a dependency on 'workitem' in eval
                    # created a really perplexing bug for me )-:
    instance = self.instance
    try:
        result = eval(transition.condition)
        
        # boolean expr
        if type(result) == type(True):
            return result
        if type(result) == type(''):
            return (instance.condition==result)
    except Exception, v:
        return (instance.condition==transition.condition)

    return False


def exec_auto_application(self):
    '''
    creates a test auto application for activities that don't yet have applications
    :type workitem: WorkItem
    :rtype: bool
    '''
    try:
        if not self.activity.process.enabled:
            raise Exception('process %s disabled.' % self.activity.process.title)
        # no application: default auto app
        if not self.activity.application:
            return self.default_auto_app()
        
        func, args, kwargs = resolve(self.activity.application.get_app_url())
        params = self.activity.app_param
        # params values defined in activity override those defined in urls.py
        if params:
            params = eval('{'+params.lstrip('{').rstrip('}')+'}')
            kwargs.update(params)
        func(workitem=self , **kwargs)
        return True
    except Exception, v:
        log.error('execution wi %s:%s', self, v)
    return False
