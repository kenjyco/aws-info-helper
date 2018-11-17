import click
import input_helper as ih
from aws_info_helper import EC2, AWS_EC2


@click.command()
def main():
    """Update info in AWS_EC2 redis-helper collection"""
    ec2 = EC2()
    print('Updating info in AWS_EC2 redis-helper collection...')
    ec2.update_collection()
    ih.start_ipython(ec2=AWS_EC2)


if __name__ == '__main__':
    main()
