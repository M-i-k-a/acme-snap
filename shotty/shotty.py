import boto3
import botocore
import click

session = boto3.Session(profile_name='acme-snap')
ec2 = session.resource('ec2')

def filter_instances(project):
  instances = []

  if project:
    print('Project filter {0}'.format(project))
    filters = [{'Name':'tag:Project', 'Values':[project]}]
    instances = ec2.instances.filter(Filters=filters)
  else:
    instances = ec2.instances.all()
  return instances

def has_pending_snapshots(volume):
  snapshots = list(volume.snapshots.all())
  return snapshots and snapshots[0].state == 'pending'
@click.group()
def cli():
  """Shotty manages snapshots"""

@cli.group('snapshots')
def snapshots():
  """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default=None,
  help='Only snapshots for project (tag Project:<name>)')
@click.option('--all', 'list_all', default=False, is_flag=True,
  help='List all snapshots for each volume, not just the most recent')

def list_snapshots(project, list_all):
  "List EC2 snapshots"
  print('List of snapshots')

  instances = filter_instances(project)

  for i in instances:
    for v in i.volumes.all():
      for s in v.snapshots.all():
        print(', '.join((
          s.id,
          v.id,
          i.id,
          s.state,
          s.progress,
          s.start_time.strftime('%c')
          )))

        if s.state == 'completed' and not list_all: break
  return

@cli.group('volumes')
def volumes():
  """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default=None,
  help='Only volumes for project (tag Project:<name>)')

def list_volumes(project):
  "List EC2 volumes"
  print('List of volumes')

  instances = filter_instances(project)

  for i in instances:
    for v in i.volumes.all():
      print(', '.join((
        v.id,
        i.id,
        v.state,
        str(v.size) + 'GB',
        v.encrypted and 'Encrypted' or 'Not encrypted'
        )))
  return

@cli.group('instances')
def instances():
  """Commands for instances"""

@instances.command('snapshot', 
  help='Create snapshot of all images')
@click.option('--project', default=None,
  help='Only instances for project (tag Project:<name>)')

def create_snapshots(project):
  "Create snapshots for EC2 instance"
  print('List of instances')

  instances = filter_instances(project)
  for i in instances:
    print('Stopping {0}...'.format(i.id))
    i.stop()
    i.wait_until_stopped()
    
    for v in i.volumes.all():
      if has_pending_snapshots(v):
        print('Skipping {0}, snapshot already in progress'.format(v.id))
        continue

      print('Creating snapshot of {0}...'.format(v.id))
      v.create_snapshot(Description='Crerated by Snappy')
    
    print('Starting {0}...'.format(i.id))
    i.start()
    i.wait_until_running()
  print('''Job's done!''')
  return

@instances.command('list')
@click.option('--project', default=None,
  help='Only instances for project (tag Project:<name>)')


def list_instances(project):
  "List EC2 instances"
  print('List of instances')

  instances = filter_instances(project)

  for i in instances:
    tags = { t['Key']: t['Value'] for t in i.tags or []}
    print(', '.join((
      i.id,
      i.instance_type,
      i.placement['AvailabilityZone'],
      i.state['Name'],
      tags.get('Project', '<no project>'),
      i.public_dns_name
      )))
  return

@instances.command('stop')
@click.option('--project', default=None,
  help='Only instances for project (tag Project:<name>)')

def stop_instances(project):
  'Stop EC2 instances'
  print('Stop instances')

  instances = filter_instances(project)
  
  for i in instances:
    print('Stoppin {0}...'.format(i.id))
    try:
      i.stop()
    except botocore.exceptions.ClientError as e:
      print('Could not stop {0}. '.format(i.id) + str(e))
      continue
  return

@instances.command('start')
@click.option('--project', default=None,
  help='Only instances for project (tag Project:<name>)')

def start_instances(project):
  'Start EC2 instances'
  print('Start instances')

  instances = filter_instances(project)
  
  for i in instances:
    print('Starting {0}...'.format(i.id))
    try:
      i.start()
    except botocore.exceptions.ClientError as e:
      print('Could not start {0}. '.format(i.id) + str(e))
      continue
  return

if __name__ == '__main__':
  cli()
