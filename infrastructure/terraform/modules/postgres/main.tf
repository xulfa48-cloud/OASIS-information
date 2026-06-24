// placeholder main.tf for a postgres module - vendor-specific details omitted

provider "random" {}

resource "random_pet" "db" {
  length = 2
}
