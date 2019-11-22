import re
import os.path
import boto3
import settings_helper as sh
import bg_helper as bh
from os import walk
from botocore.exceptions import EndpointConnectionError, ClientError, ProfileNotFound
try:
    import redis_helper as rh
    from redis import ConnectionError as RedisConnectionError
except ImportError:
    AWS_IP = None
else:
    try:
        AWS_IP = rh.Collection(
            'aws',
            'ip',
            index_fields='profile, ip, name, source, instance',
            reference_fields='instance--aws:ec2',
            insert_ts=True
        )
    except RedisConnectionError:
        AWS_IP = None


get_setting = sh.settings_getter(__name__)
EC2_INSTANCE_KEYS = get_setting('EC2_INSTANCE_KEYS')
EC2_INSTANCE_INFO_FORMAT = get_setting('EC2_INSTANCE_INFO_FORMAT')
EC2_ADDRESS_KEYS = get_setting('EC2_ADDRESS_KEYS')
ROUTE53_ZONE_KEYS = get_setting('ROUTE53_ZONE_KEYS')
ROUTE53_RESOURCE_KEYS = get_setting('ROUTE53_RESOURCE_KEYS')
ROUTE53_RESOURCE_INFO_FORMAT = get_setting('ROUTE53_RESOURCE_INFO_FORMAT')
IP_RX = re.compile(r'(?:\d{1,3}\.)+\d{1,3}')
SSH_FAILED_OUTPUT_RX = re.compile(r'.*(Timeout|Permission denied|Connection closed by|Connection timed out).*', re.DOTALL)

SSH_USERS = [
    'ec2-user',
    'ubuntu',
    'admin',
    'centos',
    'fedora',
    'root',
]


def get_session(profile_name='default'):
    """Return a boto3.Session instance for profile"""
    try:
        session = boto3.Session(profile_name=profile_name)
    except ProfileNotFound:
        if profile_name == 'default':
            session = boto3.Session()
        else:
            raise
    return session


def client_call(client, method_name, main_key='', **kwargs):
    """Call a boto client method and return retrieved data

    - client: boto3.Session.client instance
    - method_name: name of the client method to execute
    - main_key: the name of the main top-level key in the response that has the
      actual relevant info
    - kwargs: any keyword args that need to be passed to the client method
    """
    results = []
    try:
        results = getattr(client, method_name)(**kwargs)
    except (EndpointConnectionError, ClientError) as e:
        print(repr(e))
    else:
        if main_key:
            results = results.get(main_key)
    return results


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
    - command: an optional command to run on the remote server
        - if a command is specified, it will be run on the remote server and
          the output will be returned
        - if no command is specified, the SSH session will be interactive
    """
    ssh_command = 'ssh -i {} -o "StrictHostKeyChecking no" -o ConnectTimeout=2 {}@{}'
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
        if not SSH_FAILED_OUTPUT_RX.match(output):
            return user


from aws_info_helper.ec2 import EC2, AWS_EC2
from aws_info_helper.route53 import Route53, AWS_ROUTE53
from aws_info_helper.s3 import S3, AWS_S3, AWS_S3_LAST_FILE
from aws_info_helper.parameter_store import ParameterStore
