
output "instance_id" {
  description = "The unique identifier for the provisioned EC2 instance."
  value       = aws_instance.app_server.id
}

output "instance_state" {
  description = "The state of the EC2 instance (e.g., running, stopped)."
  value       = aws_instance.app_server.instance_state
}

output "instance_type" {
  description = "The type of EC2 instance (e.g., t2.micro, m5.large)."
  value       = aws_instance.app_server.instance_type
}

output "availability_zone" {
  description = "The Availability Zone where the EC2 instance is deployed."
  value       = aws_instance.app_server.availability_zone
}

output "public_dns" {
  description = "The public DNS name assigned to the EC2 instance."
  value       = aws_instance.app_server.public_dns
}

output "public_ip" {
  description = "The public IP address assigned to the EC2 instance."
  value       = aws_instance.app_server.public_ip
}

output "private_dns" {
  description = "The private DNS name assigned to the EC2 instance within its VPC."
  value       = aws_instance.app_server.private_dns
}

output "private_ip" {
  description = "The private IP address assigned to the EC2 instance within its VPC."
  value       = aws_instance.app_server.private_ip
}

output "monitoring" {
  description = "Indicates if detailed monitoring is enabled for the EC2 instance."
  value       = aws_instance.app_server.monitoring
}

output "security_group_ids" {
  description = "The list of security group IDs assigned to the EC2 instance."
  value       = aws_instance.app_server.vpc_security_group_ids
}

output "key_name" {
  description = "The name of the key pair associated with the EC2 instance."
  value       = aws_instance.app_server.key_name
}

output "subnet_id" {
  description = "The ID of the subnet to which the instance is attached."
  value       = aws_instance.app_server.subnet_id
}

output "tags" {
  description = "A map of tags assigned to the resource."
  value       = aws_instance.app_server.tags
}
