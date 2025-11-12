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
    
    def __init__(self, default_timeout: int = 600):
        """
        Initialize CommandExecutor
        
        Args:
            default_timeout: Default timeout in seconds (default: 600 = 10 minutes)
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
        # Increased timeout to 600 seconds (10 minutes) for slower connections
        create_result = await self.run_command(
            command=f"npx create-expo-app@latest {app_name} && cd {app_name}",
            cwd=parent_dir,
            timeout=timeout or 600  # 10 minutes for project creation
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
            timeout=timeout or 600  # 10 minutes for npm install
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
            command="npx expo --version",
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
    
    async def _is_port_available(self, port: int) -> bool:
        """
        Check if a port is available (not in use)
        
        Args:
            port: Port number to check
            
        Returns:
            True if port is available, False otherwise
        """
        import socket
        
        sock = None
        try:
            # Try to bind to the port - if successful, port is available
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(1)
            try:
                sock.bind(('127.0.0.1', port))
                # Port is available
                return True
            except OSError as e:
                # Port is in use (errno 10048 on Windows, 98 on Linux)
                logger.debug(f"Port {port} is not available: {e}")
                return False
        except Exception as e:
            logger.debug(f"Port availability check failed: {e}")
            return False
        finally:
            # Make sure socket is closed
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    async def _find_available_port(self, start_port: int, max_attempts: int = 10) -> int:
        """
        Find an available port starting from start_port
        
        Args:
            start_port: Starting port number
            max_attempts: Maximum number of ports to try
            
        Returns:
            Available port number
            
        Raises:
            CommandExecutionError: If no available port found
        """
        for offset in range(max_attempts):
            port = start_port + offset
            if await self._is_port_available(port):
                logger.info(f"Found available port: {port}")
                return port
        
        raise CommandExecutionError(
            f"Could not find available port starting from {start_port} after {max_attempts} attempts"
        )
    
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
            # Check if the requested port is available
            if not await self._is_port_available(port):
                logger.warning(f"Port {port} is not available, finding alternative port...")
                # Find an available port near the requested one
                port = await self._find_available_port(port, max_attempts=10)
                logger.info(f"Using alternative port: {port}")
            
            # Start Expo server using npx expo start with explicit port
            # This avoids port conflicts and interactive prompts
            import sys
            import os
            
            # Set environment variables to enable hot reload
            # Note: We don't set CI=1 because it makes Expo think it's in non-interactive mode
            # but Expo still needs to ask for input in some cases, causing errors.
            # Instead, we check port availability beforehand and pipe "yes" to handle any prompts.
            env = os.environ.copy()
            # Remove CI if it's set, to allow Expo to handle prompts properly
            if 'CI' in env:
                del env['CI']
            env['EXPO_NO_TELEMETRY'] = '1'  # Disable telemetry
            env['EXPO_DEVTOOLS_LISTEN_ADDRESS'] = '0.0.0.0'  # Allow external connections
            env['REACT_NATIVE_PACKAGER_HOSTNAME'] = '0.0.0.0'  # Metro bundler hostname
            env['EXPO_NO_DOTENV'] = '1'  # Disable .env file loading to avoid conflicts
            env['EXPO_NO_GIT_STATUS'] = '1'  # Disable git status check
            
            if sys.platform == 'win32':
                # Windows: Ensure ProactorEventLoop is set for subprocess support
                import asyncio
                loop = asyncio.get_event_loop()
                if not isinstance(loop, asyncio.ProactorEventLoop):
                    logger.warning("Current event loop is not ProactorEventLoop, setting policy...")
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    # Note: This won't affect the current loop, but will affect new ones
                
                # Windows: use shell to find npx in PATH
                # Enable web, disable tunnel (we use ngrok), enable LAN access
                # Since port is already checked and available, Expo shouldn't ask for confirmation
                # But we'll use stdin to handle any prompts that might occur
                cmd = f'npx --yes expo start --port {port} --web --lan'
                logger.info(f"Starting Expo with command: {cmd}")
                logger.info(f"Working directory: {project_dir}")
                
                try:
                    # Use subprocess.Popen wrapped in executor for Windows compatibility
                    import subprocess
                    from concurrent.futures import ThreadPoolExecutor
                    import threading
                    
                    def create_process():
                        """Create subprocess using Popen (Windows compatible)"""
                        # Create process with stdin=PIPE so we can send input if needed
                        process = subprocess.Popen(
                            cmd,
                            cwd=project_dir,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE,
                            env=env,
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0,
                            text=True,  # Use text mode for stdin
                            bufsize=1  # Line buffered
                        )
                        
                        # Start a background thread to send "yes" if Expo asks for input
                        def send_yes():
                            """Send 'yes' to stdin after a short delay"""
                            import time
                            time.sleep(0.5)  # Wait a bit for Expo to start
                            try:
                                # Send "yes" multiple times to handle any prompts
                                for _ in range(3):
                                    if process.stdin and not process.stdin.closed:
                                        process.stdin.write("yes\n")
                                        process.stdin.flush()
                                        time.sleep(0.1)
                            except:
                                pass  # Ignore if stdin is closed
                        
                        # Start thread to handle prompts
                        prompt_thread = threading.Thread(target=send_yes, daemon=True)
                        prompt_thread.start()
                        
                        return process
                    
                    # Create process in thread pool to avoid blocking
                    with ThreadPoolExecutor() as executor:
                        popen_process = await loop.run_in_executor(executor, create_process)
                    
                    # Wrap Popen process to make it compatible with asyncio.subprocess.Process
                    class ProcessWrapper:
                        def __init__(self, popen_proc):
                            self.popen_proc = popen_proc
                            self.pid = popen_proc.pid
                            self.returncode = popen_proc.returncode
                            # Expose stdout and stderr for reading
                            self.stdout = popen_proc.stdout
                            self.stderr = popen_proc.stderr
                            
                        async def communicate(self):
                            """Read stdout and stderr"""
                            loop = asyncio.get_event_loop()
                            stdout, stderr = await loop.run_in_executor(None, self.popen_proc.communicate)
                            return stdout, stderr
                        
                        def kill(self):
                            """Kill the process"""
                            try:
                                self.popen_proc.kill()
                            except:
                                pass
                    
                    process = ProcessWrapper(popen_process)
                    logger.info(f"Process created successfully with PID {process.pid}")
                    
                except Exception as e:
                    logger.error(f"Failed to create subprocess: {type(e).__name__}: {str(e)}")
                    raise CommandExecutionError(
                        f"Failed to create Expo process: {type(e).__name__}: {str(e) or 'Process creation failed'}"
                    )
            else:
                # Unix: use exec with stdin=PIPE to handle prompts
                process = await asyncio.create_subprocess_exec(
                    "npx",
                    "--yes",
                    "expo",
                    "start",
                    "--port",
                    str(port),
                    "--web",
                    "--lan",
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=asyncio.subprocess.PIPE,
                    env=env
                )
                
                # Send "yes" in background to handle any prompts
                async def send_yes_async():
                    """Send 'yes' to stdin after a short delay"""
                    await asyncio.sleep(0.5)
                    try:
                        for _ in range(3):
                            if process.stdin and not process.stdin.closed:
                                process.stdin.write(b"yes\n")
                                await process.stdin.drain()
                                await asyncio.sleep(0.1)
                    except:
                        pass  # Ignore if stdin is closed
                
                # Start background task to handle prompts
                asyncio.create_task(send_yes_async())
            
            logger.info(f"Expo server process started with PID {process.pid}")
            
            # Give process a moment to start
            await asyncio.sleep(1)
            
            # Check if process crashed immediately
            # Update returncode for wrapper
            if hasattr(process, 'popen_proc'):
                process.returncode = process.popen_proc.poll()
            
            if process.returncode is not None:
                stdout, stderr = await process.communicate()
                # Handle both bytes and strings (Windows uses text=True, Unix uses bytes)
                stdout_text = stdout if isinstance(stdout, str) else (stdout.decode('utf-8', errors='ignore') if stdout else "")
                stderr_text = stderr if isinstance(stderr, str) else (stderr.decode('utf-8', errors='ignore') if stderr else "")
                logger.error(f"Expo server crashed immediately. Exit code: {process.returncode}")
                logger.error(f"stdout: {stdout_text[:500] if stdout_text else 'None'}")
                logger.error(f"stderr: {stderr_text[:500] if stderr_text else 'None'}")
                raise CommandExecutionError(
                    f"Expo server crashed immediately (exit code {process.returncode}). "
                    f"Error: {stderr_text[:200] if stderr_text else stdout_text[:200] if stdout_text else 'No error output'}"
                )
            
            # Wait for server to be ready (check if port is listening)
            logger.info(f"Waiting for Expo server to be ready on port {port}...")
            max_wait = 60  # Wait up to 60 seconds
            wait_interval = 2  # Check every 2 seconds
            
            for attempt in range(max_wait // wait_interval):
                await asyncio.sleep(wait_interval)
                
                # Check if process is still running
                # Update returncode for wrapper
                if hasattr(process, 'popen_proc'):
                    process.returncode = process.popen_proc.poll()
                
                if process.returncode is not None:
                    # Process terminated during startup
                    stdout, stderr = await process.communicate()
                    # Handle both bytes and strings (Windows uses text=True, Unix uses bytes)
                    stdout_text = stdout if isinstance(stdout, str) else (stdout.decode('utf-8', errors='ignore') if stdout else "")
                    stderr_text = stderr if isinstance(stderr, str) else (stderr.decode('utf-8', errors='ignore') if stderr else "")
                    logger.error(f"Expo server terminated during startup: {stderr_text}")
                    raise CommandExecutionError(
                        f"Expo server terminated: {stderr_text[:200] if stderr_text else stdout_text[:200] if stdout_text else 'No error output'}"
                    )
                
                # Check if port is listening
                if await self._is_port_listening(port):
                    logger.info(f"Expo server is ready on port {port} (took {(attempt + 1) * wait_interval}s)")
                    return process
            
            # Timeout - server didn't start in time
            logger.error(f"Expo server did not start within {max_wait} seconds")
            # Try to get error output before killing (but don't fail if we can't read it)
            error_output = ""
            try:
                # For Windows ProcessWrapper, try to read synchronously from the underlying process
                if hasattr(process, 'popen_proc'):
                    # Windows: read from Popen process directly if available
                    try:
                        if process.popen_proc.stderr and not process.popen_proc.stderr.closed:
                            # Peek at stderr if available (non-blocking)
                            import select
                            import sys
                            if sys.platform == 'win32':
                                # On Windows, we can't easily peek without blocking
                                # Just log that we timed out
                                pass
                            else:
                                # Unix: try to read
                                if select.select([process.popen_proc.stderr], [], [], 0.1)[0]:
                                    stderr_data = process.popen_proc.stderr.read(1024)
                                    if stderr_data:
                                        if isinstance(stderr_data, str):
                                            error_output = stderr_data
                                        else:
                                            error_output = stderr_data.decode('utf-8', errors='ignore')
                    except Exception as e:
                        logger.debug(f"Could not read stderr: {e}")
                elif hasattr(process, 'stderr') and process.stderr:
                    # Unix: try async read
                    try:
                        stderr_data = await asyncio.wait_for(process.stderr.read(1024), timeout=0.5)
                        if stderr_data:
                            if isinstance(stderr_data, str):
                                error_output = stderr_data
                            else:
                                error_output = stderr_data.decode('utf-8', errors='ignore') if stderr_data else ""
                    except:
                        pass
                
                if error_output:
                    logger.error(f"Expo server error output: {error_output[:500]}")
            except Exception as e:
                logger.debug(f"Error reading process output: {e}")
            
            # Kill the process
            try:
                process.kill()
            except:
                pass
            
            raise CommandExecutionError(
                f"Expo server failed to start within {max_wait} seconds. "
                f"{'Error: ' + error_output[:200] if error_output else 'Check if port is available and node_modules are installed correctly.'}"
            )
            
        except CommandExecutionError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error(f"Failed to start Expo server: {str(e)}", exc_info=True)
            error_msg = str(e) if str(e) else "Unknown error starting Expo server"
            raise CommandExecutionError(f"Failed to start Expo server: {error_msg}")
    
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
