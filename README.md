# MLOps Text Embedding Pipeline

This project implements a batch embedding pipeline that encodes text into vector embeddings using a HuggingFace-compatible model. The entire infrastructure is deployed on AWS using Terraform, and the application is containerized with Docker.

## Features

- Processes text from a file (`data.txt`).
- Chunks long texts to fit the model's context window (2048 tokens).
- Generates vector embeddings using a pre-trained Sentence Transformer model.
- Stores embeddings and run metadata in a versioned S3 bucket for auditability.
- All AWS infrastructure is managed as code using Terraform.
- The application is containerized with Docker for consistent environments.
- Scheduled to run daily via an AWS EventBridge rule.

---

## Prerequisites

Before you begin, ensure you have the following installed and configured:

1.  **AWS CLI:** [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
    -   Make sure it's configured with your credentials (`aws configure`).
2.  **Terraform:** [Installation Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli)
3.  **Docker:** [Installation Guide](https://docs.docker.com/engine/install/)

---

## Local Development & Testing

These steps allow you to run and test the pipeline on your local machine.

1.  **Create a Python Virtual Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Up Environment Variables:**
    The application uses an `.env` file for local configuration. Create one from the example:
    ```bash
    # Create a .env file and set your test bucket name
    echo "S3_BUCKET_NAME=your-local-test-bucket-name" > .env
    ```

4.  **Run with Docker Compose:**
    This is the recommended way to test locally as it closely mimics the production environment.
    ```bash
    docker-compose up --build
    ```
    *Note: We discovered a host-specific Docker networking issue during development. The `docker-compose.yml` is now configured to use `network_mode: bridge`, which is a stable workaround for such local environment problems.*

---

## AWS Deployment Guide

This is a step-by-step guide to deploy the entire pipeline to your AWS account.

### Step 1: Configure Deployment Variables

All infrastructure variables are in `terraform/variables.tf`. The most important one is `s3_bucket_name`.

-   **Option A (Recommended):** Create a `terraform.tfvars` file inside the `terraform/` directory to specify your unique S3 bucket name.
    ```hcl
    # terraform/terraform.tfvars
    s3_bucket_name = "your-globally-unique-bucket-name-here"
    ```
-   **Option B:** You can use the default bucket name (`mlopsprojectbucket`), but it must be globally unique. If it's taken, the deployment will fail.

### Step 2: Deploy AWS Infrastructure

This command will provision all the necessary AWS resources (S3, ECR, ECS, etc.).

```bash
cd terraform
terraform init
terraform apply --auto-approve
```
This process may take a few minutes.

### Step 3: Build and Push Docker Image to ECR

Now that Terraform has created the ECR repository, we can build our application's Docker image and push it there.

1.  **Get the ECR Repository URL:**
    ```bash
    # Ensure you are still in the terraform/ directory
    ECR_URL=$(terraform output -raw ecr_repository_url)
    ```

2.  **Log in to AWS ECR:**
    This command retrieves a temporary password and logs Docker into the AWS ECR registry.
    ```bash
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(echo $ECR_URL | cut -d'/' -f1)
    ```

3.  **Build and Push the Image:**
    Navigate back to the project root directory to run the build.
    ```bash
    cd ..
    docker build -t $ECR_URL:latest .
    docker push $ECR_URL:latest
    ```

### Step 4: Run the Pipeline on AWS

The system is now fully deployed. The pipeline will run automatically once a day. You can also trigger it manually for testing.

1.  **Navigate to the ECS Console:** Go to the Amazon ECS service in the AWS Management Console.
2.  **Find Your Cluster:** Select **Clusters** and click on `mlops-text-embedding-pipeline-cluster`.
3.  **Run a New Task:**
    -   Click the **Tasks** tab, then click **Run new task**.
    -   **Launch type:** Select `FARGATE`.
    -   **Task definition:** Select the `mlops-text-embedding-pipeline` task definition.
    -   **Networking:** Select the `default` VPC and all of its subnets. Ensure **Public IP** is `ENABLED`.
    -   Click **Run task**.

After a few minutes, the task will complete. You can verify the results by:
-   **Checking the S3 bucket:** The `embeddings/` and `metadata/` folders should contain new JSON files.
-   **Checking the logs:** The logs are available in the **CloudWatch** service, under the `/ecs/mlops-text-embedding-pipeline` log group.

---

## Destroying the Infrastructure

To remove all the AWS resources created by this project, navigate to the `terraform` directory and run:

```bash
cd terraform
terraform destroy --auto-approve
```