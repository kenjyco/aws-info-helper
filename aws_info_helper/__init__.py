import re
import os.path
import settings_helper as sh
import bg_helper as bh
from os import walk


get_setting = sh.settings_getter(__name__)
EC2_INSTANCE_KEYS = get_setting('EC2_INSTANCE_KEYS')
EC2_INSTANCE_INFO_FORMAT = get_setting('EC2_INSTANCE_INFO_FORMAT')

SSH_USERS = [
    'ec2-user',
    'ubuntu',
    'admin',
    'centos',
    'fedora',
    'root',
]


def get_profiles():
    """Get names of profiles from ~/.aws/credentials file"""
    cred_file = os.path.abspath(os.path.expanduser('~/.aws/credentials'))
    rx = re.compile(r'^\[([^\]]+)\]$')
    profiles = []
    text = ''
    try:
        with open(cred_file) as fp:
            text = fp.read()
    except FileNotFoundError:
        pass
    for line in re.split(r'\r?\n', text):
        match = rx.match(line)
        if match:
            profiles.append(match.group(1))
    return profiles


def find_local_pem(pem):
    """Given the name of pem file, find its absolute path in ~/.ssh"""
    pem = pem if pem.endswith('.pem') else pem + '.pem'
    dirname = os.path.abspath(os.path.expanduser('~/.ssh'))
    for dirpath, dirnames, filenames in walk(dirname, topdown=True):
        if pem in filenames:
            return os.path.join(dirpath, pem)


def do_ssh(ip, pem_file, user, command='', timeout=None, verbose=False):
    """Actually SSH to a server

    - ip: IP address
    - pem_file: absolute path to pem file
    - user: remote SSH user
    - command:
    """
    ssh_command = 'ssh -i {} -o "StrictHostKeyChecking no" {}@{}'
    cmd = ssh_command.format(pem_file, user, ip)
    if command:
        cmd = cmd + ' -t {}'.format(repr(command))
    if verbose:
        print(cmd)

    result = None
    if command:
        result = bh.run_output(cmd, timeout=timeout)
        if verbose:
            print(result)
    else:
        result = bh.run(cmd)
    return result


def determine_ssh_user(ip, pem_file, verbose=False):
    """Determine which AWS default user"""
    if verbose:
        print('\nDetermining SSH user for {}'.format(ip))
    for user in SSH_USERS:
        if verbose:
            print('  - trying {}'.format(user))
        output = do_ssh(ip, pem_file, user, 'ls', timeout=2, verbose=verbose)
        if 'Timeout' not in output and 'Permission denied' not in output:
            return user


from aws_info_helper.ec2 import EC2, AWS_EC2
