import click
import aws_info_helper as ah
import input_helper as ih
from aws_info_helper.ec2 import INSTANCE_KEY_NAME_MAPPING


@click.command()
@click.option(
    '--find', '-f', 'find', default='',
    help='String with key:value pairs (separated by any of , ; |) for filtering instances'
)
@click.option(
    '--command', '-c', 'command', default='',
    help='Command string to pass to remote server(s) via SSH'
)
@click.option(
    '--timeout', '-t', 'timeout', type=click.INT,
    help='Number of seconds to wait before killing SSH command'
)
@click.option(
    '--verbose', '-v', 'verbose', is_flag=True, default=False,
    help='Show output'
)
@click.option(
    '--non-interactive', '-n', 'non_interactive', is_flag=True, default=False,
    help='Do not prompt/confirm matched instances before issuing remote command'
)
@click.option(
    '--profile', '-p', 'profile', default='default',
    help='Name of AWS profile to use'
)
def main(**kwargs):
    """For matching instances, issue a command on the instance via SSH"""
    ec2 = ah.EC2(kwargs['profile'])
    find = kwargs['find']
    command = kwargs['command']
    matched_instances = []
    local_pems = {}

    if not command:
        if kwargs['non_interactive']:
            print('No command specified')
            return
        else:
            command = ih.user_input('Enter remote command')
            if not command:
                print('No command specified')
                resp = ih.user_input('Do you want interactive SSH session(s)? (y/n)')
                if resp.lower().startswith('y') is False:
                    return

    if ah.AWS_EC2 is not None:
        ec2.update_collection()
        if not 'running' in find:
            find = find + ', status:running'
        matched_instances = ah.AWS_EC2.find(
            find,
            get_fields='name, status, pem, id, ip, sshuser',
            include_meta=False,
            limit=ah.AWS_EC2.size
        )
    else:
        instances = ec2.get_all_instances_filtered_data()
        if not 'running' in find:
            find = find + ', State__Name:running'
        matched_instances = [
            ih.rename_keys(
                ih.filter_keys(
                    instance,
                    'Tags__Value, State__Name, KeyName, InstanceId, PublicIpAddress'
                ),
                **INSTANCE_KEY_NAME_MAPPING
            )
            for instance in ih.find_items(instances, find)
        ]

    ih.sort_by_keys(matched_instances, 'name, ip')

    if kwargs['non_interactive'] is False:
        matched_instances = ih.make_selections(
            matched_instances,
            prompt='Select instances',
            item_format='{id} ({name}) at {ip} using {pem}',
            wrap=False
        )

    for instance in matched_instances:
        pem_name = instance['pem']
        ip = instance['ip']
        if not ip:
            continue
        if pem_name not in local_pems:
            pem_file = ah.find_local_pem(pem_name)
            if pem_file:
                local_pems[pem_name] = pem_file
            else:
                print('Could not find local pem file for {}'.format(repr(pem_name)))
                continue
        else:
            pem_file = local_pems[pem_name]

        sshuser = instance.get('sshuser')
        if not sshuser:
            sshuser = ah.determine_ssh_user(ip, pem_file)
        if not sshuser:
            print('Could not determine SSH user for {}'.format(repr(instance)))
            continue
        else:
            if ah.AWS_EC2:
                hash_id = ah.AWS_EC2.get_hash_id_for_unique_value(instance['id'])
                ah.AWS_EC2.update(hash_id, sshuser=sshuser)

        if kwargs['verbose']:
            print('--------------------------------------------------')
            print(
                '\nInstance {} ({}) at {} with pem {} and user {}\n'.format(
                    instance['id'], instance['name'], ip, pem_name, sshuser
                )
            )
        ah.do_ssh(ip, pem_file, sshuser, command, kwargs['timeout'], kwargs['verbose'])


if __name__ == '__main__':
    main()

