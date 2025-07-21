A practical Python library for retrieving and formatting AWS resource information with minimal cognitive overhead. Rather than hiding AWS API complexity behind abstractions, it provides transparent, three-tier data access (raw → filtered → formatted) that lets you work at the level of detail appropriate for your task. Whether you need complete AWS API responses for integration work, filtered data for operational dashboards, or human-readable formats for reporting, each processing stage is explicit and accessible. The library excels in CLI-first workflows, interactive data exploration, and multi-account AWS environments.

## Install

Install with `pip`

```
pip install aws-info-helper
```

#### Or, install with redis-helper backend support

```
pip install aws-info-helper[redis]
```

## Example settings.ini

```ini
[default]
EC2_INSTANCE_KEYS = Architecture, CpuOptions.CoreCount, CpuOptions.ThreadsPerCore, ImageId, InstanceId, InstanceType, KeyName, LaunchTime, Placement.AvailabilityZone, PrivateDnsName, PrivateIpAddress, PublicDnsName, PublicIpAddress, SecurityGroups.GroupId, State.Name, SubnetId, Tags.Value, VpcId
EC2_INSTANCE_INFO_FORMAT = \n- {InstanceId} ({PublicIpAddress}):\n   - {KeyName} {State__Name} {InstanceType} {CpuOptions__CoreCount}-core {CpuOptions__ThreadsPerCore}-thread\n   - {ImageId} {VpcId} {SubnetId}\n   - Launch Time: {LaunchTime}\n   - Name: {Tags__Value}
EC2_ADDRESS_KEYS = PublicIp, InstanceId
ROUTE53_ZONE_KEYS = Id, Name
ROUTE53_RESOURCE_KEYS = Name, Type, ResourceRecords.Value, AliasTarget.DNSName
ROUTE53_RESOURCE_INFO_FORMAT = - {name} ({value}) type={type}
```

> On first use, the default settings.ini file is copied to `~/.config/aws-info-helper/settings.ini`

## QuickStart

```python
from aws_info_helper import EC2

# Initialize with default AWS profile
ec2 = EC2()

# Get human-readable instance information
instances = ec2.get_all_instances_serialized_data()
for instance in instances:
    print(f"{instance['id']} ({instance['ip']}): {instance['type']}")

# Show formatted instance overview
ec2.show_instance_info()

# Access complete internal state for debugging
cache = ec2.get_cached()
print(f"Retrieved {len(cache.get('instances', []))} instances")

# Work with filtered data for custom processing
filtered_data = ec2.get_all_instances_filtered_data(cache=True)
running_instances = [i for i in filtered_data if i.get('State__Name') == 'running']
```

**What you gain**: Immediate access to AWS EC2 data at three different levels of processing. The `serialized_data` gives you human-friendly field names and formatting. The `filtered_data` provides AWS API fields filtered to your specifications. All processing stages are cached and inspectable, enabling both quick operational tasks and detailed debugging when needed.

## API Overview

### Utility Functions

**`get_session(profile_name='default')`** - Creates boto3 session with graceful handling of missing profiles
- `profile_name`: AWS profile name from `~/.aws/credentials`
- Returns: boto3.Session object
- Internal calls: None

**`client_call(client, method_name, main_key='', **kwargs)`** - Standardized AWS API error handling wrapper
- `client`: boto3 client object
- `method_name`: AWS API method name to call
- `main_key`: Response key to extract (e.g., 'Reservations', 'Parameters')
- `**kwargs`: Arguments passed to AWS API method
- Returns: API response data with error handling
- Internal calls: None

**`get_profiles()`** - Returns list of available AWS profiles from credentials file
- Returns: List of profile names
- Internal calls: None

### Core Service Classes

#### EC2(profile_name='default')
Primary interface for EC2 instance and related resource information. Creates boto3 EC2 client and sets `self.client_call` as a partial function wrapper around `ah.client_call` using the EC2 client.

**EC2 Instance Methods:**

**`EC2.get_all_instances_full_data(cache=False)`** - Returns complete AWS API responses from describe_instances
- `cache`: If True, stores results in internal cache for subsequent access
- Returns: List of complete AWS instance dictionaries with all AWS API fields
- Internal calls: `self.client_call('describe_instances', 'Reservations')`

