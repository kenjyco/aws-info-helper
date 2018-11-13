import boto3
import settings_helper as sh
import input_helper as ih
import dt_helper as dh
from pprint import pprint


get_setting = sh.settings_getter(__name__)
EC2_INSTANCE_KEYS = get_setting('EC2_INSTANCE_KEYS')


class EC2(object):
    def __init__(self, profile_name='default'):
        session = boto3.Session(profile_name=profile_name)
        self._ec2_client = session.client('ec2')
        self._ec2_resource = session.resource('ec2')

    def get_all_instances_full_data(self):
        """Get all instances with full data"""
        instances = []
        for x in self._ec2_client.describe_instances()['Reservations']:
            instances.extend(x['Instances'])
        return instances

    def get_all_instances_filtered_data(self):
        """Get all instances with filtered on EC2_INSTANCE_KEYS"""
        return [
            ih.filter_keys(instance, *EC2_INSTANCE_KEYS)
            for instance in self.get_all_instances_full_data()
        ]
