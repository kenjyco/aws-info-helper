import click
import input_helper as ih
from aws_info_helper import EC2
from pprint import pprint


@click.command()
def main():
    """Get info about EC2 instances"""
    ec2 = EC2()
    print('Fetching info about EC2 instances...')
    ec2.show_instance_info()


if __name__ == '__main__':
    main()
