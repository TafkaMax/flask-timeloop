# please install python if it is not present in the system
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='flask-timeloop',
    version='1.0.0',
    packages=['timeloop'],
    license = 'MIT',
    description = 'An elegant way to run period tasks.',
    author = 'Taavi Ansper',
    author_email = 'taavi.ansperr@gmail.com',
    keywords = ['tasks','jobs','periodic task','interval','periodic job', 'flask style', 'decorator', 'scheduler', 'scheduled fuction'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TafkaMax/timeloop",
    include_package_data=True,
)
