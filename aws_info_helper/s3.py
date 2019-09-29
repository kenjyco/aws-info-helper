import aws_info_helper as ah
import input_helper as ih
import dt_helper as dh
from functools import partial
from os.path import isdir, dirname, basename, join
from os import makedirs
try:
    import redis_helper as rh
    from redis import ConnectionError as RedisConnectionError
except ImportError:
    AWS_S3 = None
    AWS_S3_LAST_FILE = None
else:
    try:
        AWS_S3 = rh.Collection(
            'aws',
            's3',
            index_fields='profile, bucket',
        )
        AWS_S3_LAST_FILE = rh.Collection(
            'aws',
            's3_last',
            index_fields='profile, bucket, prefix',
        )
    except RedisConnectionError:
        AWS_S3 = None
        AWS_S3_LAST_FILE = None


BUCKET_KEY_VALUE_CASTING = {
    'CreationDate': lambda x: dh.utc_float_to_pretty(dh.dt_to_float_string(x))
}

BUCKET_KEY_NAME_MAPPING = {
    'Name': 'bucket',
    'CreationDate': 'created'
}


class S3(object):
    def __init__(self, profile_name='default'):
        session = ah.get_session(profile_name)
        self._client = session.client('s3')
        self._profile = profile_name
        self._cache = {'_last_file':{}}
        self._collection = AWS_S3
        self._collection_last_file = AWS_S3_LAST_FILE
        self.client_call = partial(ah.client_call, self._client)

    def get_cached(self, name=''):
        """Return entire cache or cache for a specific key name"""
        if name == '':
            return self._cache
        else:
            return self._cache.get(name, [])

    def get_cached_keys(self):
        """Return list of keys in self._cache"""
        return list(self._cache.keys())

    @property
    def cached_buckets(self):
        return self._cache.get('buckets', [])

    @property
    def cached_bucket_names(self):
        return self._cache.get('bucket_names', [])

    @property
    def cached_last_files(self):
        return self._cache.get('_last_file', {})

    def get_all_buckets_full_data(self, cache=False):
        """Get all buckets with full data

        - cache: if True, cache results in self._cache['buckets']
        """
        buckets = self.client_call('list_buckets', 'Buckets')
        if cache:
            self._cache['buckets'] = buckets
        return buckets

    def get_bucket_names(self, cache=False):
        """Return a list of bucket names

        - cache: if True, cache results in self._cache['bucket_names']
        """
        bucket_names = [
            bucket['Name']
            for bucket in self.get_all_buckets_full_data(cache=cache)
        ]
        if cache:
            self._cache['bucket_names'] = bucket_names
        return bucket_names

    def get_bucket_files_full_data(self, bucket, prefix='', start_after='',
                                   limit=1500, start_after_last=False):
        """List all the files in a bucket

        - bucket: name of S3 bucket
        - prefix: limit response to files that start with this prefix
        - start_after: a specific file (key) to start listing after
        - limit: if None, return all files
        - start_after_last: if True and 'start_after' is empty string,
          automatically set 'start_after' to be the last file that was returned
          by get_bucket_files_full_data for the given bucket and prefix
        """
        results = []
        cached = self._cache['_last_file'].get((bucket, prefix))
        if self._collection_last_file is not None:
            found = self._collection_last_file.find(
                'profile:{}, bucket:{}, prefix:{}'.format(self._profile, bucket, prefix),
                get_fields='last'
            )
            if found:
                found_id = found[0]['_id']
                found_name = found[0]['last']
            else:
                found_id = None
                found_name = None
        else:
            found_id = None
            found_name = None
        if start_after_last is True and start_after == '':
            if cached:
                start_after = cached
            elif found_name:
                start_after = found_name

        func = partial(
            self.client_call,
            'list_objects_v2',
            Bucket=bucket,
            Prefix=prefix,
            StartAfter=start_after
        )

        if limit is not None and limit < 1000:
            resp = func(MaxKeys=limit)
        else:
            resp = func()
        results.extend(resp.get('Contents', []))

        while 'NextContinuationToken' in resp:
            token = resp['NextContinuationToken']
            maxkeys = 1000
            if limit:
                current_len = len(results)
                if current_len >= limit:
                    break
                maxkeys = limit - current_len
                maxkeys = 1000 if maxkeys > 1000 else maxkeys
            resp = func(ContinuationToken=token, MaxKeys=maxkeys)
            results.extend(resp.get('Contents', []))
        if results:
            last_key = results[-1]['Key']
            self._cache['_last_file'][(bucket, prefix)] = last_key
            if self._collection_last_file is not None:
                if found_id:
                    self._collection_last_file.update(found_id, last=last_key)
                else:
                    self._collection_last_file.add(
                        profile=self._profile, bucket=bucket, prefix=prefix, last=last_key
                    )
        return results

    def download_file(self, bucket, filename, local_filename=''):
        """Download a file from S3

        - bucket: name of S3 bucket
        - filename: name of file (key) in S3 bucket
        - local_filename: local file name (including path) to save file as
            - if an existing directory is given, the file will be saved in there
        """
        if not local_filename:
            local_filename = basename(filename)
        elif isdir(local_filename):
            local_filename = join(local_filename, basename(filename))
        local_dir = dirname(local_filename)
        if local_dir:
            if not isdir(local_dir):
                makedirs(local_dir)
        result = self.client_call(
            'download_file',
            Bucket=bucket,
            Key=filename,
            Filename=local_filename
        )
        return local_filename

    def get_file_lister_for_bucket(self, bucket, prefix='', limit=1500):
        """Return a func that will list next limit files for a bucket at a prefix

        Wrapper to self.get_bucket_files_full_data
        """
        return partial(
            self.get_bucket_files_full_data,
            bucket,
            prefix=prefix,
            limit=limit,
            start_after_last=True
        )

    def clear_last_file_for_bucket_and_prefix(self, bucket, prefix=''):
        """Clear any 'last file' info for bucket/prefix combo"""
        if (bucket, prefix) in self._cache['_last_file']:
            del(self._cache['_last_file'][(bucket, prefix)])

        if self._collection_last_file is not None:
            found = self._collection_last_file.find(
                'profile:{}, bucket:{}, prefix:{}'.format(self._profile, bucket, prefix),
            )
            if found:
                self._collection_last_file.delete(found[0]['_id'])

    def clear_last_files_for_bucket(self, bucket):
        """Clear any 'last file' info for bucket (across all prefixes)"""
        # Technically, should try to iterate over keys in _cache['_last_file']
        # and find the ones for that bucket only to delete... but meh
        self._cache['_last_file'] = {}

        if self._collection_last_file is not None:
            found_ids = self._collection_last_file.find(
                'profile:{}, bucket:{}'.format(self._profile, bucket),
                item_format='{_id}',
                limit=None
            )
            if found_ids:
                self._collection_last_file.delete_many(*found_ids)

    def update_collection(self):
        """Update the rh.Collection object if redis-helper installed"""
        if self._collection is None:
            return

        updates = []
        for bucket in self.get_all_buckets_full_data(cache=True):
            data = ih.cast_keys(bucket, **BUCKET_KEY_VALUE_CASTING)
            data = ih.rename_keys(data, **BUCKET_KEY_NAME_MAPPING)
            data.update(dict(profile=self._profile))
            found = self._collection.find(
                'profile:{}, bucket:{}'.format(self._profile, data['bucket']),
            )
            if not found:
                updates.append(self._collection.add(**data))
        return {'updates': updates}

