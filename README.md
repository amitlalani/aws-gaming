# aws-gaming

Based on http://lg.io/2015/07/05/revised-and-much-faster-run-your-own-highend-cloud-gaming-service-on-ec2.html

A set of Python helper scripts to simplify provisioning and deprovisioning the infrastructure required for gaming on AWS

## Prerequisite

A gaming AMI (Created using the guide above) with the name 'ec2-gaming'

## Settings
Create a copy of settings file
```
cp example-settings.py settings.py
```
Update `settings.py` with settings to match your environment

## Guide
### Spin up Python Gaming Infrastructure.
* Request Spot Instance in cheapest Availabiliy Zone checking current price is lower than maximum price defined in settings file
* Create Security Group allowing traffic on all ports from your current public IP.
* Creating EC2 Instance using latest 'ec2-gaming' image AMI

```
python gaming-up.py

```

### Spin Down Python Gaming Infrastructure.
* Create AMI snapshot of running EC2 Instance
* Delete EC2 Instance
* Delete gaming security group
* Delete spot instance request
```
python gaming-down.py
```
