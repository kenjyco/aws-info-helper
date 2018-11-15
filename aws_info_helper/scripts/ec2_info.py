import click
import input_helper as ih
from aws_info_helper import EC2


@click.command()
def main():
    """Get info about EC2 instances"""
    ec2 = EC2()
    print('Fetching info about EC2 instances...')
    ec2.show_instance_info(cache=True)
    ih.start_ipython(ec2=ec2)


if __name__ == '__main__':
    main()
