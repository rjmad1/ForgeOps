import os
import sys
import pytest

def test_session_api_key_windows_acl():
    # Only test Windows ACLs on Windows platform
    if sys.platform != "win32":
        pytest.skip("Windows specific ACL test")
        
    from src.backend.app.main import API_KEY_PATH, init_security
    
    # Run security initialization
    init_security()
    
    assert os.path.exists(API_KEY_PATH)
    
    import win32api
    import win32con
    import win32security
    import ntsecuritycon as con
    
    # Read security descriptor back
    sd = win32security.GetNamedSecurityInfo(
        API_KEY_PATH,
        win32security.SE_FILE_OBJECT,
        win32security.DACL_SECURITY_INFORMATION
    )
    
    control, revision = sd.GetSecurityDescriptorControl()
    # Verify inheritance is disabled (DACL is protected)
    assert control & win32security.SE_DACL_PROTECTED, "DACL inheritance should be disabled"
    
    dacl = sd.GetSecurityDescriptorDacl()
    assert dacl is not None
    
    # Verify SIDs
    system_sid = win32security.ConvertStringSidToSid("S-1-5-18")
    admins_sid = win32security.ConvertStringSidToSid("S-1-5-32-544")
    
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    user_sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
    
    allowed_sid_strs = {
        win32security.ConvertSidToStringSid(system_sid),
        win32security.ConvertSidToStringSid(admins_sid),
        win32security.ConvertSidToStringSid(user_sid)
    }
    
    # Check that SIDs in DACL are only the allowed ones
    ace_count = dacl.GetAceCount()
    assert ace_count > 0, "DACL should have at least one ACE"
    
    for i in range(ace_count):
        ace = dacl.GetAce(i)
        # ace[2] is SID object
        sid_str = win32security.ConvertSidToStringSid(ace[2])
        assert sid_str in allowed_sid_strs, f"Unexpected SID in DACL: {sid_str}"
        
        # Verify access mask permits read/write
        access_mask = ace[1]
        assert access_mask & (con.GENERIC_READ | con.GENERIC_WRITE | con.FILE_ALL_ACCESS), f"SID {sid_str} lacks read/write permissions"
