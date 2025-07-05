#!/bin/bash

input="$1"

# Check if input is provided
if [[ -z "$input" ]]; then
  echo "Error: No input string provided." >&2
  echo "Usage: $0 Place_Name_YYYY_MMDDHHMMSS.jpg" >&2
  exit 1
fi

# Strip .jpg or .JPG extension
base="${input%.jpg}"
base="${base%.JPG}"

# Check that the base string has exactly 3 underscores (4 fields)
underscore_count=$(grep -o "_" <<< "$base" | wc -l)
if [[ "$underscore_count" -ne 3 ]]; then
  echo "Error: Filename must contain exactly 3 underscores before the extension." >&2
  exit 1
fi

# Split base into fields
IFS='_' read -r place name year datetime <<< "$base"

# Validate year: must be 4 digits
if ! [[ "$year" =~ ^[0-9]{4}$ ]]; then
  echo "Error: Year must be exactly 4 digits." >&2
  exit 1
fi

# Validate datetime: must be exactly 10 digits
if ! [[ "$datetime" =~ ^[0-9]{10}$ ]]; then
  echo "Error: Datetime must be exactly 10 numeric digits (MMDDHHMMSS)." >&2
  exit 1
fi

# Extract datetime components
month=${datetime:0:2}
day=${datetime:2:2}
hour=${datetime:4:2}
minute=${datetime:6:2}
# seconds=${datetime:8:2}  # ignored

# Validate each datetime field is two digits
for field in "$month" "$day" "$hour" "$minute"; do
  if ! [[ "$field" =~ ^[0-9]{2}$ ]]; then
    echo "Error: Invalid date/time component: $field" >&2
    exit 1
  fi
done

# Output as CSV
echo "$place,$name,$year,$month,$day,$hour,$minute"

