def convert(hex):
    
    # Format HEX string
    if hex[0] == "#":
        hex = hex[1:]

    # Convert HEX to RGB
    r,g,b = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

    # Calculate CIE 1931 XYZ color
    x = r * 0.649926 + g * 0.103455 + b * 0.197109
    y = r * 0.234327 + g * 0.743075 + b * 0.022598
    z = r * 0.0000000 + g * 0.053077 + b * 1.035763

    # Convert to Philips HUE colors
    X = x / (x + y + z)
    Y = y / (x + y + z)

    # Return [x,y] array + Y parameter which should be set as brightness
    return ([X, Y], int(y))