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
            'Flask-RESTful==0.3.8',
            'Flask==1.1.1',
            'boto3==1.14.7',
            'docker==4.2.1',
            'dynaconf==2.2.3',
            'gitpython==3.1.3',
            'requests==2.24.0',
            'waitress==1.4.3',
            ],
        extras_require={
            'build':
            ['shiv==0.1.2']
            })
