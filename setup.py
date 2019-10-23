from setuptools import setup

setup(
  name='acme-snap',
  version='0.1',
  author="MK",
  author_email='a@b.c',
  description="Acme-snap is a tool to manage AWS snapshots",
  license='GPLv3+',
  packages=['shotty'],
  url='https://github.com/M-i-k-a/acme-snap',
  install_requires=[
    'click',
    'boto3'
  ],
  entry_points='''
    [console_scripts]
    shotty=shotty.shotty:cli
  ''',
)