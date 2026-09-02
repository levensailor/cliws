#!/usr/bin/env bash
# Shared AWS deployment defaults for CLIWS EC2 provisioning.
set -euo pipefail

export AWS_REGION="${AWS_REGION:-us-east-1}"
export EC2_INSTANCE_TYPE="${EC2_INSTANCE_TYPE:-t3.micro}"
export EC2_INSTANCE_NAME="${EC2_INSTANCE_NAME:-cliws}"
export EC2_SECURITY_GROUP_NAME="${EC2_SECURITY_GROUP_NAME:-${EC2_INSTANCE_NAME}-sg}"
export EC2_VOLUME_SIZE_GB="${EC2_VOLUME_SIZE_GB:-8}"
export EC2_KEY_NAME="${EC2_KEY_NAME:-}"
export EC2_FORCE_NEW_INSTANCE="${EC2_FORCE_NEW_INSTANCE:-false}"
export EC2_AMI_PARAMETER="${EC2_AMI_PARAMETER:-/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64}"

require_aws_credentials() {
  if [[ -z "${AWS_ACCESS_KEY_ID:-}" || -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
    echo "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set." >&2
    exit 1
  fi
}

require_key_name() {
  if [[ -z "${EC2_KEY_NAME}" ]]; then
    echo "EC2_KEY_NAME must be set to an existing AWS EC2 key pair name." >&2
    exit 1
  fi
}

aws_cli() {
  aws --region "${AWS_REGION}" "$@"
}

get_default_vpc_id() {
  aws_cli ec2 describe-vpcs \
    --filters Name=isDefault,Values=true \
    --query 'Vpcs[0].VpcId' \
    --output text
}

get_latest_ami_id() {
  aws_cli ssm get-parameters \
    --names "${EC2_AMI_PARAMETER}" \
    --query 'Parameters[0].Value' \
    --output text
}

find_instance_by_name() {
  aws_cli ec2 describe-instances \
    --filters \
      "Name=tag:Name,Values=${EC2_INSTANCE_NAME}" \
      "Name=instance-state-name,Values=pending,running,stopping,stopped" \
    --query 'Reservations[].Instances[] | sort_by(@, &LaunchTime) | [-1].InstanceId' \
    --output text
}

get_instance_public_ip() {
  local instance_id="$1"
  aws_cli ec2 describe-instances \
    --instance-ids "${instance_id}" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text
}

wait_for_instance_status() {
  local instance_id="$1"
  aws_cli ec2 wait instance-running --instance-ids "${instance_id}"
  aws_cli ec2 wait instance-status-ok --instance-ids "${instance_id}"
}
