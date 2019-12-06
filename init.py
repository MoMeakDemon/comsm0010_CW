import logging
from botocore.exceptions import ClientError
import boto3
import paramiko
from scp import SCPClient
import multiprocessing as mp
import time


def create_ec2_instance(image_id, instance_type, keypair_name, GroupName, instance_number):

    ec2_client = boto3.client('ec2')
    try:
        response = ec2_client.run_instances(ImageId=image_id,
                                            InstanceType=instance_type,
                                            KeyName=keypair_name,
                                            SecurityGroups=[GroupName,],
                                            MinCount=instance_number,
                                            MaxCount=instance_number)
    except ClientError as e:
        logging.error(e)
        return None
    return list(response['Instances'])

def task(zeros, ranges, margin, public_ip):
    key = paramiko.RSAKey.from_private_key_file("") #pls put key file location
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ec2 = boto3.resource('ec2')
    try:
        client.connect(hostname=public_ip, username="ubuntu", pkey=key)
        scp = SCPClient(client.get_transport())
        scp.put('Task_T.py', recursive=True, remote_path='/home/ubuntu')
        stdin, stdout, stderr = client.exec_command('python3 Task_T.py' + ' ' + str(zeros) + ' ' + str(ranges) + ' ' + str(margin))

        data = stdout.read().splitlines()
        for line in data:
            if (line.decode()):
                print(line.decode())
                client.close()
                ec2.instances.filter(
                    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]).terminate()
    except Exception as e:
        print(e)


def multi_processing(zeros, ranges, p_num):
    start = time.perf_counter()
    image_id = 'ami-04b9e92b5572fa0d1'
    instance_type = 't2.micro'
    keypair_name = '' #key pair name
    GroupName = ''  #group name
    instance_number = p_num
    instance_info = create_ec2_instance(image_id, instance_type, keypair_name, GroupName, instance_number)
    ids = []
    for i in range(len(instance_info)):
        ids.append(instance_info[i]["InstanceId"])
    print(ids)
    ec2 = boto3.resource('ec2')
    for instance in ec2.instances.filter(InstanceIds=ids):
        while instance.state['Name'] != 'running':
            print("...instance is %s" % instance.state['Name'])
            time.sleep(1)
            instance.load()
    time.sleep(10)
    print("all instance are good!")
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    IPs = []
    for instance in instances:
        IPs.append(instance.public_ip_address)
    zero_list = [zeros] * p_num
    range_list = range(1,p_num+1)
    margin_list = [int(2**(ranges)/p_num)] * p_num
    inputs = list(zip(zero_list, range_list, margin_list, IPs))
    p = mp.Pool(processes=p_num)
    start1 = time.perf_counter()
    result = p.starmap(task, inputs)
    finish1 = time.perf_counter()
    print(f'Finished in {round(finish1 - start1, 2)} second(s)')
    p.close()
    p.join()
    finish = time.perf_counter()
    print(f'Finished in {round(finish - start, 2)} second(s)')

if __name__ == '__main__':
    multi_processing(16,32,8)