import oci, os, requests, base64, json, time

config = {
    "user": os.environ.get('OCI_USER'),
    "tenancy": os.environ.get('OCI_TENANCY'),
    "fingerprint": os.environ.get('OCI_FINGERPRINT'),
    "region": os.environ.get('OCI_REGION'),
    "key_content": os.environ.get('OCI_PRIVATE_KEY'),
}

compute_client = oci.core.ComputeClient(config)

compartment_id = os.environ.get('OCI_TENANCY')
availability_domain = 'REMOVED_AD'
shape = 'REMOVED_SHAPE'
shape_config = oci.core.models.LaunchInstanceShapeConfigDetails(ocpus=REMOVED, memory_in_gbs=REMOVED)
source_details = oci.core.models.InstanceSourceViaImageDetails(image_id='REMOVED_OCID')
create_vnic_details = oci.core.models.CreateVnicDetails(subnet_id='REMOVED_OCID', assign_public_ip=True)
ssh_key = os.environ.get('SSH_PUBLIC_KEY')
metadata = {"ssh_authorized_keys": ssh_key}
display_name = 'REMOVED_NAME'

details = oci.core.models.LaunchInstanceDetails(compartment_id=compartment_id, availability_domain=availability_domain, shape=shape, shape_config=shape_config, source_details=source_details, create_vnic_details=create_vnic_details, metadata=metadata, display_name=display_name)

def get_last_run():
    github_token = os.environ.get('GITHUB_TOKEN')
    response = requests.get('https://api.github.com/repos/Bodya282010/get_instance_bot/contents/last_run.json', headers = {"Authorization": f"Bearer {github_token}"})
    timestamp = json.loads(base64.b64decode(response.json()["content"]).decode('utf-8'))["timestamp"]
    sha = base64.b64decode(response.json()["sha"]).decode('utf-8')
    return timestamp, sha

def telegram_send_message(text):
    bot_token = os.environ.get('BOT_TOKEN')
    chat_id = os.environ.get('CHAT_ID')
    requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data={"chat_id": chat_id, "text": text})

def disable_workflow():
    github_token = os.environ.get('GITHUB_TOKEN')
    requests.put('https://api.github.com/repos/Bodya282010/get_instance_bot/actions/workflows/retry.yml/disable', headers={"Authorization": f"Bearer {github_token}"})

def disable_cronjob():
    cronjob_api_key = os.environ.get('CRONJOB_API_KEY')
    cronjob_jobid = os.environ.get('CRONJOB_JOBID')
    requests.patch(f'https://api.cron-job.org/jobs/{cronjob_jobid}', headers={"Authorization": f"Bearer {cronjob_api_key}"}, json={"job": {"enabled": False}})

try:
    instance = compute_client.launch_instance(details)

    if instance.status == 200:
        print('!!!INSTANCE CREATED!!!')
        telegram_send_message('!!!INSTANCE CREATED!!!')
        disable_workflow()
        disable_cronjob()

except oci.exceptions.ServiceError as e:
    if 'Out of host capacity' in e.message:
        print('!!!NO PLACE!!!')
    else:
        print('!!!ERROR!!!\n', e.status, e.code, e.message)
        telegram_send_message('!!!ERROR!!!')

except Exception as e:
    print('!!!ERROR!!!\n', e)
    telegram_send_message('!!!ERROR!!!')
    