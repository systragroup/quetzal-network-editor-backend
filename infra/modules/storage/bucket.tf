resource "aws_s3_bucket" "storage" {
    bucket  = var.bucket_name
    tags    = var.tags
}

resource "aws_s3_bucket_cors_configuration" "storage" {
    bucket = aws_s3_bucket.storage.id
    cors_rule {
        allowed_headers = ["*"]
        allowed_methods = [ "GET", "HEAD","PUT","POST","DELETE"]
        allowed_origins = ["http://localhost:8081",
                "https://systragroup.github.io"]
        expose_headers  = ["x-amz-server-side-encryption",
                "x-amz-meta-user_email",
                "Access-Control-Allow-Origin",
                "x-amz-request-id",
                "x-amz-id-2",
                "ETag"]
        max_age_seconds = 3000
    }
}

resource "aws_s3_bucket_lifecycle_configuration" "l1" {
  bucket = aws_s3_bucket.storage.id
  rule {
    status = "Enabled"
    id     = "expire"
    expiration {
        days = 4
    }
  }
}