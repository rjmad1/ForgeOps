import sys
import pytest
from unittest.mock import MagicMock

# Mock win32 modules if they fail (e.g. if pywin32 bindings aren't fully registered in the environment yet)
try:
    import win32serviceutil
    import win32service
    import win32event
except ImportError:
    # Mocking for environments where win32 is not registered
    sys.modules['win32serviceutil'] = MagicMock()
    sys.modules['win32service'] = MagicMock()
    sys.modules['win32event'] = MagicMock()
    sys.modules['servicemanager'] = MagicMock()

from src.backend.setup_service import AIRuntimeManagerService

def test_service_initialization():
    # Verify that the service class can be instantiated with mock arguments
    args = ["AIRuntimeManager"]
    # Mock the base constructor since it interacts with native Windows API
    original_init = win32serviceutil.ServiceFramework.__init__
    win32serviceutil.ServiceFramework.__init__ = lambda self, *args, **kwargs: None
    
    service = AIRuntimeManagerService(args)
    assert service._svc_name_ == "AIRuntimeManager"
    assert service._svc_display_name_ == "AI Runtime Manager"
    
    # Restore constructor
    win32serviceutil.ServiceFramework.__init__ = original_init
