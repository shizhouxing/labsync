from setuptools import setup

setup(
    name='labkit',
    version='0.1',
    description='Toolkit for development on university lab servers',
    author='Zhouxing Shi',
    author_email='zhouxingshichn@gmail.com',
    packages=['labkit'],
    install_requires=[
      'watchdog>=0.10',
      'flask>=1.1',
      'libsass>=0.20',
      'appdirs>=1.4'
    ],
    entry_points={
      'console_scripts': [
          'lab = labkit.main:cli_main'
      ],
    },    
    platforms=['any'],
    license='BSD',
)


