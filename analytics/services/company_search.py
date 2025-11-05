"""
Company Name to Stock Symbol Search Service
Enables searching stocks by company name instead of just symbols
"""

# Company name to symbol mapping for major stocks
COMPANY_SYMBOL_MAP = {
    # US Tech Giants
    'apple': 'AAPL',
    'apple inc': 'AAPL',
    'microsoft': 'MSFT',
    'microsoft corporation': 'MSFT',
    'google': 'GOOGL',
    'alphabet': 'GOOGL',
    'alphabet inc': 'GOOGL',
    'amazon': 'AMZN',
    'amazon.com': 'AMZN',
    'tesla': 'TSLA',
    'tesla inc': 'TSLA',
    'meta': 'META',
    'facebook': 'META',
    'meta platforms': 'META',
    'nvidia': 'NVDA',
    'nvidia corporation': 'NVDA',
    'netflix': 'NFLX',
    'netflix inc': 'NFLX',
    
    # US Financial
    'jpmorgan': 'JPM',
    'jp morgan': 'JPM',
    'jpmorgan chase': 'JPM',
    'bank of america': 'BAC',
    'wells fargo': 'WFC',
    'goldman sachs': 'GS',
    'citigroup': 'C',
    'morgan stanley': 'MS',
    'american express': 'AXP',
    'visa': 'V',
    'mastercard': 'MA',
    
    # US Healthcare
    'johnson & johnson': 'JNJ',
    'johnson and johnson': 'JNJ',
    'unitedhealth': 'UNH',
    'pfizer': 'PFE',
    'abbvie': 'ABBV',
    'eli lilly': 'LLY',
    'merck': 'MRK',
    'bristol myers': 'BMY',
    'abbott': 'ABT',
    
    # US Retail & Consumer
    'walmart': 'WMT',
    'home depot': 'HD',
    'coca cola': 'KO',
    'coca-cola': 'KO',
    'pepsi': 'PEP',
    'pepsico': 'PEP',
    'procter & gamble': 'PG',
    'procter and gamble': 'PG',
    'nike': 'NKE',
    'mcdonalds': 'MCD',
    "mcdonald's": 'MCD',
    'starbucks': 'SBUX',
    'costco': 'COST',
    'target': 'TGT',
    
    # US Industrial
    'boeing': 'BA',
    'caterpillar': 'CAT',
    'general electric': 'GE',
    '3m': 'MMM',
    'honeywell': 'HON',
    'lockheed martin': 'LMT',
    'raytheon': 'RTX',
    'united parcel': 'UPS',
    'ups': 'UPS',
    'fedex': 'FDX',
    
    # US Energy
    'exxon': 'XOM',
    'exxonmobil': 'XOM',
    'chevron': 'CVX',
    'conocophillips': 'COP',
    
    # US Telecom
    'verizon': 'VZ',
    'at&t': 'T',
    'att': 'T',
    't-mobile': 'TMUS',
    'tmobile': 'TMUS',
    'comcast': 'CMCSA',
    
    # Indian Stocks (NSE)
    'reliance': 'RELIANCE.NS',
    'reliance industries': 'RELIANCE.NS',
    'tcs': 'TCS.NS',
    'tata consultancy': 'TCS.NS',
    'tata consultancy services': 'TCS.NS',
    'infosys': 'INFY.NS',
    'hdfc bank': 'HDFCBANK.NS',
    'hdfc': 'HDFCBANK.NS',
    'icici bank': 'ICICIBANK.NS',
    'icici': 'ICICIBANK.NS',
    'state bank': 'SBIN.NS',
    'sbi': 'SBIN.NS',
    'bharti airtel': 'BHARTIARTL.NS',
    'airtel': 'BHARTIARTL.NS',
    'itc': 'ITC.NS',
    'itc limited': 'ITC.NS',
    'hindustan unilever': 'HINDUNILVR.NS',
    'hul': 'HINDUNILVR.NS',
    'asian paints': 'ASIANPAINT.NS',
    'maruti': 'MARUTI.NS',
    'maruti suzuki': 'MARUTI.NS',
    'mahindra': 'M&M.NS',
    'mahindra & mahindra': 'M&M.NS',
    'wipro': 'WIPRO.NS',
    'hcl': 'HCLTECH.NS',
    'hcl tech': 'HCLTECH.NS',
    'hcl technologies': 'HCLTECH.NS',
    'kotak': 'KOTAKBANK.NS',
    'kotak mahindra': 'KOTAKBANK.NS',
    'axis bank': 'AXISBANK.NS',
    'axis': 'AXISBANK.NS',
    'bajaj': 'BAJFINANCE.NS',
    'bajaj finance': 'BAJFINANCE.NS',
    'titan': 'TITAN.NS',
    'titan company': 'TITAN.NS',
    'sun pharma': 'SUNPHARMA.NS',
    'ultratech': 'ULTRACEMCO.NS',
    'ultratech cement': 'ULTRACEMCO.NS',
    'tech mahindra': 'TECHM.NS',
    'power grid': 'POWERGRID.NS',
    'ntpc': 'NTPC.NS',
    'ongc': 'ONGC.NS',
    'coal india': 'COALINDIA.NS',
    'tata steel': 'TATASTEEL.NS',
    'tata motors': 'TATAMOTORS.NS',
    'adani': 'ADANIENT.NS',
    'adani enterprises': 'ADANIENT.NS',
}


