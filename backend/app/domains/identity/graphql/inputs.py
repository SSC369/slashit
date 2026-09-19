import strawberry


@strawberry.input
class UpdateTimezoneInput:
    timezone: str


@strawberry.input
class SignInInput:
    email: str
    password: str