**`EC2.get_all_instances_filtered_data(cache=False, filter_keys=ah.EC2_INSTANCE_KEYS, conditions=INSTANCE_FILTER_KEY_CONDITIONS)`** - Returns subset of fields with business logic applied
- `cache`: If True, caches the filtered results
- `filter_keys`: List of AWS API field names to include (defaults to `EC2_INSTANCE_KEYS` from settings)
- `conditions`: Dict of key names and single-var funcs that return bool (defaults to `INSTANCE_FILTER_KEY_CONDITIONS`)
- Returns: List of dictionaries with specified fields, flattened key paths (e.g., `CpuOptions.CoreCount` → `CpuOptions__CoreCount`)
- Internal calls: `self.get_all_instances_full_data()`, `ih.filter_keys()`

**`EC2.get_all_instances_serialized_data(cache=False, filtered_data=None, value_casting=INSTANCE_KEY_VALUE_CASTING, name_mapping=INSTANCE_KEY_NAME_MAPPING)`** - Returns human-readable data with friendly field names
- `cache`: If True, caches serialized results
- `filtered_data`: Instance data from `get_all_instances_filtered_data()` (if None, will be retrieved)
- `value_casting`: Dict of key names and single-var funcs for value transformation (defaults to `INSTANCE_KEY_VALUE_CASTING`)
- `name_mapping`: Dict of key names and new key names for field renaming (defaults to `INSTANCE_KEY_NAME_MAPPING`)
- Returns: List with renamed keys (`InstanceId` → `id`, `PublicIpAddress` → `ip`) and formatted timestamps
- Internal calls: `self.get_all_instances_filtered_data()`, `ih.cast_keys()`, `ih.rename_keys()`

**`EC2.show_instance_info(item_format=ah.EC2_INSTANCE_INFO_FORMAT, filter_keys=ah.EC2_INSTANCE_KEYS, force_refresh=False, cache=False)`** - Displays formatted instance information using template from settings
- `item_format`: Format string for lines of output (defaults to `EC2_INSTANCE_INFO_FORMAT` from settings)
- `filter_keys`: Key names passed to `get_all_instances_filtered_data()` (defaults to `EC2_INSTANCE_KEYS` from settings)
- `force_refresh`: If True, fetch instance data with `get_all_instances_filtered_data()`
- `cache`: If True, cache results in `self._cache['instance_strings']`
- Returns: None (prints formatted output)
- Internal calls: `self.get_all_instances_filtered_data()`, `ih.get_string_maker()`

**EC2 Related Resource Methods:**

**`EC2.get_elastic_addresses_full_data(cache=False)`** - Retrieves Elastic IP addresses
- `cache`: If True, stores results in internal cache
- Returns: List of Elastic IP address dictionaries
- Internal calls: `self.client_call('describe_addresses', 'Addresses')`

**`EC2.get_elastic_addresses_filtered_data(cache=False, filter_keys=ah.EC2_ADDRESS_KEYS)`** - Retrieves filtered Elastic IP addresses
- `cache`: If True, stores results in internal cache
- `filter_keys`: Keys to include in filtered results (defaults to `EC2_ADDRESS_KEYS` from settings)
- Returns: List of filtered Elastic IP address dictionaries
- Internal calls: `self.get_elastic_addresses_full_data()`, `ih.filter_keys()`

**`EC2.get_all_azs_full_data(cache=False)`** - Retrieves availability zones
- `cache`: If True, stores results in internal cache
- Returns: List of availability zone dictionaries
- Internal calls: `self.client_call('describe_availability_zones', 'AvailabilityZones')`

**`EC2.get_all_customer_gateways_full_data(cache=False)`** - Retrieves customer gateways
- `cache`: If True, stores results in internal cache
- Returns: List of customer gateway dictionaries
- Internal calls: `self.client_call('describe_customer_gateways', 'CustomerGateways')`

**`EC2.get_all_internet_gateways_full_data(cache=False)`** - Retrieves internet gateways
- `cache`: If True, stores results in internal cache
- Returns: List of internet gateway dictionaries
- Internal calls: `self.client_call('describe_internet_gateways', 'InternetGateways')`

**`EC2.get_all_keypairs_full_data(cache=False)`** - Retrieves SSH key pairs
- `cache`: If True, stores results in internal cache
- Returns: List of key pair dictionaries
- Internal calls: `self.client_call('describe_key_pairs', 'KeyPairs')`

**`EC2.get_all_nat_gateways_full_data(cache=False)`** - Retrieves NAT gateways
- `cache`: If True, stores results in internal cache
- Returns: List of NAT gateway dictionaries
- Internal calls: `self.client_call('describe_nat_gateways', 'NatGateways')`

**`EC2.get_all_network_acls_full_data(cache=False)`** - Retrieves network ACLs
- `cache`: If True, stores results in internal cache
- Returns: List of network ACL dictionaries
- Internal calls: `self.client_call('describe_network_acls', 'NetworkAcls')`

