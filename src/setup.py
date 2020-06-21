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
        install_requires=[
            'boto3==1.14.7',
            'docker==4.2.1',
            'dynaconf==2.2.3',
            'flask-api==2.0',
            'flask==1.1.1',
            'gitpython==3.1.3',
            'jsonschema==3.2.0',
            'redis==3.5.3',
            'requests==2.24.0',
            'rq==1.4.2',
            'typing-extensions==3.7.4.2',
            'waitress==1.4.3',
            'wheel',
            ],
        extras_require={
            'build':
            ['shiv==0.1.2']
            })
