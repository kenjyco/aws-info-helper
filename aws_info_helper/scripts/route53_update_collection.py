import click
import input_helper as ih
from aws_info_helper import Route53, AWS_ROUTE53, AWS_IP, get_profiles


@click.command()
@click.option(
    '--non-interactive', '-n', 'non_interactive', is_flag=True, default=False,
    help='Do not start an ipython session at the end'
)
@click.option(
    '--all', '-a', 'all', is_flag=True, default=False,
    help='Update info from all profiles found in ~/.aws/credentials'
)
@click.option(
    '--profile', '-p', 'profile', default='default',
    help='Name of AWS profile to use'
)
def main(**kwargs):
    """Update info in AWS_ROUTE53 and AWS_IP redis-helper collections"""
    if kwargs['all'] is True:
        for profile in get_profiles():
            route53 = Route53(profile)
            route53.update_collection()
    else:
        route53 = Route53(kwargs['profile'])
        route53.update_collection()
    if kwargs['non_interactive'] is not True:
        ih.start_ipython(route53=AWS_ROUTE53, ip=AWS_IP)


if __name__ == '__main__':
    main()
