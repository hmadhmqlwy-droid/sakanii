#!/bin/sh

# If config.py does not exist (like on Railway/GitHub deploy), create it from the template
if [ ! -f config.py ]; then
    echo "config.py not found. Creating config.py from config_example.py..."
    cp config_example.py config.py
fi

# Run the python script
echo "Starting Sakani Bot..."
python sakanibot.py
