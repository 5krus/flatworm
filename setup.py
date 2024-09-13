from setuptools import setup, find_packages

setup(
    name='auto_git',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'GitPython',
        'watchdog',
        'tkinter',
        'keyring',
        'schedule'
    ],
    entry_points={
        'console_scripts': [
            'auto_git = main:main',
        ],
    },
    package_data={
        '': ['config/config.json'],
    },
)