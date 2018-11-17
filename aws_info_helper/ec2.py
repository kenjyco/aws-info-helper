import boto3
import aws_info_helper as ah
import input_helper as ih
import dt_helper as dh
from botocore.exceptions import EndpointConnectionError


FILTER_KEY_CONDITIONS = {
    'Tags__Value': lambda x: x.get('Key') == 'Name'
}


class EC2(object):
    def __init__(self, profile_name='default'):
        session = boto3.Session(profile_name=profile_name)
        self._ec2_client = session.client('ec2')
        self._ec2_resource = session.resource('ec2')
        self._instances = []
        self._instance_strings = []

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

    def get_all_instances_filtered_data(self, cache=False, filter_keys=ah.EC2_INSTANCE_KEYS,
                                        conditions=FILTER_KEY_CONDITIONS):
        """Get all instances filtered on specified keys

        - cache: if True, cache results in self._instances
        - filter_keys: the keys that should be returned from full data with
          nesting allowed (default from EC2_INSTANCE_KEYS setting)
        - conditions: dict of key names and single-var funcs that return bool
          (default from FILTER_KEY_CONDITIONS variable)
        """
        try:
            instances = [
                ih.filter_keys(instance, filter_keys, **conditions)
                for instance in self.get_all_instances_full_data()
            ]
        except EndpointConnectionError as e:
            print(repr(e))
            instances = []
        else:
            if cache:
                self._instances = instances
        return instances

    def get_cached_instances(self):
        return self._instances

    def get_cached_instance_strings(self):
        return self._instance_strings

    def show_instance_info(self, item_format=ah.EC2_INSTANCE_INFO_FORMAT,
                           filter_keys=ah.EC2_INSTANCE_KEYS, force_refresh=False,
                           cache=False):
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
        - cache: if True, cache results in self._instance_strings
        """
        if not self._instances or force_refresh:
            self.get_all_instances_filtered_data(cache=True, filter_keys=filter_keys)
        make_string = ih.get_string_maker(item_format)
        strings = [
            make_string(instance)
            for instance in self._instances
        ]
        if cache:
            self._instance_strings = strings
        print('\n'.join(strings))
