import json

from fastapi import APIRouter, Depends
from app.schemas.event import CreateEvent

from app.core.redis import get_redis_pool
from app.dependancies.security import PublishableKeyDep
from app.dependancies.rate_limiter import RateLimiter

router = APIRouter()


# imp
# if we did my_func() it says run this function at this memory address
# while my_func just points to memory address
# earlier when we did depends(check_limit) it meant everytime that fucntion would be ran by depends()
# but now we did depends(ratelimiter(1000)) so at startup the ratelimiter fucntion will be ran 
# # and at run time our inner _check_limit function works

# Now we look at Depends().
# Depends is a special FastAPI class. 
# Its only job is to catch Memory Pointers.
# It catches <function _check_limit at 0x7f8a2b4c> 
# and permanently staples that memory address to our endpoint in its internal routing dictionary.

# FastAPI does not run it.
# It just writes down: If anyone ever goes to endpoint, 
# go to memory address 0x7f8a2b4c, add parentheses, and execute it
@router.post(
    "/track", status_code=202, dependencies=[Depends(RateLimiter(1000))]
)  # 202 means its accepted , we will work on it later
async def track_new_event(event_in: CreateEvent, api_key: PublishableKeyDep):
    # Convert Schema -> Dictionary
    data = event_in.model_dump()

    # Postgres cannot store the Pydantic 'HttpUrl' object directly.
    data["url"] = str(data["url"])

    # add the tenant id
    data["tenant_id"] = str(api_key.tenant_id)

    redis= await get_redis_pool()

    await redis.rpush("vortex_buffer",json.dumps(data))

    return {
        "status": "queued",
        "message": "Event received and is being processed in background",
    }
    