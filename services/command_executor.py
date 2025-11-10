"""
Command Executor Service
Handles subprocess execution with timeout and error handling
"""
import asyncio
import subprocess
import logging
from dataclasses import dataclass
from typing import Optional, AsyncIterator, Callable
from pathlib import Path

from exceptions import CommandExecutionError, CommandTimeoutError, DependencyInstallError
from utils.sanitization import sanitize_path, SanitizationError

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float


class CommandExecutor:
    """Service for executing shell commands with timeout and monitoring"""
    
    def __init__(self, default_timeout: int = 300):
        """
        Initialize CommandExecutor
        
        Args:
            default_timeout: Default timeout in seconds (default: 300 = 5 minutes)
        """
        self.default_timeout = default_timeout
        logger.info(f"CommandExecutor initialized with default timeout: {default_timeout}s")
    
    async def run_command(
        self,
        command: str,
        cwd: str,
        timeout: Optional[int] = None,
        env: Optional[dict] = None
    ) -> CommandResult:
        """
        Execute shell command with timeout and error capture
        
        Args:
            command: Command string to execute
            cwd: Working directory for command execution
            timeout: Optional timeout in seconds (uses default if None)
            env: Optional environment variables
            
        Returns:
            CommandResult with execution details
            
        Raises:
            CommandExecutionError: If command execution fails
        """
        if timeout is None:
            timeout = self.default_timeout
        
        # Validate command doesn't contain dangerous patterns
        # Only allow safe npm/npx commands
        allowed_commands = ['npm', 'npx', 'expo', 'node']
        command_parts = command.split()
        if command_parts and command_parts[0] not in allowed_commands:
            logger.error(f"Attempted to run disallowed command: {command_parts[0]}")
            raise CommandExecutionError(
                f"Command not allowed: {command_parts[0]}. "
                f"Only {', '.join(allowed_commands)} commands are permitted."
            )
        
        # Validate working directory exists
        cwd_path = Path(cwd)
        if not cwd_path.exists():
            logger.error(f"Working directory does not exist: {cwd}")
            raise CommandExecutionError(f"Working directory does not exist: {cwd}")
        
        logger.info(f"Executing command in {cwd}: {command}")
        
        import time
        start_time = time.time()
        
        try:
            # Use subprocess.run for Windows compatibility
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def run_subprocess():
                """Run subprocess synchronously"""
                import subprocess
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    shell=True,
                    capture_output=True,
                    timeout=timeout,
                    env=env,
                    text=True
                )
                return result
            
            # Wait for process with timeout
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, run_subprocess),
                    timeout=timeout + 5  # Add buffer for executor
                )
                
                stdout = result.stdout
                stderr = result.stderr
                exit_code = result.returncode
                
            except asyncio.TimeoutError:
                # Timeout occurred
                logger.error(f"Command timed out after {timeout}s: {command}")
                duration = time.time() - start_time
                raise CommandTimeoutError(command, timeout)
            except subprocess.TimeoutExpired:
                # Subprocess timeout
                logger.error(f"Command timed out after {timeout}s: {command}")
                duration = time.time() - start_time
                raise CommandTimeoutError(command, timeout)
            
            duration = time.time() - start_time
            
            # Determine success based on exit code
            success = exit_code == 0
            
            # Log result
            if success:
                logger.info(
                    f"Command completed successfully in {duration:.2f}s: {command}"
                )
            else:
                logger.error(
                    f"Command failed with exit code {exit_code} "
                    f"after {duration:.2f}s: {command}"
                )
                logger.error(f"stderr: {stderr[:500]}")  # Log first 500 chars of stderr
            
            return CommandResult(
                success=success,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration=duration
            )
            
        except CommandExecutionError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Unexpected error executing command: {str(e)}")
            raise CommandExecutionError(
                f"Failed to execute command: {str(e)}"
            )
    
    async def create_expo_project(
        self,
        parent_dir: str,
        app_name: str,
        timeout: Optional[int] = None
    ) -> str:
        """
        Create a new Expo project using create-expo-app
        
        Args:
            parent_dir: Parent directory where project will be created
            app_name: Name of the app (will be the folder name)
            timeout: Optional timeout for command
            
        Returns:
            Path to the created project directory
            
        Raises:
            CommandExecutionError: If project creation fails
        """
        logger.info(f"Creating Expo project '{app_name}' in {parent_dir}")
        
        # Create Expo project using npx create-expo-app and cd into it
        create_result = await self.run_command(
            command=(
                f"npm create expo-app@latest {app_name} "
                f"-- --template blank --yes"
            ),
            cwd=parent_dir,
            timeout=timeout or 180  # 3 minutes for project creation
        )
        
        if not create_result.success:
            logger.error(f"create-expo-app failed: {create_result.stderr}")
            raise CommandExecutionError(
                f"Failed to create Expo project: {create_result.stderr[:200]}"
            )
        
        project_path = Path(parent_dir) / app_name
        logger.info(f"Expo project created successfully at {project_path}")
        return str(project_path)
    
    async def setup_expo_project(
        self,
        project_dir: str,
        port: int,
        timeout: Optional[int] = None
    ) -> bool:
        """
        Run complete Expo project setup workflow
        
        This includes:
        1. Installing dependencies with npm install
        2. Verifying Expo CLI availability
        
        Args:
            project_dir: Project directory path (must already exist with package.json)
            port: Port number for Expo server
            timeout: Optional timeout for each command
            
        Returns:
            True if setup completed successfully
            
        Raises:
            CommandExecutionError: If any setup step fails
        """
        logger.info(f"Starting Expo project setup in {project_dir} on port {port}")
        
        project_path = Path(project_dir)
        package_json = project_path / "package.json"
        
        # Verify package.json exists
        if not package_json.exists():
            logger.error(f"package.json not found in {project_dir}")
            raise CommandExecutionError(
                "Project must have package.json before setup. "
                "Ensure project was created with create-expo-app."
            )
        
        # Step 1: Install dependencies
        logger.info("Installing npm dependencies...")
        install_result = await self.run_command(
            command="npm install",
            cwd=project_dir,
            timeout=timeout or 300  # 5 minutes for npm install
        )
        
        if not install_result.success:
            logger.error(f"npm install failed: {install_result.stderr}")
            raise DependencyInstallError(
                f"Failed to install dependencies: {install_result.stderr[:200]}"
            )
        
        logger.info("Dependencies installed successfully")
        
        # Step 2: Verify expo CLI is available
        logger.info("Verifying Expo CLI...")
        expo_check = await self.run_command(
            command="npm exec expo -- --version",
            cwd=project_dir,
            timeout=30
        )
        
        if not expo_check.success:
            logger.error("Expo CLI not available")
            raise CommandExecutionError(
                "Expo CLI is not available. Ensure expo is installed."
            )
        
        logger.info(f"Expo project setup completed for {project_dir}")
        logger.info(f"To start the server, run: npm start")
        return True
    
    async def _is_port_listening(self, port: int) -> bool:
        """
        Check if a port is listening (server is ready)
        
        Args:
            port: Port number to check
            
        Returns:
            True if port is listening, False otherwise
        """
        import socket
        
        try:
            # Try to connect to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.debug(f"Port check failed: {e}")
            return False
    
    async def start_expo_server(
        self,
        project_dir: str,
        port: int
    ) -> asyncio.subprocess.Process:
        """
        Start Expo development server as a background process
        
        Args:
            project_dir: Project directory path
            port: Port number for Expo server
            
        Returns:
            Process handle for the running Expo server
            
        Raises:
            CommandExecutionError: If server fails to start
        """
        logger.info(f"Starting Expo server in {project_dir} on port {port}")
        
        project_path = Path(project_dir)
        
        # Verify project directory exists
        if not project_path.exists():
            logger.error(f"Project directory not found: {project_dir}")
            raise CommandExecutionError(f"Project directory does not exist: {project_dir}")
        
        try:
            # Start Expo server using npx expo start with explicit port
            # This avoids port conflicts and interactive prompts
            import sys
            import os
            
            # Set environment variables to avoid interactive prompts and enable hot reload
            env = os.environ.copy()
            env['CI'] = '1'  # Disable interactive prompts
            env['EXPO_NO_TELEMETRY'] = '1'  # Disable telemetry
            env['EXPO_DEVTOOLS_LISTEN_ADDRESS'] = '0.0.0.0'  # Allow external connections
            env['REACT_NATIVE_PACKAGER_HOSTNAME'] = '0.0.0.0'  # Metro bundler hostname
            
            if sys.platform == 'win32':
                # Windows: use shell to find npx in PATH
                # Enable web, disable tunnel (we use ngrok), enable LAN access
                cmd = (
                    f"npm exec expo -- start --port {port} --web --lan"
                )
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
            else:
                # Unix: use exec
                process = await asyncio.create_subprocess_exec(
                    "npm",
                    "exec",
                    "expo",
                    "--",
                    "start",
                    "--port",
                    str(port),
                    "--web",
                    "--lan",
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
            
            logger.info(f"Expo server process started with PID {process.pid}")
            
            # Wait for server to be ready (check if port is listening)
            logger.info(f"Waiting for Expo server to be ready on port {port}...")
            max_wait = 60  # Wait up to 60 seconds
            wait_interval = 2  # Check every 2 seconds
            
            for attempt in range(max_wait // wait_interval):
                await asyncio.sleep(wait_interval)
                
                # Check if process is still running
                if process.returncode is not None:
                    # Process already terminated
                    stdout, stderr = await process.communicate()
                    logger.error(f"Expo server failed to start: {stderr.decode()}")
                    raise CommandExecutionError(
                        f"Expo server terminated: {stderr.decode()[:200]}"
                    )
                
                # Check if port is listening
                if await self._is_port_listening(port):
                    logger.info(f"Expo server is ready on port {port} (took {(attempt + 1) * wait_interval}s)")
                    return process
            
            # Timeout - server didn't start in time
            logger.error(f"Expo server did not start within {max_wait} seconds")
            process.kill()
            raise CommandExecutionError(
                f"Expo server failed to start within {max_wait} seconds"
            )
            
        except Exception as e:
            logger.error(f"Failed to start Expo server: {str(e)}")
            raise CommandExecutionError(f"Failed to start Expo server: {str(e)}")
    
    async def run_command_with_streaming(
        self,
        command: str,
        cwd: str,
        timeout: Optional[int] = None,
        env: Optional[dict] = None,
        output_callback: Optional[Callable[[str], None]] = None
    ) -> CommandResult:
        """
        Execute command with real-time output streaming
        
        Args:
            command: Command string to execute
            cwd: Working directory for command execution
            timeout: Optional timeout in seconds (uses default if None)
            env: Optional environment variables
            output_callback: Optional callback function for streaming output
            
        Returns:
            CommandResult with execution details
            
        Raises:
            CommandExecutionError: If command execution fails
        """
        if timeout is None:
            timeout = self.default_timeout
        
        # Validate working directory exists
        cwd_path = Path(cwd)
        if not cwd_path.exists():
            logger.error(f"Working directory does not exist: {cwd}")
            raise CommandExecutionError(f"Working directory does not exist: {cwd}")
        
        logger.info(f"Executing command with streaming in {cwd}: {command}")
        
        import time
        start_time = time.time()
        
        stdout_lines = []
        stderr_lines = []
        
        try:
            # Use subprocess.Popen for Windows compatibility with streaming
            loop = asyncio.get_event_loop()
            
            def run_subprocess_streaming():
                """Run subprocess with streaming output"""
                import subprocess
                process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True,
                    bufsize=1
                )
                
                # Read output line by line
                for line in process.stdout:
                    line_str = line.rstrip()
                    stdout_lines.append(line_str)
                    if output_callback:
                        try:
                            output_callback(line_str)
                        except Exception as e:
                            logger.warning(f"Output callback error: {e}")
                
                # Read stderr
                stderr_output = process.stderr.read()
                if stderr_output:
                    for line in stderr_output.splitlines():
                        stderr_lines.append(line)
                
                # Wait for process to complete
                process.wait(timeout=timeout)
                return process.returncode
            
            # Monitor process output with timeout
            try:
                exit_code = await asyncio.wait_for(
                    loop.run_in_executor(None, run_subprocess_streaming),
                    timeout=timeout + 5
                )
                
            except asyncio.TimeoutError:
                # Timeout occurred
                logger.error(f"Command timed out after {timeout}s: {command}")
                duration = time.time() - start_time
                raise CommandExecutionError(
                    f"Command timed out after {timeout} seconds: {command}"
                )
            except subprocess.TimeoutExpired:
                # Subprocess timeout
                logger.error(f"Command timed out after {timeout}s: {command}")
                duration = time.time() - start_time
                raise CommandExecutionError(
                    f"Command timed out after {timeout} seconds: {command}"
                )
            
            duration = time.time() - start_time
            
            # Combine output lines
            stdout = '\n'.join(stdout_lines)
            stderr = '\n'.join(stderr_lines)
            
            # Determine success based on exit code
            success = exit_code == 0
            
            # Log result
            if success:
                logger.info(
                    f"Command completed successfully in {duration:.2f}s: {command}"
                )
            else:
                logger.error(
                    f"Command failed with exit code {exit_code} "
                    f"after {duration:.2f}s: {command}"
                )
                logger.error(f"stderr: {stderr[:500]}")  # Log first 500 chars of stderr
            
            return CommandResult(
                success=success,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration=duration
            )
            
        except CommandExecutionError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Unexpected error executing command: {str(e)}")
            raise CommandExecutionError(
                f"Failed to execute command: {str(e)}"
            )
    
    async def _monitor_process(
        self,
        process: asyncio.subprocess.Process,
        timeout: int
    ) -> AsyncIterator[str]:
        """
        Stream process output for logging
        
        Args:
            process: Subprocess to monitor
            timeout: Maximum time to monitor
            
        Yields:
            Output lines from the process
            
        Raises:
            asyncio.TimeoutError: If timeout is exceeded
        """
        import time
        start_time = time.time()
        
        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise asyncio.TimeoutError(f"Process monitoring timed out after {timeout}s")
            
            # Check if process is still running
            if process.returncode is not None:
                break
            
            # Read available output
            try:
                line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=1.0
                )
                
                if line:
                    line_str = line.decode('utf-8', errors='replace').rstrip()
                    logger.debug(f"Process output: {line_str}")
                    yield line_str
                else:
                    # No more output
                    break
                    
            except asyncio.TimeoutError:
                # No output available, continue monitoring
                continue
            except Exception as e:
                logger.warning(f"Error reading process output: {e}")
                break
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
