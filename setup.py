from setuptools import setup

try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()

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
      long_description=read_md('README.md'),
      zip_safe=False)
