from fastapi import APIRouter

from src.vortex.api.responses import ApiResponse
from src.vortex.auth.dependencies import CurrentUserDep

from .services import UserService
from .exceptions import UserNotFoundError

# --- router ---
router = APIRouter(prefix="/users", tags=["Users"])


# --- /me for user ----


@router.get("/me")
async def get_user_info(current_user: CurrentUserDep):

    try:
        data = await UserService.get_user_info_by_id(current_user.get("user_id"))
    except UserNotFoundError:
        return ApiResponse.error(message="user not found", code=404)

    return ApiResponse.success(message="User fetched SucessFully", data=data)
