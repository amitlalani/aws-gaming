from settings import *
import boto3


class Gaming(object):
    def __init__(self):
        self.client = boto3.client(
            'ec2',
            region_name=REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        self.ec2 = boto3.resource(
            'ec2',
            region_name=REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

    def find_gaming_image(self):
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

        return image
