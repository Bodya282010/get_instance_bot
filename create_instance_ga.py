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
availability_domain = os.environ.get('AVAILABILITY_DOMAIN')
shape = os.environ.get('SHAPE')
shape_config = oci.core.models.LaunchInstanceShapeConfigDetails(ocpus=float(os.environ.get('SHAPE_CONFIG_OCPUS')), memory_in_gbs=float(os.environ.get('SHAPE_CONFIG_MEMORY_IN_GBS')))
source_details = oci.core.models.InstanceSourceViaImageDetails(image_id=os.environ.get('SOURCE_DETAILS_IMAGE_ID'), boot_volume_size_in_gbs=int(os.environ.get('SOURCE_DETAILS_BOOT_VOLUME_SIZE_IN_GBS')))
create_vnic_details = oci.core.models.CreateVnicDetails(subnet_id=os.environ.get('CREATE_VNIC_DETAILS_SUBNET_ID'), assign_public_ip=True)
ssh_key = os.environ.get('SSH_PUBLIC_KEY')
metadata = {"ssh_authorized_keys": ssh_key}
display_name = os.environ.get('DISPLAY_NAME')

details = oci.core.models.LaunchInstanceDetails(compartment_id=compartment_id, availability_domain=availability_domain, shape=shape, shape_config=shape_config, source_details=source_details, create_vnic_details=create_vnic_details, metadata=metadata, display_name=display_name)

def get_last_run():
    github_token = os.environ.get('GITHUB_TOKEN')
    response = requests.get('https://api.github.com/repos/Bodya282010/get_instance_bot/contents/last_run.json', headers = {"Authorization": f"Bearer {github_token}"})
    response.raise_for_status()
    timestamp = json.loads(base64.b64decode(response.json()["content"]).decode('utf-8'))["timestamp"]
    sha = response.json()["sha"]
    return timestamp, sha

def update_last_run(sha):
    github_token = os.environ.get('GITHUB_TOKEN')
    
    raw_dict = {"timestamp": time.time()}
    dict_str = json.dumps(raw_dict)
    dict_bytes = dict_str.encode('utf-8')
    dictb64 = base64.b64encode(dict_bytes)
    dictb64_str = dictb64.decode('utf-8')

    response = requests.put('https://api.github.com/repos/Bodya282010/get_instance_bot/contents/last_run.json', json={"message": "updating_last_run_time", "content": dictb64_str, "sha": sha}, headers={"Authorization": f"Bearer {github_token}"})
    response.raise_for_status()

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
    timestamp, sha = get_last_run()
    
    if time.time() - timestamp >= 270:
        update_last_run(sha)
        instance = compute_client.launch_instance(details)

        if instance.status == 200:
            print('!!!INSTANCE CREATED!!!')
            telegram_send_message('!!!INSTANCE CREATED!!!')
            disable_workflow()
            disable_cronjob()

    else:
        print('!!!TOO EARLY REQUEST!!!')

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 409:
        print('!!!FILE IS ALREADY CHANGED!!!', e.response.text)
    else:
        print('!!!ERROR!!!', e.response.status_code, e.response.text)
        telegram_send_message('!!!ERROR!!!')

except requests.exceptions.RequestException as e:
    print('!!!ERROR!!!', e)
    telegram_send_message('!!!ERROR!!!')

except oci.exceptions.ServiceError as e:
    if 'Out of host capacity' in e.message:
        print('!!!NO PLACE!!!')
    else:
        print('!!!ERROR!!!', e.status, e.code, e.message)
        telegram_send_message('!!!ERROR!!!')

except Exception as e:
    print('!!!ERROR!!!', e)
    telegram_send_message('!!!ERROR!!!')