**`EC2.get_all_network_interfaces_full_data(cache=False)`** - Retrieves network interfaces
- `cache`: If True, stores results in internal cache
- Returns: List of network interface dictionaries
- Internal calls: `self.client_call('describe_network_interfaces', 'NetworkInterfaces')`

**`EC2.get_all_regions_full_data(cache=False)`** - Retrieves AWS regions
- `cache`: If True, stores results in internal cache
- Returns: List of region dictionaries
- Internal calls: `self.client_call('describe_regions', 'Regions')`

**`EC2.get_all_route_tables_full_data(cache=False)`** - Retrieves route tables
- `cache`: If True, stores results in internal cache
- Returns: List of route table dictionaries
- Internal calls: `self.client_call('describe_route_tables', 'RouteTables')`

**`EC2.get_all_security_groups_full_data(cache=False)`** - Retrieves security groups
- `cache`: If True, stores results in internal cache
- Returns: List of security group dictionaries
- Internal calls: `self.client_call('describe_security_groups', 'SecurityGroups')`

**`EC2.get_all_subnets_full_data(cache=False)`** - Retrieves subnets
- `cache`: If True, stores results in internal cache
- Returns: List of subnet dictionaries
- Internal calls: `self.client_call('describe_subnets', 'Subnets')`

**`EC2.get_all_tags_full_data(cache=False)`** - Retrieves resource tags
- `cache`: If True, stores results in internal cache
- Returns: List of tag dictionaries
- Internal calls: `self.client_call('describe_tags', 'Tags')`

**`EC2.get_all_volume_statuses_full_data(cache=False)`** - Retrieves EBS volume statuses
- `cache`: If True, stores results in internal cache
- Returns: List of volume status dictionaries
- Internal calls: `self.client_call('describe_volume_status', 'VolumeStatuses')`

**`EC2.get_all_volumes_full_data(cache=False)`** - Retrieves EBS volumes
- `cache`: If True, stores results in internal cache
- Returns: List of EBS volume dictionaries
- Internal calls: `self.client_call('describe_volumes', 'Volumes')`

**`EC2.get_all_vpcs_full_data(cache=False)`** - Retrieves VPCs
- `cache`: If True, stores results in internal cache
- Returns: List of VPC dictionaries
- Internal calls: `self.client_call('describe_vpcs', 'Vpcs')`

**State Management:**

**`EC2.get_cached()`** - Returns complete internal cache dictionary for inspection
- Returns: Dictionary containing all cached data with keys like 'instances', 'volumes', etc.
- Internal calls: None

**`EC2.cached_instances`** (property) - Safe access to cached instance data with empty list default
- Returns: List of cached instance dictionaries or empty list if not cached
- Internal calls: None

**`EC2.cached_addressess`**, **`EC2.cached_azs`**, **`EC2.cached_customer_gateways`**, **`EC2.cached_internet_gateways`**, **`EC2.cached_keypairs`**, **`EC2.cached_nat_gateways`**, **`EC2.cached_network_acls`**, **`EC2.cached_network_interfaces`**, **`EC2.cached_regions`**, **`EC2.cached_route_tables`**, **`EC2.cached_security_groups`**, **`EC2.cached_subnets`**, **`EC2.cached_tags`**, **`EC2.cached_volume_statuses`**, **`EC2.cached_volumes`**, **`EC2.cached_vpcs`** (properties) - Access to other cached resource types
- Returns: List of cached resource dictionaries or empty list if not cached
- Internal calls: None

**`EC2.update_collection()`** - Updates Redis collections with current data
- Returns: Dictionary with 'updates' and 'deletes' keys containing operation results
- Internal calls: `self.get_all_instances_filtered_data()`, `self.get_elastic_addresses_filtered_data()`, `ih.cast_keys()`, `ih.rename_keys()`, Redis collection operations (requires redis-helper)

#### S3(profile_name='default')
Interface for S3 bucket and object information with sophisticated pagination support. Creates boto3 S3 client and sets `self.client_call` as a partial function wrapper around `ah.client_call` using the S3 client.

**S3 Bucket Methods:**

**`S3.get_all_buckets_full_data(cache=False)`** - Complete bucket information
- `cache`: If True, stores results in internal cache
- Returns: List of S3 bucket dictionaries with complete AWS API response data
- Internal calls: `self.client_call('list_buckets', 'Buckets')`

