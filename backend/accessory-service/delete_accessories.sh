#!/bin/bash
# Delete all accessories from the accessory service

BASE_URL="${ACCESSORY_SERVICE_URL:-http://localhost:8030}"

echo "Deleting all accessories from $BASE_URL..."

# Get all accessories
accessories=$(curl -s "$BASE_URL/api/accessories")

# Check if we got a valid response
if [ -z "$accessories" ] || [ "$accessories" = "[]" ]; then
    echo "No accessories found to delete."
    exit 0
fi

# Extract IDs and delete each accessory
echo "$accessories" | jq -r '.[].id' | while read -r id; do
    if [ -n "$id" ]; then
        echo "Deleting accessory: $id"
        response=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/api/accessories/$id")
        if [ "$response" = "204" ]; then
            echo "  ✓ Deleted successfully"
        else
            echo "  ✗ Failed to delete (HTTP $response)"
        fi
    fi
done

echo ""
echo "Done! All accessories have been deleted."
