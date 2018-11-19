import re
import os.path
import settings_helper as sh


get_setting = sh.settings_getter(__name__)
EC2_INSTANCE_KEYS = get_setting('EC2_INSTANCE_KEYS')
EC2_INSTANCE_INFO_FORMAT = get_setting('EC2_INSTANCE_INFO_FORMAT')


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
