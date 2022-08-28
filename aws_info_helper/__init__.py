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
except (ImportError, ModuleNotFoundError):
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


from aws_info_helper.ec2 import EC2, AWS_EC2
from aws_info_helper.route53 import Route53, AWS_ROUTE53
from aws_info_helper.s3 import S3, AWS_S3, AWS_S3_LAST_FILE
from aws_info_helper.parameter_store import ParameterStore
