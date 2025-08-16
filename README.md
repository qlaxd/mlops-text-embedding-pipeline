# MLOps Embedding Pipeline

This project implements a batch embedding pipeline as per the OPSWAT MLOps Engineer Test.

## Features

- Processes text from a file (`data.txt`).
- Chunks long texts to fit the model's context window.
- Generates vector embeddings using a pre-trained model.
- Stores embeddings and run metadata in a versioned S3 bucket.
- All infrastructure is managed via Terraform.
- The application is containerized with Docker.
- Includes a CI/CD pipeline using GitHub Actions to deploy the Docker image to ECR.

## How to Run

### Local Development

1.  **Setup Environment:**
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configure AWS:**
    Make sure your AWS credentials are set up (e.g., `~/.aws/credentials` or environment variables).

3.  **Run the pipeline:**
    ```bash
    python -m src.main
    ```

### Deployment

1.  **Deploy Infrastructure:**
    Navigate to the `terraform` directory and run:
    ```bash
    terraform init
    terraform apply -var="s3_bucket_name=your-globally-unique-bucket-name"
    ```

2.  **CI/CD:**
    - Configure `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in your GitHub repository secrets.
    - Pushing to the `main` branch will automatically build and push the Docker image to the ECR repository created by Terraform.

3.  **Triggering the pipeline:**
    The pipeline is scheduled to run daily via an AWS EventBridge rule. You can also trigger it manually in the AWS ECS console.
