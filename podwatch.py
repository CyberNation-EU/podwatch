import podman
import requests
import json
import os

# systemctl --user start io.podman.socket

def get_registry_digest(image_name, registry, tag):
    if registry == "docker.io":
        token = "Bearer " + json.loads(requests.get(f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{image_name}:pull").text)['token']
        digest = requests.head(f"https://registry-1.docker.io/v2/{image_name}/manifests/{tag}", headers={ "Authorization" : token}).headers["Docker-Content-Digest"]
        return digest
    else:
        raise NotImplementedError(f"Registry `{registry}` not implement")


with podman.Client(uri=f"unix:/run/user/{os.getuid()}/podman/io.podman") as client:
    images = {}
    for image in client.images.list():
        try:
            tag = image.repoTags[0].split(":")[1]
            registry = image.repoTags[0].split("/")[0]
            image_name = "/".join(image.repoTags[0].split("/")[1:]).split(":")[0]
            upsteam_digest = get_registry_digest(image_name, registry, tag)
            images[image.repoTags[0]] = { 'local' : image.digest, 'upstream' : upsteam_digest}
            if upsteam_digest != image.digest:
                print (f"Update Image `{image_name}` ({image.digest})")
                image.update()
                print (f"New Image Digest `{image_name}` ({image.digest})")
        except:
            pass

    for container in client.containers.list():
        print(container)
