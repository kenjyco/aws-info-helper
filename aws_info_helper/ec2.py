import aws_info_helper as ah
import input_helper as ih
import dt_helper as dh
from functools import partial
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
            index_fields='profile, type, pem, az, subnet, ami, name, status, sshuser',
            json_fields='sg',
            insert_ts=True
        )
    except RedisConnectionError:
        AWS_EC2 = None


INSTANCE_FILTER_KEY_CONDITIONS = {
    'Tags__Value': lambda x: x.get('Key') == 'Name'
}

INSTANCE_KEY_VALUE_CASTING = {
    'LaunchTime': lambda x: dh.utc_float_to_pretty(dh.dt_to_float_string(x))
}

INSTANCE_KEY_NAME_MAPPING = {
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

ADDRESS_KEY_NAME_MAPPING = {
    'PublicIp': 'ip',
    'InstanceId': 'instance',
}


class EC2(object):
    def __init__(self, profile_name='default'):
        session = ah.get_session(profile_name)
        self._client = session.client('ec2')
        self._profile = profile_name
        self._cache = {}
        self._collection = AWS_EC2
        self.client_call = partial(ah.client_call, self._client)

    def get_cached(self):
        return self._cache

    @property
    def cached_instances(self):
        return self._cache.get('instances', [])

    @property
    def cached_addressess(self):
        return self._cache.get('addressess', [])

    @property
    def cached_instance_strings(self):
        return self._cache.get('instance_strings', [])

    @property
    def cached_azs(self):
        return self._cache.get('azs', [])

    @property
    def cached_customer_gateways(self):
        return self._cache.get('customer_gateways', [])

    @property
    def cached_internet_gateways(self):
        return self._cache.get('internet_gateways', [])

    @property
    def cached_keypairs(self):
        return self._cache.get('keypairs', [])

    @property
    def cached_nat_gateways(self):
        return self._cache.get('nat_gateways', [])

    @property
    def cached_network_acls(self):
        return self._cache.get('network_acls', [])

    @property
    def cached_network_interfaces(self):
        return self._cache.get('network_interfaces', [])

    @property
    def cached_regions(self):
        return self._cache.get('regions', [])

    @property
    def cached_route_tables(self):
        return self._cache.get('route_tables', [])

    @property
    def cached_security_groups(self):
        return self._cache.get('security_groups', [])

    @property
    def cached_subnets(self):
        return self._cache.get('subnets', [])

    @property
    def cached_tags(self):
        return self._cache.get('tags', [])

    @property
    def cached_volume_statuses(self):
        return self._cache.get('volume_statuses', [])

    @property
    def cached_volumes(self):
        return self._cache.get('volumes', [])

    @property
    def cached_vpcs(self):
        return self._cache.get('vpcs', [])

    def get_all_instances_full_data(self, cache=False):
        """Get all instances with full data

        - cache: if True, cache results in self._cache['instances']
        """
        instances = []
        for x in self.client_call('describe_instances', 'Reservations'):
            instances.extend(x['Instances'])
        if cache:
            self._cache['instances'] = instances
        return instances

    def get_all_instances_filtered_data(self, cache=False, filter_keys=ah.EC2_INSTANCE_KEYS,
                                        conditions=INSTANCE_FILTER_KEY_CONDITIONS):
        """Get all instances filtered on specified keys

        - cache: if True, cache results in self._cache['instances']
        - filter_keys: the keys that should be returned from full data with
          nesting allowed (default from EC2_INSTANCE_KEYS setting)
            - key name format: simple
            - key name format: some.nested.key
        - conditions: dict of key names and single-var funcs that return bool
          (default from INSTANCE_FILTER_KEY_CONDITIONS variable)
            - key name format: simple
            - key name format: some__nested__key
        """
        instances = [
            ih.filter_keys(instance, filter_keys, **conditions)
            for instance in self.get_all_instances_full_data()
        ]
        if cache:
            self._cache['instances'] = instances
        return instances

    def get_all_instances_serialized_data(self, cache=False, filtered_data=None,
                                          value_casting=INSTANCE_KEY_VALUE_CASTING,
                                          name_mapping=INSTANCE_KEY_NAME_MAPPING):
        """

        - cache: if True, cache results in self._cache['instances']
        - filtered_data: instance data from self.get_all_instances_filtered_data()
        - value_casting: dict of key names and single-var funcs that return casted
          value for that key name (default from INSTANCE_KEY_VALUE_CASTING variable)
        - name_mapping: dict of key names and new key names they should be mapped to
          (default from INSTANCE_KEY_NAME_MAPPING variable)
        """
        if filtered_data is None:
            filtered_data = self.get_all_instances_filtered_data()
        results = []
        for instance in filtered_data:
            data = ih.cast_keys(instance, **value_casting)
            data = ih.rename_keys(data, **name_mapping)
            data.update(dict(profile=self._profile))
            results.append(data)
        if cache:
            self._cache['instances'] = results
        return results

    def get_elastic_addresses_full_data(self, cache=False):
        """Get all elastic ip addresses with full data

        - cache: if True, cache results in self._cache['addresses']
        """
        addresses = self.client_call('describe_addresses', 'Addresses')
        if cache:
            self._cache['addresses'] = addresses
        return addresses

    def get_elastic_addresses_filtered_data(self, cache=False, filter_keys=ah.EC2_ADDRESS_KEYS):
        """Get all elastic ip addresses filtered on specified keys

        - cache: if True, cache results in self._cache['addresses']
        - filter_keys: the keys that should be returned from full data with
          nesting allowed (default from EC2_ADDRESS_KEYS setting)
            - key name format: simple
            - key name format: some.nested.key
        """
        addresses = [
            ih.filter_keys(address, filter_keys)
            for address in self.get_elastic_addresses_full_data()
        ]
        if cache:
            self._cache['addresses'] = addresses
        return addresses

    def get_all_azs_full_data(self, cache=False):
        """Get all availibility zones with full data

        - cache: if True, cache results in self._cache['azs']
        """
        azs = self.client_call('describe_availability_zones', 'AvailabilityZones')
        if cache:
            self._cache['azs'] = azs
        return azs

    def get_all_customer_gateways_full_data(self, cache=False):
        """Get all customer gateways with full data

        - cache: if True, cache results in self._cache['customer_gateways']
        """
        gateways = self.client_call('describe_customer_gateways', 'CustomerGateways')
        if cache:
            self._cache['customer_gateways'] = gateways
        return gateways

    def get_all_internet_gateways_full_data(self, cache=False):
        """Get all internet gateways with full data

        - cache: if True, cache results in self._cache['internet_gateways']
        """
        gateways = self.client_call('describe_internet_gateways', 'InternetGateways')
        if cache:
            self._cache['internet_gateways'] = gateways
        return gateways

    def get_all_keypairs_full_data(self, cache=False):
        """Get all keypairs with full data

        - cache: if True, cache results in self._cache['keypairs']
        """
        keypairs = self.client_call('describe_key_pairs', 'KeyPairs')
        if cache:
            self._cache['keypairs'] = keypairs
        return keypairs

    def get_all_nat_gateways_full_data(self, cache=False):
        """Get all nat gateways with full data

        - cache: if True, cache results in self._cache['nat_gateways']
        """
        gateways = self.client_call('describe_nat_gateways', 'NatGateways')
        if cache:
            self._cache['nat_gateways'] = gateways
        return gateways

    def get_all_network_acls_full_data(self, cache=False):
        """Get all network acls with full data

        - cache: if True, cache results in self._cache['network_acls']
        """
        network_acls = self.client_call('describe_network_acls', 'NetworkAcls')
        if cache:
            self._cache['network_acls'] = network_acls
        return network_acls

    def get_all_network_interfaces_full_data(self, cache=False):
        """Get all network interfaces with full data

        - cache: if True, cache results in self._cache['network_interfaces']
        """
        network_interfaces = self.client_call('describe_network_interfaces', 'NetworkInterfaces')
        if cache:
            self._cache['network_interfaces'] = network_interfaces
        return network_interfaces

    def get_all_regions_full_data(self, cache=False):
        """Get all regions with full data

        - cache: if True, cache results in self._cache['regions']
        """
        regions = self.client_call('describe_regions', 'Regions')
        if cache:
            self._cache['regions'] = regions
        return regions

    def get_all_route_tables_full_data(self, cache=False):
        """Get all route tables with full data

        - cache: if True, cache results in self._cache['route_tables']
        """
        route_tables = self.client_call('describe_route_tables', 'RouteTables')
        if cache:
            self._cache['route_tables'] = route_tables
        return route_tables

    def get_all_security_groups_full_data(self, cache=False):
        """Get all security_groups with full data

        - cache: if True, cache results in self._cache['security_groups']
        """
        security_groups = self.client_call('describe_security_groups', 'SecurityGroups')
        if cache:
            self._cache['security_groups'] = security_groups
        return security_groups

    def get_all_subnets_full_data(self, cache=False):
        """Get all subnets with full data

        - cache: if True, cache results in self._cache['subnets']
        """
        subnets = self.client_call('describe_subnets', 'Subnets')
        if cache:
            self._cache['subnets'] = subnets
        return subnets

    def get_all_tags_full_data(self, cache=False):
        """Get all tags with full data

        - cache: if True, cache results in self._cache['tags']
        """
        tags = self.client_call('describe_tags', 'Tags')
        if cache:
            self._cache['tags'] = tags
        return tags

    def get_all_volume_statuses_full_data(self, cache=False):
        """Get all volume statuses with full data

        - cache: if True, cache results in self._cache['volume_statuses']
        """
        volume_statuses = self.client_call('describe_volume_status', 'VolumeStatuses')
        if cache:
            self._cache['volume_statuses'] = volume_statuses
        return volume_statuses

    def get_all_volumes_full_data(self, cache=False):
        """Get all volumes with full data

        - cache: if True, cache results in self._cache['volumes']
        """
        volumes = self.client_call('describe_volumes', 'Volumes')
        if cache:
            self._cache['volumes'] = volumes
        return volumes

    def get_all_vpcs_full_data(self, cache=False):
        """Get all vpcs with full data

        - cache: if True, cache results in self._cache['vpcs']
        """
        vpcs = self.client_call('describe_vpcs', 'Vpcs')
        if cache:
            self._cache['vpcs'] = vpcs
        return vpcs

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
        - cache: if True, cache results in self._cache['instance_strings']
        """
        if not 'instances' in self._cache or force_refresh:
            self.get_all_instances_filtered_data(cache=True, filter_keys=filter_keys)
        make_string = ih.get_string_maker(item_format)
        strings = [
            make_string(instance)
            for instance in self.cached_instances
        ]
        if cache:
            self._cache['instance_strings'] = strings
        print('\n'.join(strings))


    def update_collection(self):
        """Update the rh.Collection object if redis-helper installed"""
        if self._collection is None:
            return

        ids_for_profile = set([
            x.get(self._collection._unique_field)
            for x in self._collection.find(
                'profile:{}'.format(self._profile),
                include_meta=False,
                get_fields=self._collection._unique_field,
                limit=self._collection.size
            )
        ])
        ids = set()
        updates = []
        deletes = []
        ip_hash_ids_to_delete = []

        for instance in self.get_all_instances_filtered_data():
            data = ih.cast_keys(instance, **INSTANCE_KEY_VALUE_CASTING)
            data = ih.rename_keys(data, **INSTANCE_KEY_NAME_MAPPING)
            data.update(dict(profile=self._profile))
            old_data = self._collection[data['id']]
            ids.add(data['id'])
            if not old_data:
                updates.append(self._collection.add(**data))
                if data['ip']:
                  updates.append(ah.AWS_IP.add(
                      ip=data['ip'],
                      instance=data['id'],
                      source='ec2',
                      profile=self._profile
                  ))
            else:
                hash_id = old_data['_id']
                try:
                    instance_id = data.pop(self._collection._unique_field)
                except KeyError:
                    pass
                updates.extend(self._collection.update(hash_id, **data))
                if data['ip'] != old_data['ip']:
                    ip_hash_ids_to_delete.extend(ah.AWS_IP.find(
                        'ip:{}, instance:{}'.format(old_data['ip'], old_data['id']),
                        item_format='{_id}'
                    ))
                if data['ip']:
                    existing = ah.AWS_IP.find(
                        'ip:{}, instance:{}'.format(data['ip'], instance_id),
                        include_meta=False
                    )
                    if not existing:
                        updates.append(ah.AWS_IP.add(
                            ip=data['ip'],
                            instance=instance_id,
                            source='ec2',
                            profile=self._profile
                        ))

        for instance_id in ids_for_profile - ids:
            hash_id = self._collection.get_hash_id_for_unique_value(instance_id)
            if hash_id is not None:
                old_data = self._collection.get(hash_id, 'id, ip')
                ip_hash_ids_to_delete.extend(ah.AWS_IP.find(
                    'ip:{}, instance:{}'.format(old_data['ip'], old_data['id']),
                    item_format='{_id}'
                ))
                self._collection.delete(hash_id)
                deletes.append(hash_id)

        if ip_hash_ids_to_delete:
            ah.AWS_IP.delete_many(*ip_hash_ids_to_delete)
            deletes.extend(ip_hash_ids_to_delete)

        for address in self.get_elastic_addresses_filtered_data():
            data = ih.rename_keys(address, **ADDRESS_KEY_NAME_MAPPING)
            existing = ah.AWS_IP.find(
                'ip:{}, source:eip'.format(data['ip']),
                include_meta=False
            )
            if not existing and data['instance']:
                updates.append(ah.AWS_IP.add(
                    ip=data['ip'],
                    instance=data['instance'],
                    source='eip',
                    profile=self._profile
                ))

        return {'updates': updates, 'deletes': deletes}
