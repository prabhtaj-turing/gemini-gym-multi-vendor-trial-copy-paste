class IncorrectEventError(Exception):
    def __init__(self, message: str = "Event id does not belong to the camera.", rpc: str = "FAILED_PRECONDITION", code: int = 400):
        self.rpc = rpc
        self.code = code
        super().__init__(f"{message} (RPC: {rpc}) (Error code: {code})")

class CameraNotAvailableError(Exception):
    def __init__(self, message: str = "The camera is not available for streaming.", rpc: str = "FAILED_PRECONDITION", code: int = 400):
        self.rpc = rpc
        self.code = code
        super().__init__(f"{message} (RPC: {rpc}) (Error code: {code})")

class CommandNotSupportedError(Exception):
    def __init__(self, message: str = "Command not supported.", rpc: str = "INVALID_ARGUMENT", code: int = 400):
        self.rpc = rpc
        self.code = code
        super().__init__(f"{message} (RPC: {rpc}) (Error code: {code})")
