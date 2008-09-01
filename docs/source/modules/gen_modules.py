from Cheetah.Template import Template

template ='''
.. _${mod.name}:

:mod:`${mod.name}` -- ${mod.synopsis} 
================================================================================

.. automodule:: ${mod.name} 
   :synopsis: ${mod.synopsis}

'''

template_ ='''
.. _${mod.name}:

:mod:`${mod.name}` -- ${mod.synopsis} 
================================================================================

..  automodule:: ${mod.name} 
    :members:
    :undoc-members:
    :inherited-members:
'''

lst = [
    ("goflow.rst","primary module containing other goflow submodules."),
    ("goflow.graphics.rst","early goflow graphics module"),
    ("goflow.graphics.models.rst","datamodels for graphics processing"),
    ("goflow.graphics.views.rst","goflow graphics views"),
    ("goflow.graphics.urls_admin.rst","goflow graphics custom admin interface"),
    ("goflow.runtime.rst","goflow runtime"),
    ("goflow.runtime.api.rst","goflow runtime api"),
    ("goflow.runtime.forms.rst","goflow runtime forms"),
    ("goflow.runtime.models.rst","goflow runtime models"),
    ("goflow.runtime.views.rst","goflow runtime views"),
    ("goflow.runtime.urls.rst","goflow runtime urls"),
    ("goflow.runtime.urls_admin.rst","goflow runtime custom admin interface"),
    ("goflow.workflow.rst","goflow core workflow functionality"),
    ("goflow.workflow.api.rst","key functions for workflow management"),
    ("goflow.workflow.applications.rst","key application function for workflow mgmt"),
    ("goflow.tools.decorators.rst","goflow decorator library"),

    ("goflow.workflow.forms.rst","goflow form utility functions"),
    ("goflow.workflow.logger.rst","logging capability"),
    ("goflow.workflow.models.rst","workflow models"),
    ("goflow.workflow.notification.rst","workflow notification library"),
    ("goflow.workflow.pushapps.rst","example goflow pushapps"),
    ("goflow.workflow.views.rst","views for goflow worklow module"),
]


def main():
    results=[]
    for fname, synopsis in lst:
        mod = dict(name=fname[:-4], file=fname, synopsis=synopsis)
        out = file(fname, 'w')
        out.write(str(Template(template, searchList=[dict(mod=mod)])))
        out.close()

    


if __name__ == '__main__':
    main()

