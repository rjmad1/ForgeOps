import os
import sys
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import logging
import threading
import uvicorn

# Set up logging for Windows Service execution
logging.basicConfig(
    filename=r"C:\ProgramData\AIRuntimeManager\logs\service.log" if os.path.exists(r"C:\ProgramData\AIRuntimeManager") else "service.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("service_wrapper")

class AIRuntimeManagerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AIRuntimeManager"
    _svc_display_name_ = "AI Runtime Manager"
    _svc_description_ = "Orchestrator for local AI services (Ollama, LiteLLM, OpenClaw, MCP)"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_running = True

    def SvcStop(self):
        logger.info("Service stop signal received. Stopping uvicorn...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False

    def SvcDoRun(self):
        logger.info("Service starting...")
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.main()

    def main(self):
        try:
            # We import here to ensure that path setup is complete before loading app
            from src.backend.app.main import app
            
            config = uvicorn.Config(
                app, 
                host="127.0.0.1", 
                port=8088, 
                log_level="info",
                loop="asyncio"
            )
            server = uvicorn.Server(config)
            
            # Run server in a helper thread so we can respond to SvcStop
            thread = threading.Thread(target=server.run)
            thread.daemon = True
            thread.start()
            
            logger.info("Uvicorn server started on thread.")
            
            # Block until Windows signals service shutdown
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            
            logger.info("Windows Service shutdown requested. Flagging uvicorn exit...")
            server.should_exit = True
            thread.join(timeout=5)
            logger.info("Service stopped successfully.")
            
        except Exception as e:
            logger.error(f"Fatal error in service execution: {e}", exc_info=True)
            sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AIRuntimeManagerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AIRuntimeManagerService)
