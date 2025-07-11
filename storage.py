# Simple in-memory storage
db = {}  # { shortcode: {original_url, created_at, expires_at, clicks} }
click_stats = {}  # { shortcode: [ {timestamp, referrer, geo}, ... ] }
