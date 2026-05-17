# Module 5: Rapid Learning Challenge (Nomad & Consul)

## What I Built

- A local Nomad + Consul dev environment running on my machine
- A Nomad job that deploys a `redis:alpine` Docker container
- Service registration in Consul via the Nomad job specification
- Verified service health and discovery through Nomad and Consul UIs

## Project Structure

```
Module5/
├── redis.nomad
└── screenshots/
    ├── Nomad_UI.png
    └── Consul_UI.png
```
# 1. Environment Setup

## Install Nomad

Download Nomad from HashiCorp releases and install it locally:

```bash
wget https://releases.hashicorp.com/nomad/1.7.6/nomad_1.7.6_linux_amd64.zip
unzip nomad_1.7.6_linux_amd64.zip
sudo mv nomad /usr/local/bin/
```

Verify installation:

```bash
nomad version
```



## Install Consul

Download Consul:

```bash
wget https://releases.hashicorp.com/consul/1.18.1/consul_1.18.1_linux_amd64.zip
unzip consul_1.18.1_linux_amd64.zip
sudo mv consul /usr/local/bin/
```

Verify installation:

```bash
consul version
```

## Start Nomad & Consul in Dev Mode

### Terminal 1 — Nomad

```bash
nomad agent -dev
```

### Terminal 2 — Consul

```bash
consul agent -dev
```


## Verify UI Access

- Nomad UI: http://localhost:4646  
- Consul UI: http://localhost:8500  


This spins up a single-node cluster for both orchestration and service discovery.

Nomad handles scheduling and running workloads, while Consul provides service registry and health checks.

## Nomad Job Specification

### Redis Job File (`redis.nomad`)

```hcl
job "redis-demo" {

  datacenters = ["dc1"]

  group "redis-group" {

    network {
      port "db" {
        static = 6379
      }
    }

    task "redis" {

      driver = "docker"

      config {
        image = "redis:alpine"
        ports = ["db"]
      }

      resources {
        cpu    = 500
        memory = 256
      }

      service {
        name = "redis-service"
        port = "db"

        check {
          type     = "tcp"
          interval = "10s"
          timeout  = "2s"
        }
      }
    }
  }
}
```

### What this job does

1. Defines a Nomad job named `redis-demo`
2. Runs a single task group called `redis`
3. Uses the Docker driver to run `redis:alpine`
4. Maps container port `6379`
5. Registers the service in Consul automatically via the `service` block
6. Adds a TCP health check to ensure the service is healthy

## Running the Job

I submitted the job using:

```bash
nomad job run redis.nomad
```

To verify deployment:

```bash
nomad job status redis
```

```bash
nomad alloc status <allocation-id>
```

## Consul Service Discovery

Once the job is running, Nomad automatically registers the service in Consul.

I verified it in the Consul UI:

- Service name: `redis-service`
- Status: passing health checks
- Instance registered via Nomad integration

This confirms Consul Connect integration is working correctly.

## Nomad & Consul UI Verification

- Nomad UI showed the allocation in a running state
- Consul UI showed the `redis-service` service as healthy and discoverable

Screenshots:

```
screenshots/Nomad_UI.png
screenshots/Consul_UI.png
```

## Issues Faced and Fixes

### Issue 1 — Docker not detected by Nomad (but working with sudo)

Docker was installed correctly, and `docker ps` worked with `sudo`, but Nomad failed to detect Docker as a driver.

#### Cause
Nomad was running as a non-root user and did not have permission to access the Docker socket:

```
/var/run/docker.sock
```

#### Fix
I added my user to the Docker group:

```bash
sudo usermod -aG docker $USER
```

Then restarted the session so group permissions were applied.

After this, Nomad successfully detected the Docker driver.



### Issue 2 — Previous Nomad jobs interfering with new deployments

When re-running updated job files, old allocations were still active and caused conflicts or port binding issues.

#### Fix
I used Nomad purge to clean up previous job state:

```bash
nomad job stop -purge redis-demo
```

This ensured a clean slate before redeploying the job.


## Key Takeaways

- Nomad can function as a lightweight alternative to Kubernetes for simple orchestration tasks
- Consul integration is automatic when using the `service` block in Nomad jobs
- Docker permissions are critical when running Nomad without root access
- Job state persistence can cause conflicts; using `-purge` helps maintain clean deployments



## Conclusion

Within a single setup, I was able to:

- Deploy a containerized service using Nomad
- Enable service discovery via Consul
- Debug real-world issues related to permissions and state management
```