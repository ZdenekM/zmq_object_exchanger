from setuptools import setup

setup(name='zmq_object_exchanger',
      version='0.1',
      description='Simple and lightweight framework for exchanging Python objects over network.',
      url='https://github.com/ZdenekM/zmq_object_exchanger',
      author='Zdenek Materna',
      author_email='zdenek.materna@gmail.com',
      license='LGPL',
      packages=['zmq_object_exchanger'],
      install_requires=[
          'pyzmq',
      ],
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
