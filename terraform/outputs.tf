output "access_key_id" {
  value = aws_iam_access_key.access_key.id
}

output "secret_access_key" {
  value     = aws_iam_access_key.access_key.secret
  sensitive = true
}

output "bucket_name" {
  value = aws_s3_bucket.photoalbum.bucket
}