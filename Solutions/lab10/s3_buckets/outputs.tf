output "bucket_arn" {
    value = {
        (var.regions[0]) = aws_s3_bucket.s3_bucket_east.arn
        (var.regions[1]) = aws_s3_bucket.s3_bucket_west.arn
    }

}

output "bucket_region" {
    value = {
        (var.regions[0]) = aws_s3_bucket.s3_bucket_east.region
        (var.regions[1]) = aws_s3_bucket.s3_bucket_west.region
    }
}