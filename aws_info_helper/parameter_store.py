import aws_info_helper as ah
import input_helper as ih
from functools import partial


class ParameterStore(object):
    def __init__(self, profile_name='default'):
        session = ah.get_session(profile_name)
        self._client = session.client('ssm')
        self._profile = profile_name
        self._cache = {}
        self.client_call = partial(ah.client_call, self._client)

    def get_cached(self):
        return self._cache

    @property
    def cached_parameters(self):
        return self._cache.get('parameters', [])

    @property
    def cached_parameter_names(self):
        return self._cache.get('parameter_names', [])

    def get_parameters_full_data(self, cache=False):
        """Get all parameters with full data

        - cache: if True, cache results in self._cache['parameters']
        """
        resp = self.client_call('describe_parameters')
        parameters = resp.get('Parameters', [])
        while 'NextToken' in resp:
            resp = self.client_call('describe_parameters', NextToken=resp['NextToken'])
            parameters.extend(resp.get('Parameters', []))
        if cache:
            self._cache['parameters'] = parameters
        return parameters

    def get_parameter_names(self, cache=False):
        """Return a list of parameter names

        - cache: if True, cache results in self._cache['parameter_names']
        """
        parameter_names = sorted([x['Name'] for x in self.get_parameters_full_data()])
        if cache:
            self._cache['parameter_names'] = parameter_names
        return parameter_names

    def get_values_dict(self, *parameters):
        """Return a dict of parameter names and values stored in Parameter Store"""
        results = {}
        for chunk in ih.chunk_list(parameters, 10):
            resp = self.client_call('get_parameters', 'Parameters', Names=chunk, WithDecryption=True)
            results.update({x['Name']: x['Value'] for x in resp})
        return results

    def get_value(self, parameter):
        """Return the value for a specific parameter"""
        param = self.client_call('get_parameter', 'Parameter', Name=parameter, WithDecryption=True)
        if param:
            return param['Value']

    def get_all_values(self):
        """Return a dict of all parameter names and values stored in Parameter Store"""
        return self.get_values_dict(*self.get_parameter_names())
