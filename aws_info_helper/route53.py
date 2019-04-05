import boto3
import aws_info_helper as ah
import input_helper as ih
import dt_helper as dh
from functools import partial
try:
    import redis_helper as rh
    from redis import ConnectionError as RedisConnectionError
except ImportError:
    AWS_ROUTE53 = None
else:
    try:
        AWS_ROUTE53 = rh.Collection(
            'aws',
            'route53',
            index_fields='domain, subdomain, type, external',
            rx_external='(yes|no)',
        )
    except RedisConnectionError:
        AWS_ROUTE53 = None


ZONE_KEY_VALUE_CASTING = {
    'Name': lambda x: x.strip('.')
}

RESOURCE_KEY_VALUE_CASTING = {
    'Name': lambda x: x.strip('.')
}

ZONE_KEY_NAME_MAPPING = {
    'Id': 'zone',
    'Name': 'domain',
}

RESOURCE_KEY_NAME_MAPPING = {
    'Name': 'subdomain',
    'Type': 'type',
    'ResourceRecords__Value': 'value',
    'AliasTarget__DNSName': 'alias',
}


class Route53(object):
    def __init__(self, profile_name='default'):
        session = boto3.Session(profile_name=profile_name)
        self._client = session.client('route53')
        self._profile = profile_name
        self._cache = {}
        self._collection = AWS_ROUTE53
        self.client_call = partial(ah.client_call, self._client)

    def get_cached(self):
        return self._cache

    @property
    def cached_zones(self):
        return self._cache.get('zones', [])

    @property
    def cached_record_sets(self):
        return self._cache.get('record_sets', [])

    def get_all_hosted_zones_full_data(self, cache=False):
        """Get all hosted zones with full data

        - cache: if True, cache results in self._cache['zones']
        """
        zones = self.client_call('list_hosted_zones', 'HostedZones')
        if cache:
            self._cache['zones'] = zones
        return zones

    def get_all_hosted_zones_filtered_data(self, cache=False, filter_keys=ah.ROUTE53_ZONE_KEYS):
        """Get all hosted zones filtered on specific keys

        - cache: if True, cache results in self._cache['zones']
        """
        zones = [
            ih.filter_keys(zone, filter_keys)
            for zone in self.client_call('list_hosted_zones', 'HostedZones')
        ]
        if cache:
            self._cache['zones'] = zones
        return zones

    def get_record_sets_for_zone_full_data(self, zone):
        """Get record sets for hosted zone

        - zone: the hosted zone id
        """
        return self.client_call(
            'list_resource_record_sets',
            'ResourceRecordSets',
            HostedZoneId=zone
        )

    def get_record_sets_for_zone_filtered_data(self, zone, filter_keys=ah.ROUTE53_RESOURCE_KEYS,
                                               types='A, CNAME'):
        """Get record sets for zone, returning specific keys

        - zone: the hosted zone id
        - filter_keys: the keys that should be returned from full data with
          nesting allowed (default from ROUTE53_RESOURCE_KEYS setting)
        - types: string containing allowed record types ('A, CNAME' by default)
        """
        types = ih.string_to_set(types)
        return [
            ih.filter_keys(record, filter_keys)
            for record in self.get_record_sets_for_zone_full_data(zone)
            if record['Type'] in types
        ]

    def get_all_record_sets_for_all_zones(self, cache=False):
        """For each hosted zone, get the record sets and return list of dicts"""
        results = []
        for zone in self.get_all_hosted_zones_filtered_data():
            zone_data = ih.cast_keys(zone, **ZONE_KEY_VALUE_CASTING)
            zone_data = ih.rename_keys(zone_data, **ZONE_KEY_NAME_MAPPING)
            for resource in self.get_record_sets_for_zone_filtered_data(zone_data['zone']):
                resource_data = ih.cast_keys(resource, **RESOURCE_KEY_VALUE_CASTING)
                resource_data = ih.rename_keys(resource_data, **RESOURCE_KEY_NAME_MAPPING)
                resource_data.update(zone_data)
                resource_data['subdomain'] = resource_data['subdomain'].replace(
                    zone_data['domain'], ''
                ).replace('\\052', '*').strip('.')
                resource_data['external'] = 'no'
                if resource_data['type'] == 'CNAME':
                    if not resource_data['value'].endswith(zone_data['domain']):
                        resource_data['external'] = 'yes'
                elif resource_data['type'] == 'A':
                    if resource_data['alias'] is not None:
                        resource_data['external'] = 'yes'
                results.append(resource_data)
        if cache:
            self._cache['record_sets'] = results
        return results

    def update_collection(self):
        """Update the rh.Collection object if redis-helper installed"""
        if self._collection is None:
            return

        updates = []
        self._collection.clear_keyspace()
        for data in self.get_all_record_sets_for_all_zones():
            updates.append(self._collection.add(**data))
        return {'updates': updates}
