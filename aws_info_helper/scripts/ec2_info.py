import click
import input_helper as ih
from aws_info_helper import EC2
from pprint import pprint


@click.command()
def main():
    """Get info about EC2 instances"""
    ec2 = EC2()
    print('Fetching info about EC2 instances...')
    instances = ec2.get_all_instances_filtered_data()
    pprint(instances)


if __name__ == '__main__':
    main()
