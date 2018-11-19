import click
import input_helper as ih
from aws_info_helper import EC2, AWS_EC2


@click.command()
@click.option(
    '--non-interactive', '-n', 'non_interactive', is_flag=True, default=False,
    help='Do not start an ipython session at the end'
)
@click.option(
    '--profile', '-p' 'profile', default='default',
    help='Name of AWS profile to use'
)
def main(**kwargs):
    """Update info in AWS_EC2 redis-helper collection"""
    ec2 = EC2(kwargs['profile'])
    ec2.update_collection()
    if kwargs['non_interactive'] is not True:
        ih.start_ipython(ec2=AWS_EC2)


if __name__ == '__main__':
    main()
