from urllib2 import urlopen

from base import Gaming
from settings import *


class GamingUp(Gaming):
    public_ip_endpoint = 'http://ip.42.pl/raw'
    self.my_public_ip = urlopen(public_ip_endpoint).read()
    print('My Public IP: {}'.format(self.my_public_ip))

    def launch_gaming_machine(self):
        cheapeast_az = self.get_cheapest_az()
        self.check_max_price_valid(cheapeast_az)
        self.security_group_setup()
        self.request_spot_instance()

    def get_cheapest_az(self):
        print('Finding cheapest AZ')
        prices = []
        for az in VPC_SUBNET_MAP.keys():
            prices.append(self.client.describe_spot_price_history(
                InstanceTypes=[INSTANCE_TYPE],
                ProductDescriptions=[SPOT_INSTANCE_DESCRIPTION],
                AvailabilityZone=az,
                MaxResults=1
            )['SpotPriceHistory'][0])

        cheapest_az = min(prices, key=lambda price: price['SpotPrice'])

        print "Cheapest AZ: " + \
            cheapest_az['SpotPrice'], cheapest_az['AvailabilityZone']
        return cheapest_az

    def check_max_price_valid(self, cheapest_az, max_price=None):
        if float(cheapest_az['SpotPrice']) > MAX_PRICE:
            print('Current spot price ({}) exceeeds maximum price ({})'.format(
                cheapest_az['SpotPrice'], MAX_PRICE))
            sys.exit(1)

    def security_group_setup(self):
        print('Creating Security Group')
        sec_group = self.client.create_security_group(
            GroupName='ec2-gaming',
            Description='ec2-gaming',
            VpcId=VPC_ID,
        )

        sec_group_id = sec_group['GroupId']

        self.client.authorize_security_group_ingress(
            GroupId=sec_group_id,
            IpProtocol='-1',
            CidrIp='{}/32'.format(self.my_public_ip),
        )

    def request_spot_instance(self):
        print('Requesting Spot Instance..')
        spot_request_instance = self.client.request_spot_instances(
            SpotPrice=str(MAX_PRICE),
            LaunchSpecification={
                'ImageId': image['ImageId'],
                'SecurityGroupIds': [sec_group_id],
                'InstanceType': INSTANCE_TYPE,
                'SubnetId': VPC_SUBNET_MAP[cheapest_az['AvailabilityZone']],
            }
        )['SpotInstanceRequests'][0]

        spot_request_id = spot_request_instance['SpotInstanceRequestId']

        self.ec2.create_tags(
            Resources=[spot_request_id],
            Tags=[
                {
                    'Key': 'Name',
                    'Value': 'ec2-gaming'
                }
            ]
        )

        print('Waiting for Spot Request to be fulfilled')
        waiter = self.client.get_waiter('spot_instance_request_fulfilled')
        waiter.wait(SpotInstanceRequestIds=[spot_request_id])

        instance_id = self.client.describe_spot_instance_requests(
            SpotInstanceRequestIds=[spot_request_id]
        )['SpotInstanceRequests'][0]['InstanceId']

        print('Waiting for Instance to be ready')
        waiter = self.client.get_waiter('instance_status_ok')
        waiter.wait(
            InstanceIds=[instance_id]
        )

        print('Instance Ready. Hostname:')
        instance = self.ec2.Instance(instance_id)
        print instance.public_dns_name


if __name__ == "__main__":
    GamingUp().launch_gaming_machine()
