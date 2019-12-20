# please install python if it is not present in the system
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='timeloop',
    version='1.0.3',
    packages=['timeloop'],
    license = 'MIT',
    description = 'An elegant way to run period tasks.',
    author = 'Ruggiero Santo',
    author_email = 'ruggiero.santo@gmail.com',
    keywords = ['tasks','jobs','periodic task','interval','periodic job', 'flask style', 'decorator', 'scheduler', 'scheduled fuction'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ruggiero-Santo/timeloop",
    include_package_data=True,
)
