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

    def get_all_instances_filtered_data(self, cache=False, filter_keys=EC2_INSTANCE_KEYS):
        """Get all instances filtered on specified keys

        - cache: if True, cache results in self._instances
        - filter_keys: the keys that should be returned from full data with
          nesting allowed (default from EC2_INSTANCE_KEYS setting)
        """
        instances = [
            ih.filter_keys(instance, filter_keys)
            for instance in self.get_all_instances_full_data()
        ]
        if cache:
            self._instances = instances
        return instances

    def get_cached_instances(self):
        return self._instances

    def show_instance_info(self, item_format=EC2_INSTANCE_INFO_FORMAT,
                           filter_keys=EC2_INSTANCE_KEYS, force_refresh=False):
        """Show info about cached instances (will fetch/cache if none cached)

        - item_format: format string for lines of output (default from
          EC2_INSTANCE_INFO_FORMAT setting)
        - filter_keys: key names that will be passed to
          self.get_all_instances_filtered_data() (default from
          EC2_INSTANCE_KEYS setting)
            - only used if force_refresh is True, or if there is no cached
              instance info
        - force_refresh: if True, fetch instance data with
          self.get_all_instances_filtered_data()
        """
        if not self._instances or force_refresh:
            self.get_all_instances_filtered_data(cache=True, filter_keys=filter_keys)
        make_string = ih.get_string_maker(item_format)
        print('\n'.join([
            make_string(instance)
            for instance in self._instances
        ]))
