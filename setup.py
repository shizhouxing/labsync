from setuptools import setup, find_packages

setup(
    name='labsync',
    version='0.4.1',
    description='Toolkit for research on lab servers',
    author='Zhouxing Shi',
    author_email='zhouxingshichn@gmail.com',
    packages=find_packages(),
    install_requires=[
      'watchdog>=0.10',
      'flask>=2.3',
      'appdirs>=1.4',
      'oslo.concurrency>=4.2',
      'pydrive2>=1.15',
      'httplib2>=0.22',
      'google_api_core==2.11.1',
      'google_auth>=2.25.0',
      'gpustat>=1.1',
      'termcolor>=2.4.0',
      'huggingface_hub>=0.33.0',
      'datasets>=4.0.0'
    ],
    url='https://github.com/shizhouxing/labsync',
    entry_points={
      'console_scripts': [
          'lab = labsync.main:cli_main'
      ],
    },
    python_requires=">=3.10",
    license='GNU GPL v3',
)
