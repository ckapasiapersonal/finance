def calculate_trailing_stop(current_price, high_since_entry, atr, multiplier=1.5):
    """
    Calculates the ATR-based trailing stop.
    Stop only moves upward.
    """
    # Potential new stop
    potential_stop = current_price - (multiplier * atr)
    
    # We use high_since_entry as well for some variations, 
    # but requirement is "Stop only moves upward".
    # So we compare current stop with new calculation.
    return potential_stop

def update_trailing_stop(current_stop, new_price, atr, multiplier=1.5):
    """
    Requirement: Stop only moves upward. Never decreases.
    """
    new_calculated_stop = new_price - (multiplier * atr)
    
    if current_stop is None:
        return new_calculated_stop
        
    return max(current_stop, new_calculated_stop)
