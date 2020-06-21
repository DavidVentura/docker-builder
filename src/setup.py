from setuptools import setup

setup(name='builder',
        version='0.1',
        description='',
        url='',
        author='',
        author_email='',
        license='',
        packages=['builder'],
        zip_safe=False,
        entry_points={
            'console_scripts': [
                'webserver=builder.webserver:start',
                'worker=builder.worker:start',
                ],
            },
        )
