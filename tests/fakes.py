from app.exceptions import UserNotFound, UserAlreadyExists

class FakeUserService:
    def __init__(self):
        self.users = {}
        self.next_id = 1

    def get_users(self, sort="id"):
        return list(self.users.values())

    def get_user_by_id(self, user_id: int):
        if user_id not in self.users:
            raise UserNotFound()
        return self.users[user_id]

    def create_user(self, username: str, password: str):
        ## Business Logik
        # for user in self.users.values():
        #     if user["username"] == username:
        #         raise UserAlreadyExists()

        user = {
            "id": self.next_id,
            "username": username,
        }
        self.users[self.next_id] = user
        self.next_id += 1
        return user

    def change_password(self, user_id: int, current_password: str, new_password: str):
        if user_id not in self.users:
            raise UserNotFound()

    def delete_user(self, user_id: int):
        if user_id not in self.users:
            raise UserNotFound()
        del self.users[user_id]