import click
import aws_info_helper as ah
import bg_helper as bh
import input_helper as ih
from aws_info_helper.ec2 import INSTANCE_KEY_NAME_MAPPING


@click.command()
@click.option(
    '--find', '-f', 'find', default='',
    help='Comma-separated string of values to filter instances by (name/id/ip)'
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
    '--quiet', '-q', 'quiet', is_flag=True, default=False,
    help='Do not show output'
)
@click.option(
    '--non-interactive', '-n', 'non_interactive', is_flag=True, default=False,
    help='Do not prompt/confirm matched instances before issuing remote command'
)
@click.option(
    '--private-ip', '-P', 'private_ip', is_flag=True, default=False,
    help='SSH using private IP instead of public IP'
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
    use_private_ip = kwargs['private_ip']
    matched_instances = []
    local_pems = bh.tools.ssh_pem_files()

    if not command:
        if kwargs['non_interactive']:
            print('No command specified')
            return
        else:
            command = ih.user_input('Enter remote command')
            if not command:
                print('No command specified')
                resp = ih.user_input('Do you want an interactive SSH session(s)? (y/n)')
                if resp.lower().startswith('y') is False:
                    return

    if ah.AWS_EC2 is not None:
        ec2.update_collection()
        running_instances = ah.AWS_EC2.find(
            'status:running',
            get_fields='name, status, pem, id, ip, ip_private, sshuser',
            include_meta=False,
            limit=ah.AWS_EC2.size
        )
    else:
        instances = ec2.get_all_instances_filtered_data()
        running_instances = [
            ih.rename_keys(
                ih.filter_keys(
                    instance,
                    'Tags__Value, State__Name, KeyName, InstanceId, PublicIpAddress, PrivateIpAddress'
                ),
                **INSTANCE_KEY_NAME_MAPPING
            )
            for instance in ih.find_items(instances, 'State__Name:running')
        ]

    for term in ih.string_to_list(find):
        for item in ih.find_items(running_instances, 'name:${}'.format(term)):
            if item not in matched_instances:
                matched_instances.append(item)
        for item in ih.find_items(running_instances, 'id:${}'.format(term)):
            if item not in matched_instances:
                matched_instances.append(item)
        for item in ih.find_items(running_instances, 'ip:${}'.format(term)):
            if item not in matched_instances:
                matched_instances.append(item)
        for item in ih.find_items(running_instances, 'ip_private:${}'.format(term)):
            if item not in matched_instances:
                matched_instances.append(item)
    if not find:
        matched_instances = running_instances

    ih.sort_by_keys(matched_instances, 'name, ip')

    # # Uncomment and modify if you ever need to use a .pem file that
    # # is different than what AWS thinks it should be
    # for i, instance in enumerate(matched_instances):
    #     if instance.get('pem', '') == 'old-pem':
    #         matched_instances[i]['pem'] = 'new-pem'

    if kwargs['non_interactive'] is False:
        matched_instances = ih.make_selections(
            matched_instances,
            prompt='Select instances',
            item_format='{id} ({name}) at {ip} ({ip_private}) using {pem}',
            wrap=False
        )

    for instance in matched_instances:
        pem_name = instance['pem']
        ip = instance['ip'] if not use_private_ip else instance['ip_private']
        if not ip:
            continue
        pem_file = local_pems.get(pem_name)
        if not pem_file:
            print('Could not find {} pem in ~/.ssh for {}.'.format(repr(pem_name), repr(instance)))
            continue

        sshuser = instance.get('sshuser')
        if not sshuser:
            sshuser = bh.tools.ssh_determine_aws_user_for_server(ip, pem_file)
        if not sshuser and not kwargs['quiet']:
            print('--------------------------------------------------')
            print('\nCould not determine SSH user for {}'.format(repr(instance)))
            continue
        else:
            if ah.AWS_EC2:
                hash_id = ah.AWS_EC2.get_hash_id_for_unique_value(instance['id'])
                ah.AWS_EC2.update(hash_id, sshuser=sshuser)

        if not kwargs['quiet']:
            print('--------------------------------------------------')
            print(
                '\nInstance {} ({}) at {} with pem {} and user {}\n'.format(
                    instance['id'], instance['name'], ip, pem_name, sshuser
                )
            )

        bh.tools.ssh_to_server(ip, user=sshuser, pem_file=pem_file, command=command, timeout=kwargs['timeout'], verbose=not kwargs['quiet'])


if __name__ == '__main__':
    main()

