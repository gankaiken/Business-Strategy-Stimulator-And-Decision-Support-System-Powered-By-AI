"""
This file contains helper functions to safely
get user input when CSV data is missing or invalid.

The goal is to prevent crashes and guide the user
to enter valid numeric values.
"""


def is_number(value):
    """
    Check if a value can be converted to a float.
    @param value - value to check
    @return bool - True if numeric, False otherwise
    """
    try:
        float(value)
        return True
    except:
        return False


COLUMN_HINTS = {
    3: "Price Change (%) e.g. 0.05 for +5%",
    4: "Marketing Spend (RM) e.g. 1500",
    5: "Staff Cost Adjustment (RM)",
    6: "Waste Reduction (%) e.g. 0.1 for 10%",
    7: "Inventory Tightness (0–1)",
}


def get_float_or_prompt(value, col_index, month=None):
    while True:
        try:
            return float(value)
        except:
            print("\nInvalid input detected!")
            print(f"Column: {COLUMN_HINTS.get(col_index, 'Unknown')}")
            if month:
                print(f"Month : {month}")
            print("Example valid value: 0.5")
            value = input("Please enter a numeric value: ")


def get_int_or_prompt(value, message):
    """
    Return an integer value if valid, otherwise prompt the user.
    @param value - value read from CSV
    @param message - error message shown to user
    @return int - valid integer value
    """
    if value is not None and value != "" and is_number(value):
        return int(float(value))

    print("ERROR:", message)
    while True:
        user_input = input("Please enter an integer value: ").strip()
        if is_number(user_input):
            return int(float(user_input))
        else:
            print("Invalid input. Please enter an integer.")