**`S3.get_bucket_names(cache=False)`** - List of bucket names
- `cache`: If True, stores bucket names in cache
- Returns: List of bucket name strings
- Internal calls: `self.get_all_buckets_full_data()`

**S3 Object Methods:**

**`S3.get_bucket_files_full_data(bucket, prefix='', start_after='', limit=1500, start_after_last=False)`** - Objects with pagination support
- `bucket`: S3 bucket name
- `prefix`: Limit response to files that start with this prefix
- `start_after`: Specific file (key) to start listing after
- `limit`: Maximum number of files to return (None for all files)
- `start_after_last`: If True and start_after is empty, automatically resume from last file returned
- Returns: List of S3 object dictionaries
- Internal calls: `self.client_call('list_objects_v2')` with continuation token management

**`S3.download_file(bucket, filename, local_filename='')`** - Download file from S3
- `bucket`: S3 bucket name
- `filename`: Name of file (key) in S3 bucket
- `local_filename`: Local file name (including path) to save file as
- Returns: Local filename where file was saved
- Internal calls: `self.client_call('download_file')`

**`S3.get_file_lister_for_bucket(bucket, prefix='', limit=1500)`** - Returns function for listing next batch of files
- `bucket`: S3 bucket name
- `prefix`: Key prefix filter for objects
- `limit`: Maximum files per batch
- Returns: Function that lists next limit files for bucket at prefix
- Internal calls: None

**State Management:**

**`S3.get_cached(name='')`** - Return entire cache or cache for specific key name
- `name`: Specific cache key name (empty string returns entire cache)
- Returns: Complete cache dictionary or specific cached data
- Internal calls: None

**`S3.get_cached_keys()`** - Return list of keys in cache
- Returns: List of cache key names
- Internal calls: None

**`S3.cached_buckets`** (property) - Access to cached bucket data
- Returns: List of cached bucket dictionaries or empty list if not cached
- Internal calls: None

**`S3.cached_bucket_names`** (property) - Access to cached bucket names
- Returns: List of cached bucket name strings or empty list if not cached
- Internal calls: None

**`S3.cached_last_files`** (property) - Access to pagination state
- Returns: Dictionary mapping (bucket, prefix) tuples to last processed file keys
- Internal calls: None

#### Route53(profile_name='default')
DNS zone and record management interface. Creates boto3 Route53 client and sets `self.client_call` as a partial function wrapper around `ah.client_call` using the Route53 client.

**Route53 Zone Methods:**

**`Route53.get_all_hosted_zones_full_data(cache=False)`** - Hosted zones information
- `cache`: If True, stores results in internal cache
- Returns: List of Route53 hosted zone dictionaries
- Internal calls: `self.client_call('list_hosted_zones', 'HostedZones')`

**`Route53.get_all_hosted_zones_filtered_data(cache=False, filter_keys=ah.ROUTE53_ZONE_KEYS)`** - Filtered hosted zones
- `cache`: If True, stores filtered results in cache
- `filter_keys`: Keys to include in filtered results (defaults to `ROUTE53_ZONE_KEYS` from settings)
- Returns: List of filtered hosted zone dictionaries
- Internal calls: `self.client_call('list_hosted_zones', 'HostedZones')`, `ih.filter_keys()`

**Route53 Record Methods:**

**`Route53.get_record_sets_for_zone_full_data(zone)`** - DNS records for specific zone
- `zone`: Hosted zone ID
- Returns: List of DNS record dictionaries for the zone
- Internal calls: `self.client_call('list_resource_record_sets', 'ResourceRecordSets')`

**`Route53.get_record_sets_for_zone_filtered_data(zone, filter_keys=ah.ROUTE53_RESOURCE_KEYS, types='A, CNAME')`** - Filtered DNS records for zone
- `zone`: Hosted zone ID
- `filter_keys`: Keys to include in filtered results (defaults to `ROUTE53_RESOURCE_KEYS` from settings)
- `types`: String containing allowed record types (defaults to 'A, CNAME')
- Returns: List of filtered DNS record dictionaries for specified types
- Internal calls: `self.get_record_sets_for_zone_full_data()`, `ih.filter_keys()`, `ih.string_to_set()`

**`Route53.get_all_record_sets_for_all_zones(cache=False)`** - DNS records across all zones with business logic
- `cache`: If True, stores results in internal cache
- Returns: List of DNS record dictionaries from all hosted zones with zone data merged and external flags
- Internal calls: `self.get_all_hosted_zones_filtered_data()`, `self.get_record_sets_for_zone_filtered_data()`, `ih.cast_keys()`, `ih.rename_keys()`

