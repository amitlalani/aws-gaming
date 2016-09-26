from urllib2 import urlopen

from base import client, ec2
from settings import *


my_public_ip = urlopen('http://ip.42.pl/raw').read()
print('My Public IP: {}'.format(my_public_ip))

print('Finding cheapest AZ')
prices = []
for az in VPC_SUBNET_MAP.keys():
    prices.append(client.describe_spot_price_history(
        InstanceTypes=[INSTANCE_TYPE],
        ProductDescriptions=[SPOT_INSTANCE_DESCRIPTION],
        AvailabilityZone=az,
        MaxResults=1
    )['SpotPriceHistory'][0])

import ipdb ; ipdb.set_trace()
cheapest_az = min(prices, key=lambda price: price['SpotPrice'])

print "Cheapest AZ: " + \
    cheapest_az['SpotPrice'], cheapest_az['AvailabilityZone']


if float(cheapest_az['SpotPrice']) > MAX_PRICE:
    print('Current spot price ({}) exceeeds maximum price ({})'.format(
        cheapest_az['SpotPrice'], MAX_PRICE))
    sys.exit(1)

print('Creating Security Group')
sec_group = client.create_security_group(
    GroupName='ec2-gaming',
    Description='ec2-gaming',
    VpcId=VPC_ID,
)

sec_group_id = sec_group['GroupId']

client.authorize_security_group_ingress(
    GroupId=sec_group_id,
    IpProtocol='-1',
    CidrIp='{}/32'.format(my_public_ip),
)

print('Finding Gaming Image:')
image = client.describe_images(
    Owners=['self'],
    Filters=[
        {
            'Name': 'name',
            'Values': [
                'ec2-gaming'
            ]
        }
    ]
)['Images'][0]

print('Requesting Spot Instance..')
spot_request_instance = client.request_spot_instances(
    SpotPrice=str(MAX_PRICE),
    LaunchSpecification={
        'ImageId': image['ImageId'],
        'SecurityGroupIds': [sec_group_id],
        'InstanceType': INSTANCE_TYPE,
        'SubnetId': VPC_SUBNET_MAP[cheapest_az['AvailabilityZone']],
    }
)['SpotInstanceRequests'][0]

spot_request_id = spot_request_instance['SpotInstanceRequestId']

ec2.create_tags(
    Resources=[spot_request_id],
    Tags=[
        {
            'Key': 'Name',
            'Value': 'ec2-gaming'
        }
    ]
)

print('Waiting for Spot Request to be fulfilled')
waiter = client.get_waiter('spot_instance_request_fulfilled')
waiter.wait(SpotInstanceRequestIds=[spot_request_id])


instance_id = client.describe_spot_instance_requests(
    SpotInstanceRequestIds=[spot_request_id]
)['SpotInstanceRequests'][0]['InstanceId']

print('Waiting for Instance to be ready')
waiter = client.get_waiter('instance_status_ok')
waiter.wait(
    InstanceIds=[instance_id]
)

print('Instance Ready. Hostname:')
instance = ec2.Instance(instance_id)
print instance.public_dns_name
