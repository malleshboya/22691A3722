async def log_middleware(request, call_next):
    from datetime import datetime
    method = request.method
    url = str(request.url)
    timestamp = datetime.utcnow().isoformat() + "Z"
    print(f"[{timestamp}] {method} request to {url}")
    response = await call_next(request)
    return response
