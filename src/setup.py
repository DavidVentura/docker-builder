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
                ],
            },
        install_requires=[
            'Flask==1.1.1',
            'Flask-RESTful==0.3.8',
            'waitress==1.4.3',
            'dynaconf',
            'requests',
            'gitpython',
            ],
        extras_require={
            'dev':
            ['shiv==0.1.2']
            })
