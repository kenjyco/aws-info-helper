from setuptools import setup, find_packages


with open('README.rst', 'r') as fp:
    long_description = fp.read()

with open('requirements.txt', 'r') as fp:
    requirements = fp.read().splitlines()

with open('requirements-redis-helper.txt', 'r') as fp:
    requirements_redis_helper = fp.read().splitlines()

setup(
    name='aws-info-helper',
    version='0.1.3',
    description='Helpers for working with Boto3 output and AWS resources ',
    long_description=long_description,
    author='Ken',
    author_email='kenjyco@gmail.com',
    license='MIT',
    url='https://github.com/kenjyco/aws-info-helper',
    download_url='https://github.com/kenjyco/aws-info-helper/tarball/v0.1.3',
    packages=find_packages(),
    install_requires=requirements,
    extras_require={
        'redis-helper': requirements_redis_helper,
    },
    include_package_data=True,
    package_dir={'': '.'},
    package_data={
        '': ['*.ini'],
    },
    entry_points={
        'console_scripts': [
            'ah-collection-update-ec2=aws_info_helper.scripts.ec2_update_collection:main',
            'ah-collection-update-route53=aws_info_helper.scripts.route53_update_collection:main',
            'ah-collection-update-s3=aws_info_helper.scripts.s3_update_collection:main',
            'ah-info-ec2=aws_info_helper.scripts.ec2_info:main',
            'ah-info-route53=aws_info_helper.scripts.route53_info:main',
            'ah-ssh-command-ec2=aws_info_helper.scripts.ec2_ssh_command:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
    ],
    keywords=['aws', 'boto', 'ec2', 's3', 'route53', 'cli', 'command-line', 'helper', 'kenjyco']
)
