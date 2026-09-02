#!/usr/bin/env bash
# Provision (or reuse) an EC2 instance and security group for CLIWS.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=aws-env.sh
source "${SCRIPT_DIR}/aws-env.sh"

require_aws_credentials
require_key_name

VPC_ID="$(get_default_vpc_id)"
if [[ -z "${VPC_ID}" || "${VPC_ID}" == "None" ]]; then
  echo "No default VPC found in ${AWS_REGION}." >&2
  exit 1
fi

SECURITY_GROUP_ID="$(
  aws_cli ec2 describe-security-groups \
    --filters "Name=group-name,Values=${EC2_SECURITY_GROUP_NAME}" "Name=vpc-id,Values=${VPC_ID}" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || true
)"

if [[ -z "${SECURITY_GROUP_ID}" || "${SECURITY_GROUP_ID}" == "None" ]]; then
  echo "Creating security group ${EC2_SECURITY_GROUP_NAME}..."
  SECURITY_GROUP_ID="$(
    aws_cli ec2 create-security-group \
      --group-name "${EC2_SECURITY_GROUP_NAME}" \
      --description "CLIWS SSH and HTTPS access" \
      --vpc-id "${VPC_ID}" \
      --query 'GroupId' \
      --output text
  )"
  aws_cli ec2 authorize-security-group-ingress \
    --group-id "${SECURITY_GROUP_ID}" \
    --ip-permissions \
      IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges='[{CidrIp=0.0.0.0/0,Description=SSH}]' \
      IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges='[{CidrIp=0.0.0.0/0,Description=HTTPS}]'
  aws_cli ec2 create-tags \
    --resources "${SECURITY_GROUP_ID}" \
    --tags "Key=Name,Value=${EC2_SECURITY_GROUP_NAME}" "Key=Project,Value=cliws"
else
  echo "Reusing security group ${SECURITY_GROUP_ID}"
fi

INSTANCE_ID="$(find_instance_by_name)"
if [[ "${EC2_FORCE_NEW_INSTANCE}" == "true" && -n "${INSTANCE_ID}" && "${INSTANCE_ID}" != "None" ]]; then
  echo "Terminating existing instance ${INSTANCE_ID} (EC2_FORCE_NEW_INSTANCE=true)..."
  aws_cli ec2 terminate-instances --instance-ids "${INSTANCE_ID}" >/dev/null
  aws_cli ec2 wait instance-terminated --instance-ids "${INSTANCE_ID}"
  INSTANCE_ID=""
fi

if [[ -z "${INSTANCE_ID}" || "${INSTANCE_ID}" == "None" ]]; then
  AMI_ID="$(get_latest_ami_id)"
  echo "Launching ${EC2_INSTANCE_TYPE} instance with AMI ${AMI_ID}..."

  INSTANCE_ID="$(
    aws_cli ec2 run-instances \
      --image-id "${AMI_ID}" \
      --instance-type "${EC2_INSTANCE_TYPE}" \
      --key-name "${EC2_KEY_NAME}" \
      --security-group-ids "${SECURITY_GROUP_ID}" \
      --associate-public-ip-address \
      --block-device-mappings "[{\"DeviceName\":\"/dev/xvda\",\"Ebs\":{\"VolumeSize\":${EC2_VOLUME_SIZE_GB},\"DeleteOnTermination\":true,\"VolumeType\":\"gp3\"}}]" \
      --tag-specifications \
        "ResourceType=instance,Tags=[{Key=Name,Value=${EC2_INSTANCE_NAME}},{Key=Project,Value=cliws}]" \
      --metadata-options "HttpTokens=optional,HttpEndpoint=enabled" \
      --query 'Instances[0].InstanceId' \
      --output text
  )"
else
  echo "Reusing instance ${INSTANCE_ID}"
  STATE="$(aws_cli ec2 describe-instances --instance-ids "${INSTANCE_ID}" --query 'Reservations[0].Instances[0].State.Name' --output text)"
  if [[ "${STATE}" == "stopped" ]]; then
    echo "Starting stopped instance ${INSTANCE_ID}..."
    aws_cli ec2 start-instances --instance-ids "${INSTANCE_ID}" >/dev/null
  fi
fi

wait_for_instance_status "${INSTANCE_ID}"
PUBLIC_IP="$(get_instance_public_ip "${INSTANCE_ID}")"

if [[ -z "${PUBLIC_IP}" || "${PUBLIC_IP}" == "None" ]]; then
  echo "Instance ${INSTANCE_ID} has no public IP." >&2
  exit 1
fi

echo "INSTANCE_ID=${INSTANCE_ID}"
echo "PUBLIC_IP=${PUBLIC_IP}"
echo "SECURITY_GROUP_ID=${SECURITY_GROUP_ID}"

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "instance_id=${INSTANCE_ID}"
    echo "public_ip=${PUBLIC_IP}"
    echo "security_group_id=${SECURITY_GROUP_ID}"
  } >> "${GITHUB_OUTPUT}"
fi
