"""
Helm wrapper — shells out to helm CLI to install/upgrade/delete releases.
"""

import asyncio
import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)


class HelmClient:
    """Async wrapper around the Helm CLI."""

    def __init__(self):
        self.helm_bin = settings.HELM_BINARY

    async def _run(self, args: list[str], env: dict | None = None) -> tuple[int, str, str]:
        """Run a helm command asynchronously."""
        cmd = [self.helm_bin] + args
        merged_env = {**os.environ, **(env or {})}

        logger.info("Running: %s", " ".join(cmd))
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=merged_env,
        )
        stdout, stderr = await proc.communicate()
        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        if proc.returncode != 0:
            logger.error("Helm command failed (rc=%d): %s", proc.returncode, stderr_str)
        else:
            logger.info("Helm command succeeded: %s", stdout_str[:200])

        return proc.returncode, stdout_str, stderr_str

    async def install(
        self,
        release_name: str,
        chart_path: str,
        namespace: str,
        values: dict | None = None,
        values_file: str | None = None,
        wait: bool = True,
        timeout: str = "600s",
    ) -> tuple[bool, str]:
        """Install a Helm chart. Returns (success, output)."""
        args = [
            "install",
            release_name,
            chart_path,
            "--namespace",
            namespace,
            "--create-namespace",
            "--timeout",
            timeout,
        ]

        if wait:
            args.append("--wait")

        if values_file:
            args.extend(["-f", values_file])

        if values:
            for k, v in values.items():
                args.extend(["--set", f"{k}={v}"])

        rc, stdout, stderr = await self._run(args)
        return rc == 0, stdout if rc == 0 else stderr

    async def upgrade(
        self,
        release_name: str,
        chart_path: str,
        namespace: str,
        values: dict | None = None,
        values_file: str | None = None,
    ) -> tuple[bool, str]:
        """Upgrade (or install) a Helm release."""
        args = [
            "upgrade",
            "--install",
            release_name,
            chart_path,
            "--namespace",
            namespace,
            "--wait",
            "--timeout",
            "600s",
        ]

        if values_file:
            args.extend(["-f", values_file])

        if values:
            for k, v in values.items():
                args.extend(["--set", f"{k}={v}"])

        rc, stdout, stderr = await self._run(args)
        return rc == 0, stdout if rc == 0 else stderr

    async def uninstall(self, release_name: str, namespace: str) -> tuple[bool, str]:
        """Uninstall a Helm release."""
        args = [
            "uninstall",
            release_name,
            "--namespace",
            namespace,
        ]
        rc, stdout, stderr = await self._run(args)
        return rc == 0, stdout if rc == 0 else stderr

    async def status(self, release_name: str, namespace: str) -> tuple[bool, str]:
        """Get helm release status."""
        args = [
            "status",
            release_name,
            "--namespace",
            namespace,
        ]
        rc, stdout, stderr = await self._run(args)
        return rc == 0, stdout if rc == 0 else stderr

    async def list_releases(self, namespace: str = "") -> tuple[bool, str]:
        """List helm releases."""
        args = ["list", "--output", "json"]
        if namespace:
            args.extend(["--namespace", namespace])
        else:
            args.append("--all-namespaces")

        rc, stdout, stderr = await self._run(args)
        return rc == 0, stdout if rc == 0 else stderr

    async def rollback(
        self, release_name: str, namespace: str, revision: int = 0
    ) -> tuple[bool, str]:
        """Rollback a Helm release."""
        args = [
            "rollback",
            release_name,
            "--namespace",
            namespace,
            "--wait",
        ]
        if revision > 0:
            args.append(str(revision))

        rc, stdout, stderr = await self._run(args)
        return rc == 0, stdout if rc == 0 else stderr


# Global singleton
helm_client = HelmClient()
