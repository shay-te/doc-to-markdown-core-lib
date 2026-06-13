import os

import setuptools

from setuptools import find_namespace_packages, setup
from pip._internal.network.session import PipSession
from pip._internal.req import parse_requirements

dir_path = os.path.dirname(os.path.realpath(__file__))


def _read_requirements(name):
    install_reqs = parse_requirements(os.path.join(dir_path, name), session=PipSession)
    try:
        return [str(ir.req) for ir in install_reqs]
    except Exception:
        install_reqs = parse_requirements(os.path.join(dir_path, name), session=PipSession)
        return [str(ir.requirement) for ir in install_reqs]


requirements = _read_requirements('requirements.txt')

packages1 = setuptools.find_packages()
packages2 = find_namespace_packages(include=['hydra_plugins.*'])
packages = list(set(packages1 + packages2))

with open('README.md', 'r') as fh:
    long_description = fh.read()

    setup(
        name='doc_to_markdown_core_lib',
        version='0.1.0',
        author='doc-to-markdown-core-lib contributors',
        author_email='',
        description='Multi-extractor document-to-markdown conversion core-lib with candidate voting',
        long_description=long_description,
        long_description_content_type='text/markdown',
        url='',
        packages=packages,
        license='MIT',
        install_requires=requirements,
        include_package_data=True,
        python_requires='>=3.7',
    )
