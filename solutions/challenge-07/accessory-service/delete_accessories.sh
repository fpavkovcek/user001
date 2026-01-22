#!/bin/bash

# Delete All Accessories Script
# This script deletes all accessories from the accessory service

echo "🗑️  Deleting All Accessories"
echo "=============================="

# Configuration
BASE_URL="http://localhost:8030"

# Get all accessories
echo "📋 Fetching all accessories..."
ACCESSORIES=$(curl -s "${BASE_URL}/api/accessories")

# Check if we got any data
if [ -z "$ACCESSORIES" ] || [ "$ACCESSORIES" = "[]" ]; then
    echo "✅ No accessories found - database is already empty"
    exit 0
fi

# Count and display accessories to delete
TOTAL=$(echo "$ACCESSORIES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
echo "Found $TOTAL accessories to delete"
echo ""

# Delete each accessory
DELETED_COUNT=0
FAILED_COUNT=0

echo "$ACCESSORIES" | python3 -c "
import sys
import json

accessories = json.load(sys.stdin)
for acc in accessories:
    print(acc['id'])
" | while IFS= read -r id; do
    if [ -n "$id" ]; then
        echo -n "🗑️  Deleting accessory: $id... "
        
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${BASE_URL}/api/accessories/${id}")
        
        if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "200" ]; then
            echo "✅ Deleted"
            ((DELETED_COUNT++))
        else
            echo "❌ Failed (HTTP $HTTP_CODE)"
            ((FAILED_COUNT++))
        fi
    fi
done

echo ""
echo "=============================="
echo "✅ Deletion complete!"
echo "   Total: $TOTAL"
echo "=============================="
