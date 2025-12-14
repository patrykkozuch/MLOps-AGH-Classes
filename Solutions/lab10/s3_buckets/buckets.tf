resource "random_id" "bucket" {
  count       = length(var.regions)
  byte_length = 8
}

resource "aws_s3_bucket" "s3_bucket_east" {
  bucket   = "${var.bucket_name_prefix}-east-${random_id.bucket[0].hex}"
  provider = aws.us_east_1
}

resource "aws_s3_bucket_versioning" "s3_east_bucket_versioning" {
  bucket   = aws_s3_bucket.s3_bucket_east.id
  provider = aws.us_east_1

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "s3_east_bucket_lifecycle" {
  bucket = aws_s3_bucket.s3_bucket_east.id
  provider = aws.us_east_1

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    filter {
      prefix = "" # Apply to all objects
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket" "s3_bucket_west" {
  bucket   = "${var.bucket_name_prefix}-west-${random_id.bucket[1].hex}"
  provider = aws.us_west_1
}

resource "aws_s3_bucket_versioning" "s3_west_bucket_versioning" {
  bucket   = aws_s3_bucket.s3_bucket_west.id
  provider = aws.us_west_1

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "s3_west_bucket_lifecycle" {
  bucket = aws_s3_bucket.s3_bucket_west.id
  provider = aws.us_west_1

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    filter {
      prefix = "" # Apply to all objects
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}