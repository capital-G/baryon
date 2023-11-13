# Baryon

*Baryon* is a package index for SuperCollider extensions, called *quarks*.

## Development

In order to verify the integrity of each commit it is necessary to install and setup [pre-commit](https://pre-commit.com).

### Run local dev server

In order to boot up the local development server use

```shell
make local
```

### Test types

In order to run static type analysis run

```shell
make test-types
```

## Deployment

The service is deployed on a server via Docker which exposes the web server on port `8080`.
On the host machine, a nginx reverse proxy is used to expose this service under a stated URL with a configuration similar to

```nginx
server {
    server_name baryon.supercollider.online;

    # adjust listen to 80 / 443

    location / {
        # add_header Access-Control-Allow-Origin *;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # new
        proxy_redirect off;

        proxy_http_version 1.1;

        proxy_pass http://127.0.0.1:8080;
    }
}
```

Use [certbot](https://certbot.eff.org/) to obtain a SSL certificate for the website.

As the scraping needs to run in regular intervals it is necessary to create a reoccurring job which executes the [Django command](https://docs.djangoproject.com/en/dev/howto/custom-management-commands/)

```shell
python manage.py scrape_quarks
```

within the Docker container `backend`.

Systemd can be used to declare a service which executes this command as well as using.
Asserting the service is deployed with the service user `baryon` under the directory `/home/baryon/baryon` the provided systemd service files can be linked and activated.

```shell
sudo ln -s /home/baryon/baryon/baryon-scraper.service /etc/systemd/system/baryon-scraper.service
sudo ln -s /home/baryon/baryon/baryon-scraper.timer /etc/systemd/system/baryon-scraper.timer

sudo systemctl daemon-reload

sudo systemctl start baryon-scraper.timer
sudo systemctl enable baryon-scraper.timer
```

In order to trigger a scraping manually it is possible via the command

```shell
sudo systemctl start baryon-scraper

# check status
sudo systemctl status baryon-scraper
```

## License

AGPL-3.0
