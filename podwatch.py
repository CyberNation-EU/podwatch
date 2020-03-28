import subprocess
import podman
import requests
import json
import os

# Pre-Requirements: Podman.socket
# > systemctl --user start io.podman.socket

def get_registry_digest(image_name, registry, tag):
    try:
        if registry == "docker.io":
            token = "Bearer " + json.loads(requests.get(f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{image_name}:pull").text)['token']
            digest = requests.head(f"https://registry-1.docker.io/v2/{image_name}/manifests/{tag}", headers={ "Authorization" : token}).headers["Docker-Content-Digest"]
            return digest
        else:
            raise NotImplementedError(f"Registry `{registry}` not implement")
    except Exception as ex:
        raise Exception(f"Could not query registry `{registry}`. Err: {str(ex)}")

def main():
    with podman.Client(uri=f"unix:/run/user/{os.getuid()}/podman/io.podman") as client:
        updated_images = []
        for image in client.images.list():
            try:
                # Extract registry, image_name and tag
                registry = image.repoTags[0].split("/")[0]
                image_name = "/".join(image.repoTags[0].split("/")[1:]).split(":")[0]
                tag = image.repoTags[0].split(":")[1]

                # Load current digest from registry
                upsteam_digest = get_registry_digest(image_name, registry, tag)

                # Compare and update image
                if upsteam_digest != image.digest:
                    print (f"Update Image `{image_name}` ({image.digest})")
                    updated_images.append(image.repoTags[0])
                    subprocess.call(["podman", "image", "pull", image.repoTags[0]])
            except Exception as ex:
                print(f"Could not check image {image.repoTags[0]}. Err: {str(ex)}")

        # Restart containers which are using an old version of an updated image
        for container in client.containers.list():
            if container.image in updated_images:
                if container.containerrunning:
                    container.stop()
                    print(f"Stopped pod.")
                    container.start()
                    print(f"Started pod.")

if __name__ == "__main__":
    main()
