#!/bin/bash
# Seed example accessories into the accessory service

BASE_URL="${ACCESSORY_SERVICE_URL:-http://localhost:8030}"

echo "Seeding accessories to $BASE_URL..."
echo ""

# Toy 1: Squeaky Ball
echo "Creating accessory 1: Squeaky Ball (toy)..."
curl -s -X POST "$BASE_URL/api/accessories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Squeaky Ball",
    "type": "toy",
    "description": "A fun squeaky ball for dogs of all sizes",
    "price": 12.99,
    "stock": 50,
    "size": "M",
    "imageUrl": "https://example.com/squeaky-ball.jpg"
  }' | jq .
echo ""

# Toy 2: Feather Wand
echo "Creating accessory 2: Feather Wand (toy)..."
curl -s -X POST "$BASE_URL/api/accessories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Feather Wand",
    "type": "toy",
    "description": "Interactive feather wand toy for cats",
    "price": 8.99,
    "stock": 35,
    "size": "S",
    "imageUrl": "https://example.com/feather-wand.jpg"
  }' | jq .
echo ""

# Food with low stock
echo "Creating accessory 3: Premium Dog Food (food, low stock)..."
curl -s -X POST "$BASE_URL/api/accessories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Dog Food",
    "type": "food",
    "description": "Nutritious dry food for adult dogs - running low!",
    "price": 45.99,
    "stock": 5,
    "size": "L",
    "imageUrl": "https://example.com/dog-food.jpg"
  }' | jq .
echo ""

echo "Done! Created 3 example accessories (2 toys, 1 food with low stock)."
