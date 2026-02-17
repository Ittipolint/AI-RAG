from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from keycloak import KeycloakOpenID
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize Keycloak Client
keycloak_openid = KeycloakOpenID(
    server_url=settings.KEYCLOAK_URL + "/",
    client_id=settings.KEYCLOAK_CLIENT_ID,
    realm_name=settings.KEYCLOAK_REALM,
    verify=False # Internal network, self-signed certs might be an issue otherwise
)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Verify the token
        # This decodes the token and validates the signature against Keycloak's public key
        # KEYCLOAK_PUBLIC_KEY logic can be used, or introspect
        # Introspection is easier for now but adds an extra call.
        # Ideally we decode locally.
        
        # Simple local decoding if we had the public key, but fetching it dynamically is better
        KEYCLOAK_PUBLIC_KEY = "-----BEGIN PUBLIC KEY-----\n" + keycloak_openid.public_key() + "\n-----END PUBLIC KEY-----"
        
        options = {"verify_signature": True, "verify_aud": False, "exp": True}
        token_info = keycloak_openid.decode_token(token, key=KEYCLOAK_PUBLIC_KEY, options=options)
        
        return token_info
    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
