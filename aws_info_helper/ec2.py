import boto3
import aws_info_helper as ah
import input_helper as ih
import dt_helper as dh
from botocore.exceptions import EndpointConnectionError, ClientError
try:
    import redis_helper as rh
    from redis import ConnectionError as RedisConnectionError
except ImportError:
    AWS_EC2 = None
else:
    try:
        AWS_EC2 = rh.Collection(
            'aws',
            'ec2',
            unique_field='id',
            index_fields='profile, type, pem, az, subnet, ami, name, status',
            json_fields='sg'
        )
    except RedisConnectionError:
        AWS_EC2 = None


FILTER_KEY_CONDITIONS = {
    'Tags__Value': lambda x: x.get('Key') == 'Name'
}

KEY_VALUE_CASTING = {
    'LaunchTime': lambda x: dh.utc_float_to_pretty(dh.dt_to_float_string(x))
}

KEY_NAME_MAPPING = {
    'Architecture': 'arch',
    'CpuOptions__CoreCount': 'cores',
    'CpuOptions__ThreadsPerCore': 'threads_per_core',
    'ImageId': 'ami',
    'InstanceId': 'id',
    'InstanceType': 'type',
    'KeyName': 'pem',
    'LaunchTime': 'launch',
    'Placement__AvailabilityZone': 'az',
    'PrivateDnsName': 'dns_private',
    'PrivateIpAddress': 'ip_private',
    'PublicDnsName': 'dns',
    'PublicIpAddress': 'ip',
    'SecurityGroups__GroupId': 'sg',
    'State__Name': 'status',
    'SubnetId': 'subnet',
    'Tags__Value': 'name',
    'VpcId': 'vpc',
}


class EC2(object):
    def __init__(self, profile_name='default'):
        session = boto3.Session(profile_name=profile_name)
        self._ec2_client = session.client('ec2')
        self._profile = profile_name
        self._instances = []
        self._instance_strings = []
        self._collection = AWS_EC2

    def get_all_instances_full_data(self, cache=False):
        """Get all instances with full data

        - cache: if True, cache results in self._instances
        """
        instances = []
        try:
            for x in self._ec2_client.describe_instances()['Reservations']:
                instances.extend(x['Instances'])
        except (EndpointConnectionError, ClientError) as e:
            print(repr(e))
        if cache:
            self._instances = instances
        return instances

    def get_all_instances_filtered_data(self, cache=False, filter_keys=ah.EC2_INSTANCE_KEYS,
                                        conditions=FILTER_KEY_CONDITIONS):
        """Get all instances filtered on specified keys

        - cache: if True, cache results in self._instances
        - filter_keys: the keys that should be returned from full data with
          nesting allowed (default from EC2_INSTANCE_KEYS setting)
            - key name format: simple
            - key name format: some.nested.key
        - conditions: dict of key names and single-var funcs that return bool
          (default from FILTER_KEY_CONDITIONS variable)
            - key name format: simple
            - key name format: some__nested__key
        """
        instances = [
            ih.filter_keys(instance, filter_keys, **conditions)
            for instance in self.get_all_instances_full_data()
        ]
        if cache:
            self._instances = instances
        return instances

    def get_cached_instances(self):
        return self._instances

    def get_cached_instance_strings(self):
        return self._instance_strings

    def get_collection_object(self):
        return self._collection

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


    def update_collection(self):
        """Update the rh.Collection object if redis-helper installed"""
        if self._collection is None:
            return

        updates = []
        for instance in self.get_all_instances_filtered_data():
            data = ih.cast_keys(instance, **KEY_VALUE_CASTING)
            data = ih.rename_keys(data, **KEY_NAME_MAPPING)
            data.update(dict(profile=self._profile))
            old_data = self._collection[data['id']]
            if not old_data:
                updates.append(self._collection.add(**data))
            else:
                hash_id = old_data['_id']
                try:
                    data.pop(self._collection._unique_field)
                except KeyError:
                    pass
                updates.extend(self._collection.update(hash_id, **data))
        return updates
