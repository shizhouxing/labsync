from setuptools import setup, find_packages

setup(
    name='labsync',
    version='0.2',
    description='Toolkit for synchronizing works with remote servers',
    author='Zhouxing Shi',
    author_email='zhouxingshichn@gmail.com',
    packages=find_packages(),
    install_requires=[
      'watchdog>=0.10',
      'flask>=1.1',
      'appdirs>=1.4',
      'oslo.concurrency>=4.2',
      'pydrive2>=1.15',
      'httplib2==0.15',
    ],
    url='https://github.com/shizhouxing/labsync',
    entry_points={
      'console_scripts': [
          'lab = labsync.main:cli_main'
      ],
    },
    python_requires=">=3.7",
    license='GNU GPL v3',
)
