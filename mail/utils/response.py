class ServiceResponse:
    def __init__(self, success, message=None, status=200, data=None, error=None):
        self.success = success
        self.message = message
        self.status = status
        self.data = data
        self.error = error

    def to_dict(self):
        response = {
            'success': self.success,
            'status': self.status,
        }
        if self.message:
            response['message'] = self.message
        if self.data:
            response['data'] = self.data
        if self.error:
            response['error'] = self.error
        return response
