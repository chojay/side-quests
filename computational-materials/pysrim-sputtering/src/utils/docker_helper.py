"""
Docker container management for running SRIM/TRIM on macOS.

SRIM.exe is a Windows binary that requires Wine. On macOS ARM64,
the most reliable approach is running via Docker with platform
emulation (linux/amd64 via Rosetta 2).
"""
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DockerSRIMRunner:
    """
    Manage Docker container for running SRIM/TRIM simulations.

    Parameters
    ----------
    image : str
        Docker image name. Default "pysrim".
    srim_dir : str
        Path to SRIM directory inside the container.
    """

    def __init__(self, image: str = "pysrim",
                 srim_dir: str = "/opt/SRIM"):
        self.image = image
        self.srim_dir = srim_dir
        self._docker_available = None

    @property
    def docker_available(self) -> bool:
        """Check if Docker daemon is running."""
        if self._docker_available is None:
            try:
                result = subprocess.run(
                    ["docker", "info"],
                    capture_output=True, timeout=10
                )
                self._docker_available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._docker_available = False
        return self._docker_available

    def image_exists(self) -> bool:
        """Check if the Docker image is available locally."""
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", self.image],
                capture_output=True, timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def build_image(self, dockerfile_dir: Optional[str] = None) -> bool:
        """Build the Docker image from Dockerfile."""
        if dockerfile_dir is None:
            from ..utils.config_loader import PROJECT_ROOT
            dockerfile_dir = str(PROJECT_ROOT)

        logger.info(f"Building Docker image '{self.image}' from {dockerfile_dir}")
        result = subprocess.run(
            ["docker", "build", "--platform", "linux/amd64",
             "-t", self.image, dockerfile_dir],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode != 0:
            logger.error(f"Docker build failed: {result.stderr}")
            return False
        logger.info("Docker image built successfully")
        return True

    def run_trim_script(self, script_content: str,
                        output_dir: str,
                        timeout: int = 300) -> bool:
        """
        Run a Python script inside the Docker container.

        Parameters
        ----------
        script_content : str
            Python script to execute.
        output_dir : str
            Host directory to mount for output.
        timeout : int
            Timeout in seconds.

        Returns
        -------
        bool
            True if execution succeeded.
        """
        if not self.docker_available:
            raise RuntimeError("Docker is not available")

        os.makedirs(output_dir, exist_ok=True)

        # Write script to temp file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as f:
            f.write(script_content)
            script_path = f.name

        try:
            cmd = [
                "docker", "run", "--rm",
                "--platform", "linux/amd64",
                "-v", f"{script_path}:/app/run_sim.py:ro",
                "-v", f"{output_dir}:/app/output",
                "-e", f"SRIM_EXECUTABLE_DIRECTORY={self.srim_dir}",
                self.image,
                "python3", "/app/run_sim.py"
            ]

            logger.info("Running TRIM simulation in Docker...")
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )

            if result.stdout:
                logger.info(f"TRIM stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"TRIM stderr: {result.stderr}")

            return result.returncode == 0
        finally:
            os.unlink(script_path)

    def run_command(self, command: str, timeout: int = 60) -> str:
        """Run a command inside the container and return stdout."""
        if not self.docker_available:
            raise RuntimeError("Docker is not available")

        cmd = [
            "docker", "run", "--rm",
            "--platform", "linux/amd64",
            self.image,
            "bash", "-c", command
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {result.stderr}")
        return result.stdout


def check_docker_setup() -> dict:
    """
    Check Docker availability and image status.

    Returns
    -------
    dict
        Status information with keys: docker_available, image_exists,
        docker_version, platform.
    """
    status = {
        'docker_available': False,
        'image_exists': False,
        'docker_version': None,
        'platform': None,
    }

    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            status['docker_available'] = True
            status['docker_version'] = result.stdout.strip()

        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Arch}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            status['platform'] = result.stdout.strip()

        runner = DockerSRIMRunner()
        status['image_exists'] = runner.image_exists()

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return status
