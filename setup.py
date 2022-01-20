from setuptools import setup


# access readme for long description
def readme():
    with open('README.md') as file:
        return file.read()


setup(
    name='grive',  # name of the program
    version='1.0.0',  # current version
    description='A command-line client for Google Drive for Linux',
    long_description=readme(),
    classifiers=[
        'Development Status :: 1 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: POSIX :: Linux',
        'Topic :: Utilities',
      ],
    keywords='Google Drive client Linux Python',
    url='https://github.com/hoangnv-bkhn/grive',
    author='Tokyo Team',
    author_email='tokyo.example@gmail.com',
    license='MIT',
    packages=['grive'],  # folders to be included
    include_package_data=True,
    install_requires=[
        'pydrive',
        'python-crontab',
        'future',
        'pyperclip',
        'prettytable',
        'google',
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
        'console_progressbar'
      ],
    dependency_links=[],
    entry_points={
        'console_scripts': ['grive=grive.main:main']
    },
    zip_safe=False)
