import time

from base import Gaming
from botocore import exceptions
from settings import *


class GamingDown(Gaming):
    def gaming_image_cleanup(self):
        # get image from base class method
        client.deregister_image(ImageId=image['ImageId'])
        time.sleep(30)

        print('# Cleanup Snapshots')
        snapshots = client.describe_snapshots(OwnerIds=['self'])['Snapshots']
        for snapshot in snapshots:
            if image['ImageId'] in snapshot['Description']:
                client.delete_snapshot(
                    SnapshotId=snapshot['SnapshotId']
                )

    def find_spot_request(self):
        print('# Get Request Information')
        spot_request = client.describe_spot_instance_requests(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': ['ec2-gaming']
                },
                {
                    'Name': 'state',
                    'Values': ['active']
                }
            ]
        )['SpotInstanceRequests'][0]

        spot_request_instance = spot_request['InstanceId']

        instance = ec2.Instance(spot_request_instance)
        return instance

    def create_gaming_image(self):
        print('# Create new AMI')
        image = instance.create_image(Name='ec2-gaming')
        try:
            time.sleep(60)
            waiter = client.get_waiter('image_available')
            waiter.wait(ImageIds=[image.id])
        except exceptions.WaiterError:
            print('Still waiting for Image to be be ready')
            waiter.wait(ImageIds=[image.id])

        print('# Delete Instance')
        instance.terminate()
        waiter = client.get_waiter('instance_terminated')
        waiter.wait(
            InstanceIds=[spot_request_instance]
        )

        print('# Cancel Spot Request')
        client.cancel_spot_instance_requests(
            SpotInstanceRequestIds=[spot_request['SpotInstanceRequestId']]
        )

    def security_group_cleanup(self):
        print('# Delete Security Grouip')
        sec_group = instance.security_groups
        client.delete_security_group(
            GroupId=sec_group[0]['GroupId']
        )
