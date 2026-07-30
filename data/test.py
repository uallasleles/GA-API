from filters import FILTERS_TO_NOTIFICATIONS

# print('AAAXU8AARAAAAlVAAP' in FILTERS_TO_NOTIFICATIONS)

def filter(rowid):
    return rowid in set(FILTERS_TO_NOTIFICATIONS)

print(filter('AAAXU8AARAAAAlVAAP'))

if filter('AAAXU8AARAAAAlVAAP'):
    print('Ok')