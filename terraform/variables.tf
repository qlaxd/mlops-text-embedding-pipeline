variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "The name of the project."
  type        = string
  default     = "mlops-text-embedding-pipeline"
}

variable "s3_bucket_name" {
  description = "The name of the S3 bucket for storing embeddings and metadata."
  type        = string
  default     = "mlopsprojectbucket"
}
