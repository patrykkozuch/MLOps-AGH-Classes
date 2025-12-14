locals {
  visibility = var.is_private ? "private" : "public"
}

resource "github_repository" "example" {
  name        = var.repository_name
  description = var.repository_description
  visibility  = local.visibility
  auto_init   = true
}
