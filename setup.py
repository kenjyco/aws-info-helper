from setuptools import setup, find_packages


with open('README.rst', 'r') as fp:
    long_description = fp.read()

with open('requirements.txt', 'r') as fp:
    requirements = fp.read().splitlines()

with open('requirements-redis-helper.txt', 'r') as fp:
    requirements_redis_helper = fp.read().splitlines()

setup(
    name='aws-info-helper',
    version='0.0.18',
    description='CLI helpers for AWS info gathering using Boto3',
    long_description=long_description,
    author='Ken',
    author_email='kenjyco@gmail.com',
    license='MIT',
    url='https://github.com/kenjyco/aws-info-helper',
    download_url='https://github.com/kenjyco/aws-info-helper/tarball/v0.0.18',
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
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
        'Intended Audience :: Developers',
    ],
    keywords=['aws', 'boto', 'helper']
)