def search_company(query: str) -> dict:
    """
    Search for a stock by company name or symbol
    
    Args:
        query: Company name or stock symbol (case-insensitive)
        
    Returns:
        dict with:
            - found: bool
            - symbol: str (stock symbol)
            - company_name: str (full company name)
            - match_type: str (exact, partial, symbol)
            - confidence: float (0-1)
    """
    if not query:
        return {'found': False, 'error': 'Empty query'}
    
    # Normalize query
    query_lower = query.lower().strip()
    
    # Check if it's already a valid symbol (uppercase check)
    if query.isupper() and len(query) <= 10:
        return {
            'found': True,
            'symbol': query,
            'company_name': query,
            'match_type': 'symbol',
            'confidence': 1.0
        }
    
    # Exact company name match
    if query_lower in COMPANY_SYMBOL_MAP:
        symbol = COMPANY_SYMBOL_MAP[query_lower]
        return {
            'found': True,
            'symbol': symbol,
            'company_name': query.title(),
            'match_type': 'exact',
            'confidence': 1.0
        }
    
    # Partial company name match
    matches = []
    for company_name, symbol in COMPANY_SYMBOL_MAP.items():
        if query_lower in company_name or company_name in query_lower:
            # Calculate confidence based on match quality
            confidence = len(query_lower) / len(company_name)
            matches.append({
                'symbol': symbol,
                'company_name': company_name.title(),
                'confidence': min(confidence, 1.0)
            })
    
    if matches:
        # Sort by confidence and return best match
        best_match = max(matches, key=lambda x: x['confidence'])
        return {
            'found': True,
            'symbol': best_match['symbol'],
            'company_name': best_match['company_name'],
            'match_type': 'partial',
            'confidence': best_match['confidence'],
            'alternatives': matches[:5]  # Top 5 alternatives
        }
    
    # Fuzzy match using Levenshtein distance
    from difflib import get_close_matches
    close_matches = get_close_matches(query_lower, COMPANY_SYMBOL_MAP.keys(), n=3, cutoff=0.6)
    
    if close_matches:
        best_match = close_matches[0]
        symbol = COMPANY_SYMBOL_MAP[best_match]
        return {
            'found': True,
            'symbol': symbol,
            'company_name': best_match.title(),
            'match_type': 'fuzzy',
            'confidence': 0.7,
            'suggestion': f"Did you mean '{best_match.title()}'?"
        }
    
    # No match found
    return {
        'found': False,
        'error': f'No company found matching "{query}"',
        'suggestion': 'Try using the stock symbol (e.g., AAPL, MSFT) or full company name'
    }


def get_symbol_from_query(query: str) -> str:
    """
    Simple helper to get symbol from query
    Returns the symbol if found, otherwise returns the original query
    """
    result = search_company(query)
    if result['found']:
        return result['symbol']
    return query.upper()


def list_available_companies(limit: int = 50) -> list:
    """
    List available companies
    
    Args:
        limit: Maximum number of companies to return
        
    Returns:
        List of dicts with company_name and symbol
    """
    # Get unique companies (remove duplicates from aliases)
    unique_companies = {}
    for company_name, symbol in COMPANY_SYMBOL_MAP.items():
        if symbol not in unique_companies:
            unique_companies[symbol] = company_name.title()
    
    companies = [
        {'company_name': name, 'symbol': symbol}
        for symbol, name in unique_companies.items()
    ]
    
    return companies[:limit]


# Example usage and testing
if __name__ == '__main__':
    print("=== Company Search Service Test ===\n")
    
    test_queries = [
        'apple',
        'AAPL',
        'micro',
        'tesla',
        'TSLA',
        'reliance',
        'tcs',
        'google',
        'nvidea',  # typo
        'jpmorgan',
        'Unknown Company'
    ]
    
    for query in test_queries:
        result = search_company(query)
        print(f"Query: '{query}'")
        print(f"  Result: {result}")
        print()
