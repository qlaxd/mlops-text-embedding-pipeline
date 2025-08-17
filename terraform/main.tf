provider "aws" {
  region = var.aws_region
}

# Data source for the existing S3 bucket
data "aws_s3_bucket" "existing" {
  bucket = var.s3_bucket_name
}

# Ensure versioning is enabled on the existing bucket
resource "aws_s3_bucket_versioning" "versioning" {
  bucket = data.aws_s3_bucket.existing.id
  versioning_configuration {
    status = "Enabled"
  }
}

# ECR repository to store the Docker image
resource "aws_ecr_repository" "main" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"
}

# CloudWatch log group for the ECS task
resource "aws_cloudwatch_log_group" "main" {
  name = "/ecs/${var.project_name}"
}

# IAM role for ECS task execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.project_name}-exec-role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = [
            "ecs-tasks.amazonaws.com",
            "scheduler.amazonaws.com"
            ]
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM role for the application running in the ECS task
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-task-role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy to allow the task to write to the S3 bucket
resource "aws_iam_policy" "s3_write_policy" {
  name        = "${var.project_name}-s3-write-policy"
  description = "Allows writing objects to the S3 bucket"
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Action   = [
          "s3:PutObject"
        ]
        Effect   = "Allow"
        Resource = "${data.aws_s3_bucket.existing.arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "task_s3_write_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.s3_write_policy.arn
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"
}

# ECS Task Definition for Fargate
resource "aws_ecs_task_definition" "main" {
  family                   = var.project_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"  # 0.25 vCPU
  memory                   = "512"  # 0.5 GB
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "${var.project_name}-app"
      image     = "${aws_ecr_repository.main.repository_url}:latest"
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.main.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      environment = [
        {
          name  = "S3_BUCKET_NAME"
          value = var.s3_bucket_name
        }
      ]
    }
  ])
}

# Default VPC and subnets for the EventBridge target
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# EventBridge Scheduler to run the task daily
resource "aws_scheduler_schedule" "daily_run" {
  name       = "${var.project_name}-daily-run"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(1 day)"

  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.ecs_task_execution_role.arn # A role with permissions to run tasks

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.main.arn
      launch_type         = "FARGATE"
      network_configuration {
        subnets         = data.aws_subnets.default.ids
        assign_public_ip = true
      }
    }
  }
}
