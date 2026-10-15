# To merge all modules
# ------------------------------------------------------------ Root main.tf

# ------------------------------------------------------------ Root main.tf

# 1. APIs Module
module "apis" {
  source     = "./modules/apis"
  project_id = var.project_id
}

# 2. Storage Module
module "storage" {
  source     = "./modules/storage"
  project_id = var.project_id
  region     = var.region
  depends_on = [module.apis]
}

# 3. BigQuery Module
module "bigquery" {
  source = "./modules/bigquery"
  region = var.region
  depends_on = [module.apis]
}

# 4. IAM Module
module "iam" {
  source         = "./modules/iam"
  project_id     = var.project_id
  bucket_name    = module.storage.bucket_name
  raw_dataset_id = module.bigquery.raw_dataset_id
  depends_on     = [module.storage, module.bigquery]
}

# 5. Compute Pipeline Module
module "compute_pipeline" {
  source             = "./modules/compute_pipeline"
  project_id         = var.project_id
  region             = var.region
  image              = "asia-southeast1-docker.pkg.dev/${var.project_id}/crypto-repo/crypto-ingest:latest"
  coin_count         = 3
  ingest_sa_email    = module.iam.ingest_sa_email
  scheduler_sa_email = module.iam.scheduler_sa_email
  depends_on         = [module.iam]
}