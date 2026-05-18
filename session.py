class SessionManager:   
    
    def __init__(self):
        self.current_user = None 
        self.is_logged_in = False

    def login(self, user_data):
        
        self.current_user = user_data
        self.is_logged_in = True

    def logout(self):
                
        self.current_user = None
        self.is_logged_in = False

    def get_current_user(self):
   
        return self.current_user

    def get_username(self):
        if isinstance(self.current_user, dict):
            return str(self.current_user.get("username", "")).strip()
        return ""

    def check_auth(self):
        return self.is_logged_in

current_session = SessionManager()