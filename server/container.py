import docker

class ContainerManager:

    def __init__(self):
        self.client = docker.from_env()

    def start_container(self):
        container = self.client.containers.run(
            image="ubuntu:22.04",
            command="sleep infinity",
            detach=True,
            tty=True,
            mem_limit="512m",
            network_mode="none"
        )

        return container

    def exec(self, container, cmd: str):
        result = container.exec_run(cmd)
        return result.output.decode()

    def destroy(self, container):
        container.stop()
        container.remove()