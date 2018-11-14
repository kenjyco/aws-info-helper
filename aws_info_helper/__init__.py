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
        self._instances = []

    def get_all_instances_full_data(self, cache=False):
        """Get all instances with full data

        - cache: if True, cache results in self._instances
        """
        instances = []
        for x in self._ec2_client.describe_instances()['Reservations']:
            instances.extend(x['Instances'])
        if cache:
            self._instances = instances
        return instances

    def get_all_instances_filtered_data(self, cache=False):
        """Get all instances filtered on EC2_INSTANCE_KEYS

        - cache: if True, cache results in self._instances
        """
        instances = [
            ih.filter_keys(instance, *EC2_INSTANCE_KEYS)
            for instance in self.get_all_instances_full_data()
        ]
        if cache:
            self._instances = instances
        return instances

    def get_cached_instances(self):
        return self._instances
