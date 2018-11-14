import boto3
import settings_helper as sh
import input_helper as ih
import dt_helper as dh
from pprint import pprint


get_setting = sh.settings_getter(__name__)
EC2_INSTANCE_KEYS = get_setting('EC2_INSTANCE_KEYS')
EC2_INSTANCE_INFO_FORMAT = get_setting('EC2_INSTANCE_INFO_FORMAT')


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

    def show_instance_info(self, item_format=EC2_INSTANCE_INFO_FORMAT):
        """Show info about cached instances

        - item_format: Format string for lines of output (default from
          EC2_INSTANCE_INFO_FORMAT setting)

        If no cached info is found, fetch it using
        self.get_all_instances_filtered_data
        """
        if not self._instances:
            self.get_all_instances_filtered_data(cache=True)
        make_string = ih.get_string_maker(item_format)
        print('\n'.join([
            make_string(instance)
            for instance in self._instances
        ]))
