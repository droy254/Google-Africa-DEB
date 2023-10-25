# Google Kubernetes Engine (GKE), Airflow and Terraform template


## Prerequisites
- [Configured GCP account](https://cloud.google.com/)
- [Homebrew](https://brew.sh/) (if you're using MacOS)
- [Kubectl cli](https://kubernetes.io/docs/tasks/tools/) (choose the OS you're working with)
- [gCloud SDK](https://cloud.google.com/sdk/docs/quickstart)
- [Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli) >= 0.13
- [Helm 3](https://helm.sh/docs/intro/install/)


## Step by step guide
1. Clone this repository.


2. Create a [virtual environment for your local project](https://medium.com/@dakota.lillie/an-introduction-to-virtual-environments-in-python-ce16cda92853)
and activate it:
    ```bash
    python3 -m venv .venv # create virtual environment
    source .venv/bin/activate # activate virtual environment
    deactivate # DO NOT RUN YET: deactivates virtual environment
    ```

3. Initialize gcloud SDK and authorize it to access GCP using your user account credentials:
    ```bash
    gcloud init
       
    # The next portion represents the cli settings setup
    >> [1] Re-initialize this configuration [default] with new settings # config to use
    >> [1] user@sample.com # account to perform operations for config
    >> [6] project-id # cloud project to use
    >> [8] us-central1-a # region to connect to
   
    gcloud auth application-default login # authorize access
    ```
   **DISCLAIMER:** This part will ask you to choose the Google account and the GCP project you will work with. It
will also ask you to choose a region to connect to. The information shown above in is an example of what you *can*
choose, but keep in mind that this was used for credentials that were already entered once before.


3. For GCP to access you user account credentials for the first time, it will ask you to give it explicit permission
like so:
![Choose account for Google Cloud SDK](./imgs/google-account.png "Choose account")
![Grant access for Google Cloud SDK](./imgs/authorization.png "Grant access")


4. After choosing the Google account to work with and successfully granting permissions, you should be redirected to
    this message:
![Successful authentication message](./imgs/successful-authentication.png "Successful authentication")


5. You should also see a similar message to this in your terminal:
![Configured Google Cloud SDK](./imgs/cloud-sdk-configured.png "Configured Google Cloud SDK")


7. In the GCP Console, enable: 
   - Compute Engine API
   - Kubernetes Engine API


7. In your cloned local project, copy the [terraform.tfvars.example](./terraform.tfvars.example) and paste it in the
root of the project named as *terraform.tfvars*, changing the property *project_id* to your corresponding project ID.


8. Initialize the Terraform workspace and create the resources:
    ```bash
    terraform init # initialize
    terraform init --upgrade # if you initialized once before and need to update terraform config

    terraform plan --var-file=terraform.tfvars

    terraform apply --var-file=terraform.tfvars
    >> yes # lets terraform perform actions described
    ```
    ***IMPORTANT***: This process might take around 10-15 minutes, **be patient please**.


9. Set the kubectl context:
    ```bash
    gcloud container clusters get-credentials $(terraform output -raw kubernetes_cluster_name) --region $(terraform output -raw location)
    ```

10. Create a namespace for Airflow:

    ```bash
    kubectl create namespace airflow
    ```

11. Add the chart repository: Using the airflow community chart
    ```bash
    helm repo add airflow-stable https://airflow-helm.github.io/charts
    ```

11. Add the chart repository: Using the airflow community chart
    ```bash
    helm repo update
    ```

13. Install the Airflow chart from the repository: Deploy airflow
    ```bash
    helm upgrade --install airflow -f airflow-values.yaml airflow-stable/airflow --namespace airflow
    ```
    ***IMPORTANT***: This process might take around 5 minutes to execute, **be patient please**.


14. Verify that the pods are up and running:
    ```bash
    kubectl get pods -n airflow
    ```

15. Access the Airflow dashboard with what the Helm chart provided:
    ```bash
    Your release is named airflow.
    You can now access your dashboard(s) by executing the following command(s) and visiting the corresponding port at localhost in your browser:
    
    Airflow Webserver:     kubectl port-forward svc/airflow-web 8080:8080 --namespace airflow
    Default Webserver (Airflow UI) Login credentials:
        username: admin
        password: admin
    Default Postgres connection credentials:
        username: postgres
        password: postgres
        port: 5432
    ```
    **Note:** Sometimes there's an error when doing the kubectl portforward. If all of the pods are running, we might
    just need to keep trying.
    

16. Once in `localhost:8080`, you should see the Airflow login.
![Airflow Login](./imgs/airflow-login.png "Airflow Login")


17. After logging in with your credentials (username and password from webserver in step 18), you should see the Airflow
dashboard.
![Airflow Dashboard](./imgs/airflow-dag-dashboard.png "Airflow Dashboard")


## Don't forget to ***destroy everything*** after you're done using it!
- To destroy the cluster:
    ```bash
    terraform destroy --var-file=terraform.tfvars
    ```
- Double-check your GCP console to make sure everything was correctly destroyed.

