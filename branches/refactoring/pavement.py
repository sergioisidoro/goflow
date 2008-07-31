import paver.doctools

options(
        setup=Bunch(
            name="GoFlow",
            packages=['goflow'],
            version="0.6",
            author="Eric Simmore",
            author_email="name@org.com"
         ),

        # documentation
        sphinx=Bunch(
            builddir="build",
            sourcedir="source"
        ),

)

@task
@needs(['generate_setup', 'minilib', 'setuptools.command.sdist'])
def sdist():
    """Overrides sdist to make sure that our setup.py is generated"""
    pass
