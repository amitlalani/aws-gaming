import time

from base import client, ec2
from botocore import exceptions
from settings import *

print('# Cleanup AMI + Snapshot')
print('Finding Gaming Image:')
try:
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
    client.deregister_image(ImageId=image['ImageId'])
    time.sleep(30)

    print('# Cleanup Snapshots')
    snapshots = client.describe_snapshots(OwnerIds=['self'])['Snapshots']
    for snapshot in snapshots:
        if image['ImageId'] in snapshot['Description']:
            client.delete_snapshot(
                SnapshotId=snapshot['SnapshotId']
            )
except IndexError:
    print 'Cannot Find Gaming AMI. Continuing....'


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
#import ipdb ; ipdb.set_trace()
sec_group = instance.security_groups


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
response = client.cancel_spot_instance_requests(
    SpotInstanceRequestIds=[spot_request['SpotInstanceRequestId']]
)

print('# Delete Security Grouip')
client.delete_security_group(
    GroupId=sec_group[0]['GroupId']
)
