from urllib.parse import urlparse

def validate_listing_url(url, listing_type):
    """
    Validate if a URL is likely to be a direct listing
    """
    # Invalid patterns that indicate search pages or invalid listings
    invalid_patterns = [
        '/search', '/soeg', '?soeg=', '/item/',
        'boligportal.dk/lejeboliger/',  # Main category page
        'lejebolig.dk/lejebolig/',      # Main category page
        'dba.dk/andelsbolig/',          # Main category page
        '/marketplace/search/',          # Facebook search page
        'category', 'categories',
        'side-', 'page-'
    ]
    
    # Check for invalid patterns
    if any(pattern in url.lower() for pattern in invalid_patterns):
        return False
        
    # Verify the URL matches the listing type
    if listing_type == 'andelsbolig':
        valid_domains = ['dba.dk', 'facebook.com', 'andelsbolig.dk']
    else:  # lejebolig
        valid_domains = ['boligportal.dk', 'lejebolig.dk', 'dba.dk', 'facebook.com']
    
    # Extract domain from URL
    domain = urlparse(url).netloc.replace('www.', '')
    
    return domain in valid_domains

def filter_tavily_results(results, listing_type):
    """
    Pre-filter Tavily results before sending to OpenAI
    """
    if not results or 'results' not in results:
        return results
        
    return results  # Return all results without filtering