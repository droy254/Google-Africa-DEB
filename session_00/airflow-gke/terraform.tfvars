project_id = "deb-capstone"
region   = "us-east1"
location = "us-east1-b"


#GKE
gke_num_nodes = 2
machine_type  = "n1-standard-2"

#CloudSQL
instance_name     = "cap01instance"
database_version  = "POSTGRES_15"
instance_tier     = "db-f1-micro"
disk_space        = 10
database_name     = "capdb"
db_username       = "capuser"
db_password       = "cappassword"


