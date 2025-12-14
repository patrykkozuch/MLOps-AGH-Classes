variable "regions" {
  type    = list(string)
  default = ["us-east-1", "us-west-1"]
}

variable "bucket_name_prefix" {
  type    = string
  default = "agh-mlops-lab10-refactor"
}