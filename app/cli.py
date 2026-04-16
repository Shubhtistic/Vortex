import asyncio
import secrets
import time
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, delete

from app.core.config import settings
from app.db.db_models import ApiKey, KeyType
from app.utils.hash import hash_api_key

async_engine = create_async_engine(settings.POSTGRES_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def start_new():
    print("\nPlease enter a unique Tenant ID.")
    print("If that ID already exists, the program will exit.")
    print("\nType 'Y' to enter your own Tenant ID, or press ENTER to auto-generate a random one.")

    input_given = input("Y / [Enter] > ").strip()
    tenant_id = ""
    
    if input_given.lower() == 'y':
        tenant_id = input("Tenant ID > ").strip()
    else:
        tenant_id = f"Tenant_{secrets.token_urlsafe(8)}"
    
    secret_key = f"vtx_sec_{secrets.token_urlsafe(24)}"
    public_key = f"vtx_pub_{secrets.token_urlsafe(24)}"

    async with AsyncSessionLocal() as session:
        qry = select(1).where(ApiKey.tenant_id == tenant_id)
        res = (await session.execute(qry)).scalar_one_or_none()
        
        if res:
            print("Error: The Tenant ID already exists.")
            print("Exiting...")
            await asyncio.sleep(2) 
            return

        add_secret_key = ApiKey(
            tenant_id=tenant_id,
            hashed_key=hash_api_key(secret_key),
            key_type=KeyType.secret
        )

        add_public_key = ApiKey(
            tenant_id=tenant_id,
            hashed_key=hash_api_key(public_key),
            key_type=KeyType.publishable
        )

        session.add(add_public_key)
        session.add(add_secret_key)
        await session.commit()

        print("\n*** PLEASE PAY ATTENTION ***\n")
        print("Below are your Tenant ID, Secret Key, and Public Key.")
        print("Please save them immediately. You will not be able to view them again.")
        print(f"Tenant ID:  {tenant_id}")
        print(f"Secret Key: {secret_key}")
        print(f"Public Key: {public_key}\n")


async def rotate_keys():
    print("\nPlease enter a valid Tenant ID.")
    tenant_id = input("Tenant ID > ").strip()

    if not tenant_id:
        print("No input provided. Exiting...")
        await asyncio.sleep(3) 
        return
    
    async with AsyncSessionLocal() as session:
        new_secret_key = f"vtx_sec_{secrets.token_urlsafe(24)}"
        new_public_key = f"vtx_pub_{secrets.token_urlsafe(24)}"
        
        del_qry = delete(ApiKey).where(ApiKey.tenant_id == tenant_id)
        result = await session.execute(del_qry)

        if result.rowcount == 0:
            print("No existing keys were found to delete.")
            print("You provided an incorrect Tenant ID.")
            print("Exiting...")
            await asyncio.sleep(2)
            return 

        add_secret_key = ApiKey(
            tenant_id=tenant_id,
            hashed_key=hash_api_key(new_secret_key),
            key_type=KeyType.secret
        )

        add_public_key = ApiKey(
            tenant_id=tenant_id,
            hashed_key=hash_api_key(new_public_key),
            key_type=KeyType.publishable
        )

        session.add(add_public_key)
        session.add(add_secret_key)
        await session.commit()

        print("\n*** PLEASE PAY ATTENTION ***\n")
        print("Below are your Tenant ID and newly rotated keys.")
        print("Please save them immediately. The old keys are now invalid.")
        print(f"Tenant ID:  {tenant_id}")
        print(f"Secret Key: {new_secret_key}")
        print(f"Public Key: {new_public_key}\n")

        
try:
    print("Welcome to the Vortex Telemetry Engine")
    print("A lightweight, high-performance open-source infrastructure tool for tracking and tracing telemetry data.")
    print("Engineered by Shubham (GitHub: @Shubhtistic). Thanks for using!\n")

    print("Policy Note: We strictly allow only one Public and one Secret key per tenant.")
    print("This constraint simplifies key rotation and prevents active-key confusion.")
    print("You can alter the source code if you require multiple concurrent keys.\n")

    print("Select an option:")
    print("1. Create a Tenant and generate keys")
    print("2. Rotate keys for an existing Tenant\n")
    
    choice = input("Option > ").strip()

    if not choice:
        print("No input provided. Exiting...")
        time.sleep(2) 
        exit()

    if choice == '1':
        asyncio.run(start_new()) 

    elif choice == '2':
        asyncio.run(rotate_keys())

except KeyboardInterrupt:
    print("\nUser closed the setup. Exiting...")
    time.sleep(2)
    exit()