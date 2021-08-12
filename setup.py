from setuptools import setup

setup(
    name='labsync',
    version='0.1',
    description='Toolkit for synchronizing works with university lab servers',
    author='Zhouxing Shi',
    author_email='zhouxingshichn@gmail.com',
    packages=['labsync'],
    install_requires=[
      'watchdog>=0.10',
      'flask>=1.1',
      'appdirs>=1.4',
      'oslo.concurrency>=4.2',  
      'pydrive>=1.3'  ,
      'httplib2==0.15'  
    ],
    entry_points={
      'console_scripts': [
          'lab = labsync.main:cli_main'
      ],
    },    
    platforms=['any'],
    license='BSD',
)
