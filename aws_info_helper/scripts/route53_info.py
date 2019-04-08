import click
import input_helper as ih
from aws_info_helper import Route53


@click.command()
@click.option(
    '--non-interactive', '-n', 'non_interactive', is_flag=True, default=False,
    help='Do not start an ipython session at the end'
)
@click.option(
    '--profile', '-p', 'profile', default='default',
    help='Name of AWS profile to use'
)
def main(**kwargs):
    """Get info about Route53 resources"""
    route53 = Route53(kwargs['profile'])
    route53.show_resource_info(cache=True)
    if kwargs['non_interactive'] is not True:
        ih.start_ipython(route53=route53)


if __name__ == '__main__':
    main()