**`Route53.show_resource_info(item_format=ah.ROUTE53_RESOURCE_INFO_FORMAT, force_refersh=False, cache=False)`** - Formatted DNS record display
- `item_format`: Format string for output lines (defaults to `ROUTE53_RESOURCE_INFO_FORMAT` from settings)
- `force_refersh`: If True, fetch resource data with `get_all_record_sets_for_all_zones()`
- `cache`: If True, cache results in `self._cache['resource_strings']`
- Returns: None (prints formatted output)
- Internal calls: `self.get_all_record_sets_for_all_zones()`, `ih.get_string_maker()`

**State Management:**

**`Route53.get_cached()`** - Returns complete internal cache dictionary
- Returns: Dictionary containing all cached data
- Internal calls: None

**`Route53.cached_zones`** (property) - Access to cached zone data
- Returns: List of cached zone dictionaries or empty list if not cached
- Internal calls: None

**`Route53.cached_record_sets`** (property) - Access to cached record set data
- Returns: List of cached record set dictionaries or empty list if not cached
- Internal calls: None

**`Route53.cached_resource_strings`** (property) - Access to cached formatted strings
- Returns: List of cached formatted resource strings or empty list if not cached
- Internal calls: None

**`Route53.update_collection()`** - Updates Redis collections with current data
- Returns: Dictionary with 'updates' key containing operation results
- Internal calls: `self.get_all_record_sets_for_all_zones()`, Redis collection operations (requires redis-helper)

#### ParameterStore(profile_name='default')
AWS Systems Manager Parameter Store interface. Creates boto3 SSM client and sets `self.client_call` as a partial function wrapper around `ah.client_call` using the SSM client.

**Parameter Store Methods:**

**`ParameterStore.get_parameters_full_data(cache=False)`** - Complete parameter metadata
- `cache`: If True, stores results in internal cache
- Returns: List of parameter metadata dictionaries (names, types, descriptions, but not values)
- Internal calls: `self.client_call('describe_parameters')` with pagination handling

**`ParameterStore.get_parameter_names(cache=False)`** - Sorted list of parameter names
- `cache`: If True, stores parameter names in cache
- Returns: Sorted list of parameter name strings
- Internal calls: `self.get_parameters_full_data()`

**`ParameterStore.get_values_dict(*parameters)`** - Parameter values by name with decryption
- `*parameters`: Parameter names to retrieve
- Returns: Dictionary mapping parameter names to decrypted values
- Internal calls: `ih.chunk_list()`, `self.client_call('get_parameters')`

**`ParameterStore.get_value(parameter)`** - Single parameter value
- `parameter`: Parameter name to retrieve
- Returns: Decrypted parameter value string or None if not found
- Internal calls: `self.client_call('get_parameter')`

**`ParameterStore.get_all_values()`** - All parameter names and values as dictionary
- Returns: Dictionary mapping all parameter names to their decrypted values
- Internal calls: `self.get_parameter_names()`, `self.get_values_dict()`

**State Management:**

**`ParameterStore.get_cached()`** - Returns complete internal cache dictionary
- Returns: Dictionary containing all cached data
- Internal calls: None

**`ParameterStore.cached_parameters`** (property) - Access to cached parameter metadata
- Returns: List of cached parameter dictionaries or empty list if not cached
- Internal calls: None

**`ParameterStore.cached_parameter_names`** (property) - Access to cached parameter names
- Returns: List of cached parameter name strings or empty list if not cached
- Internal calls: None

### Redis Integration (Optional)

When redis-helper is available, the following collections are automatically created:

- `AWS_EC2` - EC2 instance data with indexing on profile, instance ID, name, and IP
- `AWS_S3` - S3 bucket information indexed by profile and bucket name
- `AWS_ROUTE53` - DNS records with cross-service IP address relationships
- `AWS_IP` - IP address tracking across services with instance references

These collections enable persistent data storage, cross-service queries, and relationship tracking between AWS resources.

### CLI Tools

The library includes comprehensive command-line interfaces:

- `ah-info-ec2` - Display EC2 instance information
- `ah-info-s3` - Display S3 bucket and object information
- `ah-info-route53` - Display DNS zone and record information
- `ah-collection-update-ec2` - Update Redis collections with current EC2 data
- `ah-ssh-command-ec2` - Execute SSH commands on EC2 instances with automatic key management

All CLI tools support:
- `--profile` flag for AWS profile selection
- `--all` flag for multi-profile operations
- `--non-interactive` flag to disable IPython sessions
- Interactive IPython integration for data exploration
