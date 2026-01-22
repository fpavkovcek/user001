#!/bin/bash

# Seed Accessories Script
# This script creates 3 example accessories:
# - Two toys
# - One food item with low stock

set -e

echo "🌱 Seeding Accessories Database"
echo "================================"

# Configuration
BASE_URL="http://localhost:8030"

# Function to create an accessory
create_accessory() {
    local name="$1"
    local type="$2"
    local price="$3"
    local stock="$4"
    local size="$5"
    local imageUrl="$6"
    local description="$7"
    
    echo -n "📦 Creating: $name... "
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/accessories" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$name\",
            \"type\": \"$type\",
            \"price\": $price,
            \"stock\": $stock,
            \"size\": \"$size\",
            \"imageUrl\": \"$imageUrl\",
            \"description\": \"$description\"
        }")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "201" ]; then
        ACCESSORY_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "unknown")
        echo "✅ Created (ID: $ACCESSORY_ID)"
        return 0
    else
        echo "❌ Failed (HTTP $HTTP_CODE)"
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
        return 1
    fi
}

echo ""
echo "Creating sample accessories..."
echo "------------------------------"

# Create Toy #1: Squeaky Ball
create_accessory \
    "Squeaky Ball" \
    "toy" \
    12.99 \
    45 \
    "M" \
    "https://example.com/squeaky-ball.jpg" \
    "Rubber ball with squeaker that bounces unpredictably - perfect for fetch and play"

# Create Toy #2: Interactive Puzzle Toy
create_accessory \
    "Interactive Puzzle Toy" \
    "toy" \
    24.99 \
    30 \
    "L" \
    "https://example.com/puzzle-toy.jpg" \
    "Mental stimulation toy with hidden treats - keeps pets engaged for hours"

# Create Food: Premium Dog Food (Low Stock)
create_accessory \
    "Premium Grain-Free Dog Food" \
    "food" \
    54.99 \
    7 \
    "XL" \
    "https://example.com/premium-food.jpg" \
    "High-protein, grain-free formula with real chicken - LOW STOCK"

echo ""
echo "================================"
echo "✅ Seeding complete!"
echo ""
echo "To verify, run:"
echo "  curl http://localhost:8030/api/accessories | python3 -m json.tool"
echo ""
echo "To view low stock items:"
echo "  curl 'http://localhost:8030/api/accessories?lowStockOnly=true' | python3 -m json.tool"
echo "================================"
