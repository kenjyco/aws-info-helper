import settings_helper as sh


get_setting = sh.settings_getter(__name__)
EC2_INSTANCE_KEYS = get_setting('EC2_INSTANCE_KEYS')
EC2_INSTANCE_INFO_FORMAT = get_setting('EC2_INSTANCE_INFO_FORMAT')


from aws_info_helper.ec2 import EC2, AWS_EC2
