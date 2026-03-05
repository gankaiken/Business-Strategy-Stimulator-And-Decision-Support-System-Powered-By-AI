def insertion_sort(data, key_func=None, reverse=False):
    """
    Sorts a list in-place using the insertion sort algorithm.
    @param data - the list of elements to be sorted
    @param key_func - function used to extract the comparison value
    @param reverse - if True, sorts the list in descending order
    @return data - the sorted list
    """
    if key_func is None:
        key_func = lambda x: x

    for i in range(1, len(data)):
        current_item = data[i]
        current_val = key_func(current_item)
        j = i - 1

        while j >= 0:
            compare_val = key_func(data[j])
            if reverse:
                condition = compare_val < current_val
            else:
                condition = compare_val > current_val
            if not condition:
                break
            data[j + 1] = data[j]
            j -= 1
        data[j + 1] = current_item
    return data


def calculate_sum(data):
    """
    Calculates the sum of all elements in a list.
    @param data - a list of numerical values
    @return total - the sum of all values in the list
    """
    total = 0
    for item in data:
        total += item
    return total


def find_max(data, key_func=None):
    """
    Finds and returns the maximum element in a list.
    @param data - a list of elements
    @param key_func - function used to extract the comparison value
    @return best_item - the element with the maximum value, or None if the list is empty
    """
    if not data:
        return None

    best_item = data[0]

    if key_func is None:
        for item in data[1:]:
            if item > best_item:
                best_item = item
    else:
        best_val = key_func(best_item)
        for item in data[1:]:
            val = key_func(item)
            if val > best_val:
                best_val = val
                best_item = item

    return best_item
