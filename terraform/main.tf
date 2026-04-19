terraform {
  backend "s3" {
    bucket = "photoalbum-skicpausz-media"
    key    = "terraform/state.tfstate"
    region = "eu-north-1"
  }
}

provider "aws" {
  region = "eu-north-1"
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

variable "kubeconfig_path" {
  type = string
}

# -----------------------
# S3 BUCKET
# -----------------------
resource "aws_s3_bucket" "photoalbum" {
  bucket = "photoalbum-skicpausz-media"

  tags = {
    Name = "PhotoAlbumBucket"
  }
}

# -----------------------
# PUBLIC READ POLICY
# -----------------------
resource "aws_s3_bucket_policy" "public_read" {
  bucket = aws_s3_bucket.photoalbum.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject"]
        Resource  = "${aws_s3_bucket.photoalbum.arn}/*"
      }
    ]
  })
}

# -----------------------
# IAM USER
# -----------------------
resource "aws_iam_user" "photoalbum_user" {
  name = "photoalbum-django"
}

# -----------------------
# IAM POLICY (restricted to bucket)
# -----------------------
resource "aws_iam_policy" "photoalbum_policy" {
  name = "PhotoAlbumS3Access"

    policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
        {
        Sid = "AllowPhotoBucketAccess"
        Effect = "Allow"
        Action = [
            "s3:PutObject",
            "s3:GetObject",
            "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.photoalbum.arn}/*"
        },
        {
        Sid = "AllowBucketAccess"
        Effect = "Allow"
        Action = [
            "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.photoalbum.arn
        }
    ]
    })
}

# -----------------------
# ATTACH POLICY
# -----------------------
resource "aws_iam_user_policy_attachment" "attach_policy" {
  user       = aws_iam_user.photoalbum_user.name
  policy_arn = aws_iam_policy.photoalbum_policy.arn
}

# -----------------------
# ACCESS KEY
# -----------------------
resource "aws_iam_access_key" "access_key" {
  user = aws_iam_user.photoalbum_user.name
}

# -----------------------
# OPENSHIFT SECRET (AUTO SYNC)
# -----------------------
resource "kubernetes_secret_v1" "s3_credentials" {
  metadata {
    name      = "s3-credentials"
    namespace = "skicpausz-dev" 
  }

  data = {
    AWS_ACCESS_KEY_ID       = aws_iam_access_key.access_key.id
    AWS_SECRET_ACCESS_KEY   = aws_iam_access_key.access_key.secret
    AWS_STORAGE_BUCKET_NAME = aws_s3_bucket.photoalbum.bucket
  }

  type = "Opaque"
}

#trigger 