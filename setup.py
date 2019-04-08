from setuptools import setup, find_packages


setup(
    name='aws-info-helper',
    version='0.0.9',
    description='CLI helpers for AWS info gathering using Boto3',
    author='Ken',
    author_email='kenjyco@gmail.com',
    license='MIT',
    url='https://github.com/kenjyco/aws-info-helper',
    download_url='https://github.com/kenjyco/aws-info-helper/tarball/v0.0.9',
    packages=find_packages(),
    install_requires=[
        'boto3',
        'input-helper',
        'settings-helper',
        'dt-helper',
        'bg-helper',
        'click>=6.0',
    ],
    include_package_data=True,
    package_dir={'': '.'},
    package_data={
        '': ['*.ini'],
    },
    entry_points={
        'console_scripts': [
            'ah-info-ec2=aws_info_helper.scripts.ec2_info:main',
            'ah-collection-update-ec2=aws_info_helper.scripts.ec2_update_collection:main',
            'ah-ssh-command-ec2=aws_info_helper.scripts.ec2_ssh_command:main',
            'ah-info-route53=aws_info_helper.scripts.route53_info:main',
            'ah-collection-update-route53=aws_info_helper.scripts.route53_update_collection:main',
            'ah-collection-update-s3=aws_info_helper.scripts.s3_update_collection:main',
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
