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
