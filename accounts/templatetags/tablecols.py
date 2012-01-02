from django import template

register = template.Library()

def tablecols(data, cols):
    rows = []
    row = []
    index = 0
    for user in data:
        row.append(user)
        index += 1
        if not index % cols:
            rows.append(row)
            row = []
        # Still stuff missing?
    if len(row) > 0:
        rows.append(row)
    return rows
register.filter('tablecols',tablecols)