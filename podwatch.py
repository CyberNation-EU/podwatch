#!/bin/python3
import subprocess
import podman
import requests
import argparse
import logging
import json
import os

# Pre-Requirements: Podman.socket
# > systemctl --user start io.podman.socket

__app_name__ = "podwatch"

class Podwatch:
    __args = {}
    __ignored_registries = ["k8s.gcr.io"]
    def __init__(self):
        # Parse Arguments
        parser = argparse.ArgumentParser(
            description="Utility which uses podman.socket to watch and update running containers. "
        )
        parser.add_argument("--dry-run", action="store_true", dest="dry_run", default=False,
                            help="List only actions to be performed. Doesn't update images nor restarts containers.")
        parser.add_argument("--debug", "-d", action="store_true", dest="debug", default=False,
                            help="Log additional debug information.")
        self.__args = parser.parse_args()

        # Initialize Logger
        logging.basicConfig()
        self.logger = logging.getLogger(__app_name__)
        if self.__args.debug == True:
            self.logger.setLevel(level=logging.DEBUG)
        else:
            self.logger.setLevel(level=logging.INFO)

    def get_registry_digest(self, image_name, registry, tag):
        try:
            if registry == "docker.io":
                token = "Bearer " + json.loads(requests.get(f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{image_name}:pull").text)['token']
                digest = json.loads(requests.get(f"https://registry-1.docker.io/v2/{image_name}/manifests/{tag}", headers={ "Authorization" : token, "Accept": "application/vnd.docker.distribution.manifest.v2+json"}).content)["config"]["digest"]
                return digest
            else:
                raise NotImplementedError(f"Registry `{registry}` not implement")
        except Exception as ex:
            raise Exception(f"Could not query registry `{registry}`. Err: {str(ex)}")

    def update(self):
        with podman.Client(uri=f"unix:/run/user/{os.getuid()}/podman/io.podman") as client:
            updated_images = []
            for image in client.images.list():
                try:
                    if len(image.repoTags) > 0:
                        # Extract registry, image_name and tag
                        registry = image.repoTags[0].split("/")[0]
                        image_name = "/".join(image.repoTags[0].split("/")[1:]).split(":")[0]
                        tag = image.repoTags[0].split(":")[1]

                        if registry in self.__ignored_registries:
                            self.logger.debug(f"Ignoring Image from registry {registry}.")
                            continue

                        self.logger.debug(f"Validate Image: {registry}/{image_name}:{tag}.")

                        # Load current digest from registry
                        upsteam_digest = self.get_registry_digest(image_name, registry, tag)[7:]
                        self.logger.debug(f"Compare upstream digest. Local ({image.id}). Remote ({upsteam_digest})")

                        # Compare and update image
                        if upsteam_digest != image.id:
                            updated_images.append(image.repoTags[0])
                            self.logger.info(f"Different digest pull image {image.repoTags[0]}")
                            if self.__args.dry_run:
                                self.logger.info(f"Exec: podman image pull -q {image.repoTags[0]}")
                            else:
                                subprocess.call(["podman", "image", "pull", "-q", image.repoTags[0]])
                except Exception as ex:
                    if len(image.repoTags):
                        self.logger.warning(f"Could not check image {image.repoTags[0]}. Err: {str(ex)}")
                    else:
                        self.logger.warning(f"Could not check image {image.id}. Err: {str(ex)}")

            cnt_restart = 0
            # Restart containers which are using an old version of an updated image
            for container in client.containers.list():
                if container.image in updated_images:
                    if container.containerrunning:
                        if not self.__args.dry_run:
                            container.restart()
                        cnt_restart += 1
                        self.logger.info(f"Restarted container {container.names}.")

            print(f"Updated {str(len(updated_images))} images. Restarted {str(cnt_restart)} associated containers")

if __name__ == "__main__":
    podatch = Podwatch()
    podatch.update()
