from log_setup import log_error


async def check_link_liquidity(link):
    try:
        if link.startswith("https://"):
            return True
        else:
            return False
    except Exception as e:
        log_error("system", f"Error checking link: {e}")
        return False
